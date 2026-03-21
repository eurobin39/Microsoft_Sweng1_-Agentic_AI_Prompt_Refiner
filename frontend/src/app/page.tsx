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

type TraceToolCall = {
  tool: string;
  arguments: string | object;
  result?: string | object | null;
};
type TraceAgentLog = {
  instructions?: string | null;
  tools_available: string[];
  tool_calls: TraceToolCall[];
  output?: string | null;
  duration_ms?: number | null;
};
type TraceHandoff = { from?: string | null; to?: string | null };
type Trace = {
  timestamp: string;
  mode?: string | null;
  input?: string | null;
  agents: Record<string, TraceAgentLog>;
  execution_order: string[];
  handoffs: TraceHandoff[];
  final_output?: string | null;
  duration_ms?: number | null;
};

type AgentBlueprintWithTraces = {
  blueprint: Blueprint;
  traces: Trace[];
};

type TestCaseResult = {
  test_case_description: string;
  score: number;
  passed: boolean;
  reasoning: string;
  issues: string[];
};
type EvaluationResult = {
  overall_score: number;
  test_results: TestCaseResult[];
  summary: string;
};
type RefinementChange = {
  issue_reference: string;
  change_description: string;
  reasoning: string;
};
type RefinementResult = {
  refined_prompt: string;
  changes: RefinementChange[];
  expected_impact: string;
  summary: string;
};
type AgentRefinementResult = {
  agent_name: string;
  evaluation: EvaluationResult;
  refinement: RefinementResult | null;
};

type Stage = "idle" | "extracting" | "extracted" | "refining" | "done" | "error";

