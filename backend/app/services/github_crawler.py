import base64
import os
import re
from typing import Dict

import httpx

GITHUB_API = "https://api.github.com"
MAX_FILE_BYTES = 50_000   # skip files larger than 50 KB
MAX_TOTAL_BYTES = 200_000  # stop fetching after 200 KB total
MAX_FILES = 30

RELEVANT_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".yaml", ".yml", ".json", ".toml",
    ".md", ".txt", ".env.example",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".next",
    "dist", "build", "venv", ".venv", ".mypy_cache",
}

PRIORITY_KEYWORDS = {"agent", "prompt", "system", "config", "readme", "tool", "instruction"}


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) from a GitHub URL."""
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/\s]+?)(?:\.git)?(?:/.*)?$",
        url.strip(),
    )
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url!r}")
    return match.group(1), match.group(2)


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def crawl_repo(github_url: str) -> Dict[str, str]:
    """
    Crawl a public GitHub repo and return a mapping of
    file_path → file_content for the most relevant files.
    """
    owner, repo = parse_github_url(github_url)

    async with httpx.AsyncClient(headers=_headers(), timeout=30) as client:
        # Resolve default branch
        repo_resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
        repo_resp.raise_for_status()
        default_branch = repo_resp.json().get("default_branch", "main")

        # Fetch full file tree
        tree_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        )
        tree_resp.raise_for_status()
        tree = tree_resp.json().get("tree", [])

        # Filter to relevant blobs
        candidates = [
            item for item in tree
            if item["type"] == "blob"
            and not any(seg in SKIP_DIRS for seg in item["path"].split("/"))
            and any(item["path"].endswith(ext) for ext in RELEVANT_EXTENSIONS)
            and item.get("size", 0) < MAX_FILE_BYTES
        ]

        # Prioritise files whose path contains agent/prompt/config keywords
        def _priority(f: dict) -> int:
            return 0 if any(kw in f["path"].lower() for kw in PRIORITY_KEYWORDS) else 1

        candidates.sort(key=_priority)
        candidates = candidates[:MAX_FILES]

        # Fetch file contents
        contents: Dict[str, str] = {}
        total = 0

        for item in candidates:
            if total >= MAX_TOTAL_BYTES:
                break
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{item['path']}",
                params={"ref": default_branch},
            )
            if resp.status_code != 200:
                continue
            raw = base64.b64decode(resp.json()["content"]).decode("utf-8", errors="ignore")
            contents[item["path"]] = raw
            total += len(raw)

        return contents
