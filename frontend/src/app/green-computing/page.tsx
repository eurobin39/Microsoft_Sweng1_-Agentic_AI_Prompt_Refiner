"use client";

import { useEffect, useRef, useState, ReactNode } from "react";

/* ────────────────────────────────────────────
   Hooks
──────────────────────────────────────────── */

function useReveal<T extends Element = HTMLDivElement>(threshold = 0.12) {
  const ref = useRef<T>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true); },
      { threshold }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return { ref, visible };
}

function Reveal({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`transition-all duration-700 ease-out ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      }`}
    >
      {children}
    </div>
  );
}

function CountUp({ to, decimals = 0, suffix = "", prefix = "" }: {
  to: number; decimals?: number; suffix?: string; prefix?: string;
}) {
  const [val, setVal] = useState(0);
  const { ref, visible } = useReveal<HTMLSpanElement>(0.3);
  useEffect(() => {
    if (!visible) return;
    let raf: number;
    const t0 = performance.now();
    const dur = 1600;
    function tick(now: number) {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(eased * to);
      if (p < 1) raf = requestAnimationFrame(tick);
      else setVal(to);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [visible, to]);
  return (
    <span ref={ref}>
      {prefix}{decimals > 0 ? val.toFixed(decimals) : Math.round(val)}{suffix}
    </span>
  );
}

/* ────────────────────────────────────────────
   Icons
──────────────────────────────────────────── */

function BoltIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}
function CloudIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
    </svg>
  );
}
function ShareIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
    </svg>
  );
}
function PuzzleIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
    </svg>
  );
}
function ChartIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

/* ────────────────────────────────────────────
   Section data
──────────────────────────────────────────── */

type Accent = "emerald" | "green" | "teal" | "cyan" | "lime";

const accentMap: Record<
  Accent,
  { border: string; iconBg: string; iconText: string; tag: string; insight: string; dot: string; gradient: string }
> = {
  emerald: {
    border: "border-l-emerald-500",
    iconBg: "bg-emerald-100",
    iconText: "text-emerald-600",
    tag: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    insight: "bg-emerald-50 border border-emerald-200 text-emerald-800",
    dot: "bg-emerald-500",
    gradient: "from-emerald-50/60 to-white",
  },
  green: {
    border: "border-l-green-500",
    iconBg: "bg-green-100",
    iconText: "text-green-600",
    tag: "bg-green-50 text-green-700 border border-green-200",
    insight: "bg-green-50 border border-green-200 text-green-800",
    dot: "bg-green-500",
    gradient: "from-green-50/60 to-white",
  },
  teal: {
    border: "border-l-teal-500",
    iconBg: "bg-teal-100",
    iconText: "text-teal-600",
    tag: "bg-teal-50 text-teal-700 border border-teal-200",
    insight: "bg-teal-50 border border-teal-200 text-teal-800",
    dot: "bg-teal-500",
    gradient: "from-teal-50/60 to-white",
  },
  cyan: {
    border: "border-l-cyan-500",
    iconBg: "bg-cyan-100",
    iconText: "text-cyan-600",
    tag: "bg-cyan-50 text-cyan-700 border border-cyan-200",
    insight: "bg-cyan-50 border border-cyan-200 text-cyan-800",
    dot: "bg-cyan-500",
    gradient: "from-cyan-50/60 to-white",
  },
  lime: {
    border: "border-l-lime-500",
    iconBg: "bg-lime-100",
    iconText: "text-lime-600",
    tag: "bg-lime-50 text-lime-700 border border-lime-200",
    insight: "bg-lime-50 border border-lime-200 text-lime-800",
    dot: "bg-lime-500",
    gradient: "from-lime-50/60 to-white",
  },
};

interface Section {
  id: string;
  tag: string;
  title: string;
  accent: Accent;
  icon: ReactNode;
  paragraphs: string[];
  insight: string;
}

