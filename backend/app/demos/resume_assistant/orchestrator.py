"""
Resume Assistant Orchestrator (compatibility layer).

This wrapper preserves the older orchestrator import path used by CI tests.
It avoids requiring Azure/OpenAI credentials by default, and falls back to
simple, deterministic routing using local tools.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional, Tuple

from .runner import run_sync

logger = logging.getLogger("resume_assistant")

# ==========================================
# 1. Intent & Keyword Matching (Aligns with Travel's _WEATHER_KEYWORDS)
# ==========================================
_ANALYZE_KEYWORDS = ("analyze", "analysis", "requirements", "jd", "job description")
_WRITE_KEYWORDS = ("write", "generate", "create", "draft", "resume", "cv")
_REVIEW_KEYWORDS = ("review", "feedback", "score", "improve", "critique")

_JOB_HINTS = ("responsibilities", "requirements", "qualifications", "what you'll do", "skills")


# ==========================================
# 2. Text Parsing & Helper Functions (Aligns with Travel's _extract_destination)
# ==========================================
def _split_user_and_job(text: str) -> Tuple[str, str]:
    """Splits the user's background information and the job description."""
    if not text:
        return "", ""
    patterns = [
        r"(?:\n|^)\s*(JD|JOB|JOB DESCRIPTION|JOB POSTING)\s*:\s*",
        r"(?:\n|^)\s*---+\s*(?:\n|$)",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            left = text[: m.start()].strip()
            right = text[m.end() :].strip()
            return left, right

    t_lower = text.lower()
    if any(h in t_lower for h in _JOB_HINTS) or "requirements:" in t_lower:
        return "", text.strip()
    return text.strip(), ""


def _wants_analyze(text: str) -> bool:
    """Checks if the user intent is to analyze a job description."""
    return any(k in text.lower() for k in _ANALYZE_KEYWORDS)


def _wants_write(text: str) -> bool:
    """Checks if the user intent is to write a resume."""
    return any(k in text.lower() for k in _WRITE_KEYWORDS)


def _wants_review(text: str) -> bool:
    """Checks if the user intent is to review a resume."""
    return any(k in text.lower() for k in _REVIEW_KEYWORDS)


def _is_weak_output(text: str) -> bool:
    """Checks if the generated output is too short or empty."""
    if not text:
        return True
    return len(text.strip()) < 30


# ==========================================
# 3. Deterministic CI Fallback Logic (Aligns with Travel's mock routing)
# ==========================================
def _fallback_collect_profile(user_info: str) -> str:
    """Mock info collection for CI."""
    ui = (user_info or "").strip()
    name = "Candidate"
    m = re.search(r"(?:my name is|name:|name\s+-)\s*([A-Za-z\s]+)", ui, flags=re.IGNORECASE)
    if m:
        name = m.group(1).strip()
    return json.dumps({"name": name, "summary": ui[:200] if ui else "No data provided."})


def _fallback_analyze_job(job_desc: str) -> str:
    """Mock job analysis for CI."""
    jd = (job_desc or "").lower()
    bank = ["python", "java", "sql", "git", "docker", "aws", "react", "agile"]
    found = [k for k in bank if k in jd]
    return json.dumps({"role": "Target Role", "required_skills": found})


def _fallback_write_resume(profile_json: str, job_json: str) -> str:
    """Mock resume writing for CI."""
    profile = json.loads(profile_json)
    job = json.loads(job_json)
    return (
        f"## {profile.get('name', 'Candidate')}\n\n"
        f"### Summary\n{profile.get('summary')}\n\n"
        f"### Skills\n{', '.join(job.get('required_skills', []))}"
    )


def _fallback_review(resume_md: str, job_json: str) -> str:
    """Mock resume reviewing for CI."""
    job = json.loads(job_json)
    skills = job.get('required_skills', [])
    score = 60 + (len(skills) * 10) if skills else 65
    return f"**Score:** {min(score, 100)}/100\n**Missing Skills:** Check JD requirements."


# ==========================================
# 4. Core Orchestrator (Aligns with Travel's orchestrator body)
# ==========================================
def orchestrator(user_request: str, stream: bool = False) -> str:
    """
    Route resume requests.

    If Azure OpenAI credentials are present, this can run the full
    Microsoft Agent Framework workflow. Otherwise, it uses a lightweight
    rules-based fallback suitable for CI.
    """
    if not user_request or not user_request.strip():
        return "Please paste your background info and (optionally) a job description."

    # ---------------------------------------------------------
    # Path A: MAF Workflow (Aligns with TRAVEL_ASSISTANT_USE_MAF)
    # ---------------------------------------------------------
    if os.getenv("RESUME_ASSISTANT_USE_MAF", "").lower() in {"1", "true", "yes"}:
        logger.info("Orchestrator path: MAF (RESUME_ASSISTANT_USE_MAF enabled)")
        print("[resume_assistant] orchestrator path: MAF (RESUME_ASSISTANT_USE_MAF enabled)")
        
        trace = run_sync(
            user_request=user_request,
            mode="sequential",
            stream=stream,
            log_file=None,
            trace_dir="resume_assistant/log/traces",
        )
        output = trace.get("final_output") or ""

        if not output:
            agents = trace.get("agents", {}) or {}
            pieces = []
            for agent in ("info_collector_agent", "job_analyst_agent", "resume_writer_agent", "feedback_agent"):
                agent_out = (agents.get(agent) or {}).get("output", "")
                if agent_out:
                    pieces.append(agent_out.strip())
            output = "\n\n".join(pieces).strip()

        if _is_weak_output(output):
            logger.warning("MAF output weak/empty; using fallback composition")
            print("[resume_assistant] MAF output weak/empty; using fallback composition")
        else:
            return output

    # ---------------------------------------------------------
    # Path B: Fallback Workflow (Aligns with fallback rules + mock tools)
    # ---------------------------------------------------------
    logger.info("Orchestrator path: fallback (rules + mock tools)")
    print("[resume_assistant] orchestrator path: fallback (rules + mock tools)")

    wants_analyze = _wants_analyze(user_request)
    wants_write = _wants_write(user_request)
    wants_review = _wants_review(user_request)

    if not (wants_analyze or wants_write or wants_review):
        wants_write = True
        wants_review = True

    user_info, job_desc = _split_user_and_job(user_request)

    profile_json = _fallback_collect_profile(user_info)
    job_json = _fallback_analyze_job(job_desc)

    if wants_analyze and not (wants_write or wants_review):
        return job_json

    resume_md = _fallback_write_resume(profile_json, job_json) if wants_write else (user_info or "")

    if wants_review:
        feedback = _fallback_review(resume_md, job_json)
        if wants_write:
            return f"{resume_md}\n\n## Resume Feedback\n{feedback}"
        return feedback

    return resume_md