export default function Home() {
  const [url, setUrl] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [items, setItems] = useState<AgentBlueprintWithTraces[]>([]);
  const [results, setResults] = useState<AgentRefinementResult[]>([]);
  const [error, setError] = useState("");
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  async function handleExtract(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setStage("extracting");
    setItems([]);
    setResults([]);
    setError("");
    setExpandedAgent(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/extract-blueprints`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: url.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Request failed (${res.status})`);
      }

      const data: AgentBlueprintWithTraces[] = await res.json();
      setItems(data);
      setStage("extracted");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setStage("error");
    }
  }

  async function handleRefineAll() {
    setStage("refining");
    setResults([]);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/refine-all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Request failed (${res.status})`);
      }

      const data: AgentRefinementResult[] = await res.json();
      setResults(data);
      setStage("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setStage("error");
    }
  }

  const isLoading = stage === "extracting" || stage === "refining";

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Agentic AI Prompt Refiner
        </h1>
        <p className="text-gray-500 max-w-xl">
          Point it at a GitHub repo containing AI agents. It will crawl the
          code, extract a blueprint per agent, and refine each system prompt
          against its test cases.
        </p>
      </div>

      {/* Input */}
      <form onSubmit={handleExtract} className="flex gap-3 max-w-2xl">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          required
          disabled={isLoading}
          className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {stage === "extracting" ? "Crawling…" : "Extract Agents"}
        </button>
      </form>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
          {stage === "extracting"
            ? "Crawling repo and extracting agent blueprints…"
            : `Running refinement on ${items.length} agent${items.length !== 1 ? "s" : ""}…`}
        </div>
      )}

      {/* Error */}
      {stage === "error" && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Extracted — show agents + Run Refine button */}
      {(stage === "extracted" || stage === "done") && items.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm font-medium text-gray-700">
                Found {items.length} agent{items.length !== 1 ? "s" : ""}
              </span>
              <span className="text-sm text-gray-400">
                · {items.reduce((n, it) => n + it.traces.length, 0)} trace{items.reduce((n, it) => n + it.traces.length, 0) !== 1 ? "s" : ""} scraped
              </span>
            </div>
            {stage === "extracted" && (
              <button
                onClick={handleRefineAll}
                className="rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700 transition-colors"
              >
                Run Refine on All Agents
              </button>
            )}
          </div>

          <div className="space-y-3">
            {items.map((item, i) => {
              const agentName = item.blueprint.agent.name ?? `Agent ${i + 1}`;
              const result = results.find((r) => r.agent_name === agentName);
              const isExpanded = expandedAgent === agentName;

              return (
                <AgentCard
                  key={agentName}
                  blueprint={item.blueprint}
                  traces={item.traces}
                  agentName={agentName}
                  result={result ?? null}
                  isExpanded={isExpanded}
                  onToggle={() =>
                    setExpandedAgent(isExpanded ? null : agentName)
                  }
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function AgentCard({
  blueprint,
  traces,
  agentName,
  result,
  isExpanded,
  onToggle,
}: {
  blueprint: Blueprint;
  traces: Trace[];
  agentName: string;
  result: AgentRefinementResult | null;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const score = result?.evaluation.overall_score;
  const scoreColor =
    score === undefined
      ? "text-gray-400"
      : score >= 0.7
      ? "text-green-600"
      : score >= 0.4
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      {/* Card header — always visible */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-gray-900">{agentName}</span>
          {blueprint.agent.description && (
            <span className="text-sm text-gray-500">{blueprint.agent.description}</span>
          )}
          <span className="text-xs text-gray-400">
            {blueprint.test_cases.length} test case{blueprint.test_cases.length !== 1 ? "s" : ""}
          </span>
          {blueprint.agent.tools && blueprint.agent.tools.length > 0 && (
            <span className="text-xs text-gray-400">
              {blueprint.agent.tools.length} tool{blueprint.agent.tools.length !== 1 ? "s" : ""}
            </span>
          )}
          <span className={`text-xs ${traces.length > 0 ? "text-blue-500" : "text-gray-300"}`}>
            {traces.length} trace{traces.length !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {score !== undefined && (
            <span className={`text-sm font-semibold tabular-nums ${scoreColor}`}>
              {Math.round(score * 100)}%
            </span>
          )}
          {result?.refinement && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              Refined
            </span>
          )}
          {result && !result.refinement && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              Passed
            </span>
          )}
          <svg
            className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-100 px-5 py-4 space-y-6">
          {/* Traces */}
          {traces.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                Scraped Traces ({traces.length})
              </h3>
              <div className="space-y-2">
                {traces.map((trace, i) => {
                  const agentLog = trace.agents[agentName];
                  return (
                    <div key={i} className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium text-blue-700">
                          {trace.input ? `"${trace.input}"` : `Trace ${i + 1}`}
                        </p>
                        <span className="text-xs text-blue-400">
                          {trace.execution_order.join(" → ")}
                        </span>
                      </div>
                      {agentLog && (
                        <div className="space-y-1">
                          {agentLog.tool_calls.length > 0 && (
                            <p className="text-xs text-blue-600">
                              Tools called: {agentLog.tool_calls.map((tc) => tc.tool).join(", ")}
                            </p>
                          )}
                          {agentLog.output && (
                            <p className="text-xs text-gray-600 line-clamp-2">{agentLog.output}</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {traces.length === 0 && (
            <p className="text-xs text-gray-400">No trace logs found in repo for this agent.</p>
          )}

          {/* Blueprint */}
          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Blueprint</h3>

            <div className="space-y-1">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-400">System Prompt</span>
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 border border-gray-200 p-4 text-sm text-gray-800 font-mono leading-relaxed">
                {blueprint.agent.system_prompt}
              </pre>
            </div>

            {blueprint.agent.tools && blueprint.agent.tools.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                  Tools ({blueprint.agent.tools.length})
                </span>
                <div className="space-y-1">
                  {blueprint.agent.tools.map((tool, i) => (
                    <div key={i} className="rounded-lg border border-gray-200 bg-white px-3 py-2">
                      <p className="text-sm font-medium text-gray-900">{tool.name}</p>
                      <p className="text-sm text-gray-500">{tool.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                Test Cases ({blueprint.test_cases.length})
              </span>
              <div className="space-y-1">
                {blueprint.test_cases.map((tc, i) => (
                  <div key={i} className="rounded-lg border border-gray-200 bg-white px-3 py-2 space-y-1">
                    {tc.description && (
                      <p className="text-xs text-gray-400">{tc.description}</p>
                    )}
                    <p className="text-sm text-gray-900">
                      <span className="font-medium">Input: </span>{tc.input}
                    </p>
                    {tc.expected_behavior && (
                      <p className="text-sm text-gray-500">
                        <span className="font-medium">Expected: </span>{tc.expected_behavior}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Evaluation results */}
          {result && (
            <div className="space-y-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Evaluation</h3>
                <ScoreBadge score={result.evaluation.overall_score} />
              </div>

              <p className="text-sm text-gray-700">{result.evaluation.summary}</p>

              <div className="space-y-2">
                {result.evaluation.test_results.map((tr, i) => (
                  <div
                    key={i}
                    className={`rounded-lg border px-4 py-3 space-y-1 ${
                      tr.passed
                        ? "border-green-200 bg-green-50"
                        : "border-red-200 bg-red-50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">
                        {tr.test_case_description}
                      </p>
                      <span className={`text-sm font-semibold tabular-nums ${tr.passed ? "text-green-600" : "text-red-600"}`}>
                        {Math.round(tr.score * 100)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{tr.reasoning}</p>
                    {tr.issues.length > 0 && (
                      <ul className="list-disc list-inside text-sm text-red-700 space-y-0.5 pt-1">
                        {tr.issues.map((issue, j) => (
                          <li key={j}>{issue}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Refinement */}
          {result?.refinement && (
            <div className="space-y-4 pt-4 border-t border-gray-100">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Refined Prompt</h3>

              <p className="text-sm text-gray-700">{result.refinement.summary}</p>

              <pre className="whitespace-pre-wrap rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-gray-800 font-mono leading-relaxed">
                {result.refinement.refined_prompt}
              </pre>

              {result.refinement.changes.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                    Changes ({result.refinement.changes.length})
                  </span>
                  <div className="space-y-1">
                    {result.refinement.changes.map((change, i) => (
                      <div key={i} className="rounded-lg border border-gray-200 bg-white px-3 py-2 space-y-1">
                        <p className="text-sm font-medium text-gray-900">{change.change_description}</p>
                        <p className="text-xs text-gray-500">
                          <span className="font-medium">Issue: </span>{change.issue_reference}
                        </p>
                        <p className="text-xs text-gray-500">
                          <span className="font-medium">Why: </span>{change.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                <p className="text-sm text-amber-800">
                  <span className="font-medium">Expected impact: </span>
                  {result.refinement.expected_impact}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7
      ? "bg-green-100 text-green-700"
      : score >= 0.4
      ? "bg-yellow-100 text-yellow-700"
      : "bg-red-100 text-red-700";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold tabular-nums ${color}`}>
      {pct}%
    </span>
  );
}