const sections: Section[] = [
  {
    id: "single-pass",
    tag: "Sprint 4 · Architecture",
    title: "Single-Pass Refinement Architecture",
    accent: "emerald",
    icon: <BoltIcon />,
    paragraphs: [
      "One of the most impactful Green Computing decisions made during Sprint 4 was the move from an iterative refinement loop to a single-pass evaluation and refinement architecture. In earlier versions of the system, the pipeline would repeatedly cycle between the Judge and Refiner agents until the evaluation score crossed a defined threshold. While this produced incrementally improved prompts, it also resulted in a high volume of LLM calls per run — each cycle invoking multiple models across the ensemble.",
      "By redesigning the pipeline to enforce stricter evaluation criteria and produce a refined prompt in a single pass, the system now achieves comparable output quality with a fraction of the computational cost. This directly reduces GPU inference time, token consumption, and the associated energy expenditure per evaluation run.",
    ],
    insight: "Directly reduces GPU inference time, token consumption, and the associated energy expenditure per evaluation run.",
  },
  {
    id: "carbon-cloud",
    tag: "Cloud Infrastructure",
    title: "Carbon-Aware Cloud Infrastructure",
    accent: "green",
    icon: <CloudIcon />,
    paragraphs: [
      "The system is deployed on Microsoft Azure, which provides measurable sustainability advantages over local or ad-hoc hosting. Azure's data centres operate with a Power Usage Effectiveness ratio of approximately 1.18 across its global fleet, meaning that the vast majority of energy consumed is directed toward computation rather than cooling and overhead.",
      "Microsoft has committed to operating on 100% renewable energy and achieving carbon-negative status, which means the infrastructure underpinning this project benefits from these commitments at no additional cost or configuration. Azure's managed scaling also ensures that compute resources are provisioned dynamically in response to actual demand rather than sitting idle at full capacity during periods of low usage, preventing wasteful baseline energy draw.",
    ],
    insight: "Azure PUE of ~1.18 means nearly all consumed energy is directed to computation, not cooling overhead.",
  },
  {
    id: "shared-deployment",
    tag: "DevOps",
    title: "Shared Azure OpenAI Deployment",
    accent: "teal",
    icon: <ShareIcon />,
    paragraphs: [
      "Rather than provisioning separate Azure OpenAI deployments for each agent or each developer, the team consolidated all inference requests through a single shared endpoint. In a typical multi-developer AI project, it would be common for each team member or each agent to have their own deployment, resulting in duplicated infrastructure and idle compute capacity across multiple endpoints.",
      "By routing all traffic through one centrally managed deployment, the project eliminates this redundancy entirely. This also simplifies monitoring — all token consumption, request volume, and response latency can be tracked from a single dashboard, making it straightforward to identify and address any wasteful usage patterns early.",
    ],
    insight: "Avoids an estimated 3–5 redundant deployments, each carrying its own baseline energy overhead even during inactivity.",
  },
  {
    id: "multi-agent",
    tag: "Architecture",
    title: "Multi-Agent Task Decomposition",
    accent: "cyan",
    icon: <PuzzleIcon />,
    paragraphs: [
      "The project's multi-agent architecture inherently supports Green Computing principles. Rather than submitting large, complex prompts to a single model and relying on one monolithic call to produce a complete output, the system decomposes the workflow into discrete, specialised agents. The Evaluator, Judge, and Refiner each handle a focused sub-task and only invoke the model with the context strictly required for their scope of work.",
      "This yields several sustainability benefits: individual agent calls use fewer tokens than an equivalent monolithic prompt because each agent processes only what it needs; targeted task execution reduces the frequency of failed or low-quality outputs that would otherwise require costly retries; and the modular design means that if only one stage of the pipeline needs to be re-run, the system does not repeat the entire workflow from scratch, avoiding unnecessary computation.",
    ],
    insight: "Modular agents process only the context they need — minimising tokens, retries, and redundant computation.",
  },
  {
    id: "evidence",
    tag: "Measured Impact",
    title: "Evidence and Impact",
    accent: "lime",
    icon: <ChartIcon />,
    paragraphs: [
      "The Green Computing measures outlined above produce observable and measurable effects. The move to single-pass refinement eliminates the multiple LLM invocations per evaluation run that characterised the earlier iterative design, reducing per-run compute by a significant margin. The shared Azure deployment avoids an estimated three to five redundant deployments that would each carry their own baseline energy overhead even during inactivity.",
      "Multi-agent decomposition reduces per-request token usage compared to a single-prompt approach, translating directly to lower GPU inference time and energy consumption. And deployment on Azure rather than local hardware takes advantage of Microsoft's data centre optimisations, renewable energy sourcing, and dynamic scaling — ensuring that the project's infrastructure footprint remains as small as practically possible.",
    ],
    insight: "Every architectural decision was evaluated not just for output quality, but for its computational and energy cost.",
  },
];

