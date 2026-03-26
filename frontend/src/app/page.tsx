"use client";

import { useEffect, useRef, useState } from "react";

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

type Stage = "idle" | "extracting" | "extracted" | "error";

type ThinkingState = {
  agentName: string | null;
  executor: string | null;
  judgeText: string;
  refinerText: string;
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [items, setItems] = useState<AgentBlueprintWithTraces[]>([]);
  const [results, setResults] = useState<AgentRefinementResult[]>([]);
  const [error, setError] = useState("");
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [refiningAgents, setRefiningAgents] = useState<string[]>([]);
  const [thinking, setThinking] = useState<ThinkingState>({
    agentName: null,
    executor: null,
    judgeText: "",
    refinerText: "",
  });
  const judgeScrollRef = useRef<HTMLPreElement>(null);
  const refinerScrollRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (judgeScrollRef.current) {
      judgeScrollRef.current.scrollTop = judgeScrollRef.current.scrollHeight;
    }
  }, [thinking.judgeText]);

  useEffect(() => {
    if (refinerScrollRef.current) {
      refinerScrollRef.current.scrollTop = refinerScrollRef.current.scrollHeight;
    }
  }, [thinking.refinerText]);

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

  function getAgentName(item: AgentBlueprintWithTraces, idx: number) {
    return item.blueprint.agent.name ?? `Agent ${idx + 1}`;
  }

  async function runRefine(itemsToRefine: AgentBlueprintWithTraces[]) {
    if (itemsToRefine.length === 0) return;

    const namesToRefine = itemsToRefine.map(it => getAgentName(it, items.indexOf(it)));
    setRefiningAgents(prev => [...new Set([...prev, ...namesToRefine])]);
    setError("");
    setThinking({ agentName: null, executor: null, judgeText: "", refinerText: "" });

    try {
      const res = await fetch(`${API_BASE}/api/v1/refine-all-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsToRefine }),
      });

      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          const event = JSON.parse(line.slice(6));

          if (event.type === "agent_start") {
            setThinking(prev => ({
              ...prev,
              agentName: event.agent_name,
              executor: event.executor,
              judgeText: event.executor === "judge_agent" ? "" : prev.judgeText,
              refinerText: event.executor === "refiner_agent" ? "" : prev.refinerText,
            }));
          } else if (event.type === "chunk") {
            setThinking(prev => ({
              ...prev,
              executor: event.executor,
              judgeText: event.executor === "judge_agent" ? prev.judgeText + event.text : prev.judgeText,
              refinerText: event.executor === "refiner_agent" ? prev.refinerText + event.text : prev.refinerText,
            }));
          } else if (event.type === "result") {
            setResults(prev => [...prev, {
              agent_name: event.agent_name,
              evaluation: event.evaluation,
              refinement: event.refinement,
            }]);
          } else if (event.type === "error") {
            throw new Error(event.detail);
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setRefiningAgents(prev => prev.filter(n => !namesToRefine.includes(n)));
      setThinking({ agentName: null, executor: null, judgeText: "", refinerText: "" });
    }
  }

  function handleRefineAll() {
    const unrefined = items.filter((it, i) => {
      const name = getAgentName(it, i);
      return !results.find(r => r.agent_name === name) && !refiningAgents.includes(name);
    });
    runRefine(unrefined);
  }

  function handleRefineOne(agentName: string) {
    const item = items.find((it, i) => getAgentName(it, i) === agentName);
    if (item) runRefine([item]);
  }

  const isLoading = stage === "extracting";
  const isRefiningAny = refiningAgents.length > 0;

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="space-y-4 pt-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
          <span className="text-xs font-medium text-indigo-700">AI-Powered Prompt Analysis</span>
        </div>
        <h1 className="text-4xl font-bold tracking-tight">
          <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 bg-clip-text text-transparent">
            Agentic AI
          </span>{" "}
          <span className="text-slate-900">Prompt Refiner</span>
        </h1>
        <p className="text-slate-500 max-w-xl text-base leading-relaxed">
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
          className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400/50 focus:border-indigo-300 disabled:opacity-50 transition-all"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-medium text-white hover:from-indigo-700 hover:to-violet-700 disabled:opacity-50 transition-all shadow-sm hover:shadow-md hover:shadow-indigo-200/60"
        >
          {stage === "extracting" ? "Crawling…" : "Extract Agents"}
        </button>
      </form>

      {/* Loading — extracting */}
      {stage === "extracting" && (
        <div className="flex items-center gap-3 text-sm text-slate-600 bg-white rounded-xl border border-slate-200 px-4 py-3 w-fit shadow-sm">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
          Crawling repo and extracting agent blueprints…
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-3">
          <svg className="h-4 w-4 mt-0.5 flex-shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* How it works — only on idle */}
      {stage === "idle" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 pt-2">
          {[
            {
              step: "01",
              title: "Paste a GitHub URL",
              desc: "Link to any repository containing AI agents built with frameworks like the OpenAI Agents SDK.",
              icon: (
                <svg className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              ),
            },
            {
              step: "02",
              title: "Extract Blueprints",
              desc: "We crawl the codebase, extract system prompts, tools, test cases, and execution traces per agent.",
              icon: (
                <svg className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              ),
            },
            {
              step: "03",
              title: "Refine Prompts",
              desc: "Each agent's system prompt is evaluated against its test cases and refined for better performance.",
              icon: (
                <svg className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              ),
            },
          ].map(({ step, title, desc, icon }) => (
            <div
              key={step}
              className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-9 w-9 rounded-xl bg-indigo-50 flex items-center justify-center">
                  {icon}
                </div>
                <span className="text-xs font-bold text-slate-300 font-mono tabular-nums">{step}</span>
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Agents list + stream panels */}
      {stage === "extracted" && items.length > 0 && (() => {
        const unrefinedCount = items.filter((it, i) => {
          const n = getAgentName(it, i);
          return !results.find(r => r.agent_name === n) && !refiningAgents.includes(n);
        }).length;

        return (
          <div className="space-y-4">
            {/* Header row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-full bg-green-50 border border-green-200 px-3 py-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  <span className="text-xs font-medium text-green-700">
                    {items.length} agent{items.length !== 1 ? "s" : ""} found
                  </span>
                </div>
                <span className="text-sm text-slate-400">
                  · {items.reduce((n, it) => n + it.traces.length, 0)} trace{items.reduce((n, it) => n + it.traces.length, 0) !== 1 ? "s" : ""} scraped
                </span>
              </div>
              {unrefinedCount > 0 && (
                <button
                  onClick={handleRefineAll}
                  disabled={isRefiningAny}
                  className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-2 text-sm font-medium text-white hover:from-indigo-700 hover:to-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                >
                  {results.length === 0
                    ? "Refine All Agents"
                    : `Refine Remaining (${unrefinedCount})`}
                </button>
              )}
            </div>

            {/* Two-column layout */}
            <div className="flex gap-5 items-start">
              {/* Left: agent cards */}
              <div className="flex-1 min-w-0 space-y-3">
                {items.map((item, i) => {
                  const name = getAgentName(item, i);
                  const result = results.find((r) => r.agent_name === name);
                  const isExpanded = expandedAgent === name;
                  const isRefining = refiningAgents.includes(name);

                  return (
                    <AgentCard
                      key={name}
                      blueprint={item.blueprint}
                      traces={item.traces}
                      agentName={name}
                      result={result ?? null}
                      isExpanded={isExpanded}
                      isRefining={isRefining}
                      anyRefining={isRefiningAny}
                      onToggle={() => setExpandedAgent(isExpanded ? null : name)}
                      onRefine={result ? null : () => handleRefineOne(name)}
                    />
                  );
                })}
              </div>

              {/* Right: persistent stream panels */}
              <div className="w-72 flex-shrink-0 sticky top-6 space-y-3">
                {/* Active agent indicator */}
                <div className="flex items-center gap-2 px-1">
                  {isRefiningAny ? (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                      <span className="text-xs text-slate-500 truncate">
                        {thinking.agentName ? `Processing: ${thinking.agentName}` : "Starting…"}
                      </span>
                    </>
                  ) : (
                    <span className="text-xs text-slate-400">Agent output stream</span>
                  )}
                </div>

                {/* Judge panel */}
                <div className="rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-800">
                    <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Judge</span>
                    {isRefiningAny && thinking.executor === "judge_agent" && (
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    )}
                  </div>
                  <pre
                    ref={judgeScrollRef}
                    className="h-52 overflow-y-auto px-4 py-3 whitespace-pre-wrap text-xs font-mono leading-relaxed text-slate-300"
                  >
                    {thinking.judgeText || (
                      <span className="text-slate-600">Waiting for judge…</span>
                    )}
                  </pre>
                </div>

                {/* Refiner panel */}
                <div className="rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-800">
                    <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Refiner</span>
                    {isRefiningAny && thinking.executor === "refiner_agent" && (
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    )}
                  </div>
                  <pre
                    ref={refinerScrollRef}
                    className="h-52 overflow-y-auto px-4 py-3 whitespace-pre-wrap text-xs font-mono leading-relaxed text-amber-200/80"
                  >
                    {thinking.refinerText || (
                      <span className="text-slate-600">Waiting for refiner…</span>
                    )}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

function AgentCard({
  blueprint,
  traces,
  agentName,
  result,
  isExpanded,
  isRefining,
  anyRefining,
  onToggle,
  onRefine,
}: {
  blueprint: Blueprint;
  traces: Trace[];
  agentName: string;
  result: AgentRefinementResult | null;
  isExpanded: boolean;
  isRefining: boolean;
  anyRefining: boolean;
  onToggle: () => void;
  onRefine: (() => void) | null;
}) {
  const score = result?.evaluation.overall_score;
  const scoreColor =
    score === undefined
      ? "text-slate-400"
      : score >= 0.7
      ? "text-green-600"
      : score >= 0.4
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* Card header — always visible */}
      <div
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50/70 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center flex-shrink-0">
            <svg className="h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
            </svg>
          </div>
          <div className="min-w-0">
            <span className="text-sm font-semibold text-slate-900">{agentName}</span>
            {blueprint.agent.description && (
              <p className="text-xs text-slate-500 truncate mt-0.5">{blueprint.agent.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 ml-1">
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
              {blueprint.test_cases.length} tests
            </span>
            {blueprint.agent.tools && blueprint.agent.tools.length > 0 && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                {blueprint.agent.tools.length} tools
              </span>
            )}
            <span className={`rounded-full px-2 py-0.5 text-xs ${
              traces.length > 0 ? "bg-blue-50 text-blue-600" : "bg-slate-100 text-slate-400"
            }`}>
              {traces.length} traces
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {score !== undefined && (
            <span className={`text-sm font-bold tabular-nums ${scoreColor}`}>
              {Math.round(score * 100)}%
            </span>
          )}
          {result?.refinement && (
            <span className="rounded-full bg-amber-100 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-700">
              Refined
            </span>
          )}
          {result && !result.refinement && (
            <span className="rounded-full bg-green-100 border border-green-200 px-2.5 py-0.5 text-xs font-medium text-green-700">
              Passed
            </span>
          )}
          {/* Individual refine button — only shown when no result yet */}
          {!result && (
            <button
              onClick={(e) => { e.stopPropagation(); onRefine?.(); }}
              disabled={isRefining || anyRefining}
              className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {isRefining ? (
                <>
                  <span className="inline-block h-3 w-3 animate-spin rounded-full border border-indigo-300 border-t-indigo-600" />
                  Refining…
                </>
              ) : (
                <>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  Refine
                </>
              )}
            </button>
          )}
          <svg
            className={`h-4 w-4 text-slate-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-slate-100 divide-y divide-slate-100">
          {/* Traces */}
          {traces.length > 0 && (
            <div className="px-5 py-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Scraped Traces ({traces.length})
              </h3>
              <div className="space-y-2">
                {traces.map((trace, i) => {
                  const agentLog = trace.agents[agentName];
                  return (
                    <div key={i} className="rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50/40 px-4 py-3 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium text-blue-700">
                          {trace.input ? `"${trace.input}"` : `Trace ${i + 1}`}
                        </p>
                        <span className="text-xs text-blue-400 font-mono">
                          {trace.execution_order.join(" → ")}
                        </span>
                      </div>
                      {agentLog && (
                        <div className="space-y-1">
                          {agentLog.tool_calls.length > 0 && (
                            <p className="text-xs text-blue-600">
                              <span className="font-medium">Tools:</span>{" "}
                              {agentLog.tool_calls.map((tc) => tc.tool).join(", ")}
                            </p>
                          )}
                          {agentLog.output && (
                            <p className="text-xs text-slate-600 line-clamp-2">{agentLog.output}</p>
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
            <div className="px-5 py-4">
              <p className="text-xs text-slate-400">No trace logs found in repo for this agent.</p>
            </div>
          )}

          {/* Blueprint */}
          <div className="px-5 py-4 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Blueprint</h3>

            <div className="space-y-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">System Prompt</span>
              <pre className="whitespace-pre-wrap rounded-xl bg-slate-900 border border-slate-800 p-4 text-xs text-slate-300 font-mono leading-relaxed">
                {blueprint.agent.system_prompt}
              </pre>
            </div>

            {blueprint.agent.tools && blueprint.agent.tools.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Tools ({blueprint.agent.tools.length})
                </span>
                <div className="grid gap-2">
                  {blueprint.agent.tools.map((tool, i) => (
                    <div key={i} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
                      <p className="text-sm font-medium text-slate-900">{tool.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{tool.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Test Cases ({blueprint.test_cases.length})
              </span>
              <div className="grid gap-2">
                {blueprint.test_cases.map((tc, i) => (
                  <div key={i} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 space-y-1">
                    {tc.description && (
                      <p className="text-xs text-slate-400">{tc.description}</p>
                    )}
                    <p className="text-sm text-slate-900">
                      <span className="font-medium">Input: </span>{tc.input}
                    </p>
                    {tc.expected_behavior && (
                      <p className="text-sm text-slate-500">
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
            <div className="px-5 py-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Evaluation</h3>
                <ScoreBadge score={result.evaluation.overall_score} />
              </div>

              <p className="text-sm text-slate-700">{result.evaluation.summary}</p>

              <div className="space-y-2">
                {result.evaluation.test_results.map((tr, i) => (
                  <div
                    key={i}
                    className={`rounded-xl border px-4 py-3 space-y-1.5 ${
                      tr.passed
                        ? "border-green-200 bg-gradient-to-r from-green-50 to-emerald-50/40"
                        : "border-red-200 bg-gradient-to-r from-red-50 to-rose-50/40"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-slate-900">
                        {tr.test_case_description}
                      </p>
                      <span className={`text-sm font-bold tabular-nums ${tr.passed ? "text-green-600" : "text-red-600"}`}>
                        {Math.round(tr.score * 100)}%
                      </span>
                    </div>
                    <p className="text-sm text-slate-600">{tr.reasoning}</p>
                    {tr.issues.length > 0 && (
                      <ul className="list-disc list-inside text-xs text-red-700 space-y-0.5 pt-0.5">
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
            <div className="px-5 py-4 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Refined Prompt</h3>

              <p className="text-sm text-slate-700">{result.refinement.summary}</p>

              <div className="relative group">
                <pre className="whitespace-pre-wrap rounded-xl bg-slate-900 border border-amber-800/30 p-4 text-xs text-amber-200/90 font-mono leading-relaxed">
                  {result.refinement.refined_prompt}
                </pre>
                <CopyButton text={result.refinement.refined_prompt} />
              </div>

              {result.refinement.changes.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Changes ({result.refinement.changes.length})
                  </span>
                  <div className="grid gap-2">
                    {result.refinement.changes.map((change, i) => (
                      <div key={i} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 space-y-1">
                        <p className="text-sm font-medium text-slate-900">{change.change_description}</p>
                        <p className="text-xs text-slate-500">
                          <span className="font-medium">Issue: </span>{change.issue_reference}
                        </p>
                        <p className="text-xs text-slate-500">
                          <span className="font-medium">Why: </span>{change.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-yellow-50/40 px-4 py-3">
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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2.5 right-2.5 flex items-center gap-1.5 rounded-lg bg-slate-700/80 hover:bg-slate-600/90 border border-slate-600/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition-all opacity-0 group-hover:opacity-100"
    >
      {copied ? (
        <>
          <svg className="h-3.5 w-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-green-400">Copied</span>
        </>
      ) : (
        <>
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7
      ? "bg-green-100 text-green-700 border-green-200"
      : score >= 0.4
      ? "bg-yellow-100 text-yellow-700 border-yellow-200"
      : "bg-red-100 text-red-700 border-red-200";
  return (
    <span className={`rounded-full border px-3 py-0.5 text-xs font-bold tabular-nums ${color}`}>
      {pct}%
    </span>
  );
}
