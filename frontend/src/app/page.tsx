"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Tool = { name: string; description: string; parameters?: object | null };
type TestCase = {
  description?: string | null;
  input: string;
  expected_output?: string | null;
  expected_behavior?: string | null;
};
type Blueprint = {
  agent: {
    name?: string | null;
    description?: string | null;
    system_prompt: string;
    model?: string | null;
    provider?: string | null;
    tools?: Tool[];
  };
  test_cases: TestCase[];
  evaluation_criteria?: {
    goals?: string[];
    constraints?: string[];
    priority_description?: string | null;
  } | null;
};

type Status = "idle" | "loading" | "done" | "error";

export default function Home() {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setStatus("loading");
    setBlueprint(null);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/extract-blueprint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: url.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Request failed (${res.status})`);
      }

      const data: Blueprint = await res.json();
      setBlueprint(data);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setStatus("error");
    }
  }

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Agentic AI Prompt Refiner
        </h1>
        <p className="text-gray-500 max-w-xl">
          Point it at a GitHub repo containing an AI agent. It will crawl the
          code, extract the agent blueprint, and evaluate the system prompt
          against your test cases.
        </p>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3 max-w-2xl">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          required
          className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {status === "loading" ? "Crawling…" : "Extract Blueprint"}
        </button>
      </form>

      {/* Loading */}
      {status === "loading" && (
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
          Crawling repo and extracting blueprint…
        </div>
      )}

      {/* Error */}
      {status === "error" && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Result */}
      {status === "done" && blueprint && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm font-medium text-gray-700">
              Blueprint extracted
            </span>
          </div>

          <div className="grid gap-4">
            {/* Agent info */}
            <Section title="Agent">
              <Row label="Name" value={blueprint.agent.name} />
              <Row label="Description" value={blueprint.agent.description} />
              <Row label="Model" value={blueprint.agent.model} />
              <Row label="Provider" value={blueprint.agent.provider} />
              <div className="col-span-2 space-y-1">
                <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                  System Prompt
                </span>
                <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 border border-gray-200 p-4 text-sm text-gray-800 font-mono leading-relaxed">
                  {blueprint.agent.system_prompt}
                </pre>
              </div>
            </Section>

            {/* Tools */}
            {blueprint.agent.tools && blueprint.agent.tools.length > 0 && (
              <Section title={`Tools (${blueprint.agent.tools.length})`}>
                <div className="col-span-2 space-y-2">
                  {blueprint.agent.tools.map((tool, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-gray-200 bg-white px-4 py-3 space-y-1"
                    >
                      <p className="text-sm font-medium text-gray-900">
                        {tool.name}
                      </p>
                      <p className="text-sm text-gray-500">{tool.description}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Test cases */}
            <Section title={`Test Cases (${blueprint.test_cases.length})`}>
              <div className="col-span-2 space-y-2">
                {blueprint.test_cases.map((tc, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-gray-200 bg-white px-4 py-3 space-y-1"
                  >
                    {tc.description && (
                      <p className="text-xs font-medium text-gray-400">
                        {tc.description}
                      </p>
                    )}
                    <p className="text-sm text-gray-900">
                      <span className="font-medium">Input: </span>
                      {tc.input}
                    </p>
                    {tc.expected_behavior && (
                      <p className="text-sm text-gray-500">
                        <span className="font-medium">Expected: </span>
                        {tc.expected_behavior}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Section>

            {/* Evaluation criteria */}
            {blueprint.evaluation_criteria && (
              <Section title="Evaluation Criteria">
                {blueprint.evaluation_criteria.goals &&
                  blueprint.evaluation_criteria.goals.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                        Goals
                      </span>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
                        {blueprint.evaluation_criteria.goals.map((g, i) => (
                          <li key={i}>{g}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                {blueprint.evaluation_criteria.constraints &&
                  blueprint.evaluation_criteria.constraints.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                        Constraints
                      </span>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
                        {blueprint.evaluation_criteria.constraints.map(
                          (c, i) => (
                            <li key={i}>{c}</li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
              </Section>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-4">
      <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
      <div className="grid grid-cols-2 gap-4">{children}</div>
    </div>
  );
}

function Row({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  if (!value) return null;
  return (
    <div className="space-y-1">
      <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
        {label}
      </span>
      <p className="text-sm text-gray-800">{value}</p>
    </div>
  );
}