/* ────────────────────────────────────────────
   Section card
──────────────────────────────────────────── */

function SectionCard({ section, index }: { section: Section; index: number }) {
  const ac = accentMap[section.accent];
  return (
    <Reveal delay={index * 80}>
      <div
        className={`rounded-2xl bg-white border border-slate-200/80 border-l-4 ${ac.border} shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300`}
      >
        {/* Header */}
        <div className={`px-6 pt-5 pb-4 bg-gradient-to-r ${ac.gradient}`}>
          <div className="flex items-start gap-4">
            <div className={`h-10 w-10 rounded-xl ${ac.iconBg} flex items-center justify-center flex-shrink-0`}>
              <span className={ac.iconText}>{section.icon}</span>
            </div>
            <div className="space-y-1.5 min-w-0">
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${ac.tag}`}>
                {section.tag}
              </span>
              <h2 className="text-lg font-semibold text-slate-900 leading-snug">{section.title}</h2>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-3 border-t border-slate-100">
          {section.paragraphs.map((para, i) => (
            <p key={i} className="text-sm text-slate-600 leading-relaxed">{para}</p>
          ))}
        </div>

        {/* Insight footer */}
        <div className={`mx-6 mb-5 rounded-xl px-4 py-3 flex items-start gap-3 ${ac.insight}`}>
          <span className={`mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0 ${ac.dot} animate-pulse`} />
          <div className="space-y-0.5">
            <p className="text-xs font-semibold uppercase tracking-wider opacity-60">Key insight</p>
            <p className="text-sm leading-relaxed">{section.insight}</p>
          </div>
        </div>
      </div>
    </Reveal>
  );
}

/* ────────────────────────────────────────────
   Page
──────────────────────────────────────────── */

const floatingParticles = [
  { top: "18%", left: "8%",  size: "h-1.5 w-1.5", delay: "0s",    dur: "3.2s" },
  { top: "55%", left: "18%", size: "h-1 w-1",     delay: "1.1s",  dur: "4.0s" },
  { top: "28%", left: "72%", size: "h-2 w-2",     delay: "0.4s",  dur: "5.1s" },
  { top: "72%", left: "84%", size: "h-1.5 w-1.5", delay: "2.0s",  dur: "3.6s" },
  { top: "12%", left: "48%", size: "h-1 w-1",     delay: "1.6s",  dur: "4.4s" },
  { top: "82%", left: "42%", size: "h-1.5 w-1.5", delay: "0.9s",  dur: "3.9s" },
  { top: "40%", left: "92%", size: "h-1 w-1",     delay: "2.5s",  dur: "4.8s" },
  { top: "65%", left: "5%",  size: "h-1.5 w-1.5", delay: "0.3s",  dur: "3.3s" },
];

export default function GreenComputing() {
  return (
    <div className="space-y-10 pt-2">

      {/* ─── Hero ─────────────────────────────────────────── */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-emerald-950 via-green-900 to-teal-900 px-8 py-14 shadow-xl">
        {/* Ambient glows */}
        <div
          className="pointer-events-none absolute right-16 top-10 h-72 w-72 rounded-full bg-emerald-400/10 blur-3xl animate-pulse"
          style={{ animationDuration: "4s" }}
        />
        <div
          className="pointer-events-none absolute bottom-6 left-10 h-52 w-52 rounded-full bg-teal-400/10 blur-3xl animate-pulse"
          style={{ animationDuration: "6s", animationDelay: "2s" }}
        />
        <div
          className="pointer-events-none absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-green-400/5 blur-3xl animate-pulse"
          style={{ animationDuration: "8s", animationDelay: "1s" }}
        />

        {/* Floating dots */}
        {floatingParticles.map((p, i) => (
          <span
            key={i}
            className={`pointer-events-none absolute ${p.size} rounded-full bg-emerald-400/30 animate-bounce`}
            style={{ top: p.top, left: p.left, animationDelay: p.delay, animationDuration: p.dur }}
          />
        ))}

        {/* Content */}
        <div className="relative z-10 space-y-5">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/20 px-3 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-medium text-emerald-300">Core Design Principle</span>
            </span>
          </div>

          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
              Green{" "}
              <span className="bg-gradient-to-r from-emerald-300 via-green-300 to-teal-300 bg-clip-text text-transparent">
                Computing
              </span>
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-emerald-100/80">
              Green Computing was treated as a core design principle throughout the lifecycle of this project,
              shaping architectural decisions, development practices, and deployment choices from the outset
              rather than being applied as an afterthought.
            </p>
          </div>

          {/* Keyword pills */}
          <div className="flex flex-wrap gap-2 pt-1">
            {[
              "Single-pass architecture",
              "Azure PUE ~1.18",
              "100% renewable energy",
              "Shared inference endpoint",
              "Multi-agent decomposition",
            ].map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-medium text-white/80 backdrop-blur-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Stats bar ────────────────────────────────────── */}
      <Reveal>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            {
              display: <CountUp to={1.18} decimals={2} prefix="~" />,
              label: "Azure PUE",
              desc: "Power usage efficiency",
              accent: "text-emerald-600",
              bg: "bg-emerald-50",
              border: "border-emerald-200",
            },
            {
              display: <CountUp to={100} suffix="%" />,
              label: "Renewable Energy",
              desc: "Microsoft's commitment",
              accent: "text-green-600",
              bg: "bg-green-50",
              border: "border-green-200",
            },
            {
              display: <>3–<CountUp to={5} />+</>,
              label: "Deployments Avoided",
              desc: "Redundant endpoints eliminated",
              accent: "text-teal-600",
              bg: "bg-teal-50",
              border: "border-teal-200",
            },
            {
              display: <CountUp to={1} />,
              label: "Refinement Pass",
              desc: "Single pass, full quality",
              accent: "text-cyan-600",
              bg: "bg-cyan-50",
              border: "border-cyan-200",
            },
          ].map((s, i) => (
            <div
              key={i}
              className={`rounded-2xl border ${s.border} ${s.bg} px-5 py-4 shadow-sm text-center space-y-1 hover:shadow-md transition-shadow duration-300`}
            >
              <div className={`text-3xl font-bold tabular-nums ${s.accent}`}>{s.display}</div>
              <div className="text-xs font-semibold text-slate-800">{s.label}</div>
              <div className="text-xs text-slate-500 leading-snug">{s.desc}</div>
            </div>
          ))}
        </div>
      </Reveal>

      {/* ─── Section cards ────────────────────────────────── */}
      <div className="space-y-5">
        {sections.map((section, i) => (
          <SectionCard key={section.id} section={section} index={i} />
        ))}
      </div>

      {/* ─── Footer badge ─────────────────────────────────── */}
      <Reveal>
        <div className="flex items-center justify-center pb-4">
          <span className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-5 py-2.5 text-sm text-emerald-700 shadow-sm">
            <svg className="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Powered by sustainable infrastructure — Microsoft Azure
          </span>
        </div>
      </Reveal>

    </div>
  );
}
