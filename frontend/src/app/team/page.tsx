"use client";

import Image, { StaticImageData } from "next/image";
import { useEffect, useRef, useState, ReactNode } from "react";

import RachelImg from "@/src/images/Rachel.jpg";
import ConorImg from "@/src/images/Conor.jpg";
import EuroImg from "@/src/images/Euro.jpg";
import OdhranImg from "@/src/images/Odhran.jpeg";
import PratyakshImg from "@/src/images/Pratyaksh.jpg";
import TashfiaImg from "@/src/images/Tashfia.jpg";
import DanielImg from "@/src/images/Daniel.jpg";
import HanImg from "@/src/images/Han.jpg";

/* ────────────────────────────────────────────
   Hooks
──────────────────────────────────────────── */

function useReveal<T extends Element = HTMLDivElement>(threshold = 0.1) {
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
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      }`}
    >
      {children}
    </div>
  );
}

/* ────────────────────────────────────────────
   Types & data
──────────────────────────────────────────── */

interface TeamMember {
  name: string;
  photo: StaticImageData;
  title: string;
  roleLabel: string;
  isSecondYear?: boolean;
  bio: string;
  skills: string[];
  color: {
    ring: string;
    badge: string;
    dot: string;
    avatarBg: string;
    skillBg: string;
    skillText: string;
  };
}

const team: TeamMember[] = [
  {
    name: "Rachel Ranjith",
    photo: RachelImg,
    title: "Project Lead / Product Owner",
    roleLabel: "Project Lead",
    bio: "Led product strategy, team coordination, and architecture decisions across all four sprints. Developed the Code Assistant workflow and drove stakeholder communication with Microsoft mentors.",
    skills: ["Python", "Django", "Azure", "MAF", "SQL", "GitLab CI"],
    color: {
      ring: "ring-indigo-400",
      badge: "bg-indigo-100 text-indigo-700 border-indigo-200",
      dot: "bg-indigo-500",
      avatarBg: "bg-indigo-50",
      skillBg: "bg-indigo-50",
      skillText: "text-indigo-700",
    },
  },
  {
    name: "Conor Kelly",
    photo: ConorImg,
    title: "Backend Lead",
    roleLabel: "Backend Lead",
    bio: "Managed sprint workflows and issue tracking. Led development of the Judge agent and co-built the Travel Assistant, mentoring second-year contributors throughout.",
    skills: ["Java", "Python", "Kotlin", "MongoDB", "RAG Systems"],
    color: {
      ring: "ring-blue-400",
      badge: "bg-blue-100 text-blue-700 border-blue-200",
      dot: "bg-blue-500",
      avatarBg: "bg-blue-50",
      skillBg: "bg-blue-50",
      skillText: "text-blue-700",
    },
  },
  {
    name: "Euro Bae",
    photo: EuroImg,
    title: "DevOps Lead",
    roleLabel: "DevOps Lead",
    bio: "Architected the CI/CD pipeline and led MCP integration with GitHub Copilot. Designed core system architecture diagrams and built the Resume Assistant end-to-end.",
    skills: ["React", "Next.js", "TypeScript", "Node.js", "Docker"],
    color: {
      ring: "ring-violet-400",
      badge: "bg-violet-100 text-violet-700 border-violet-200",
      dot: "bg-violet-500",
      avatarBg: "bg-violet-50",
      skillBg: "bg-violet-50",
      skillText: "text-violet-700",
    },
  },
  {
    name: "Ódhran Mulvihill",
    photo: OdhranImg,
    title: "Integration Lead",
    roleLabel: "Integration Lead",
    bio: "Developed FastAPI health-check and monitoring endpoints, contributed to backend infrastructure, and produced documentation for the Microsoft Agent Framework.",
    skills: ["Python", "C++", "FastAPI", "Docker", "AWS"],
    color: {
      ring: "ring-emerald-400",
      badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
      dot: "bg-emerald-500",
      avatarBg: "bg-emerald-50",
      skillBg: "bg-emerald-50",
      skillText: "text-emerald-700",
    },
  },
  {
    name: "Pratyaksh Agarwal",
    photo: PratyakshImg,
    title: "Backend Dev",
    roleLabel: "Backend Dev",
    isSecondYear: true,
    bio: "Implemented the Judge agent with strict Pydantic schemas and contributed to the Resume Assistant and MCP server setup.",
    skills: ["JavaScript", "Next.js", "Java", "Pydantic", "OOP"],
    color: {
      ring: "ring-rose-400",
      badge: "bg-rose-100 text-rose-700 border-rose-200",
      dot: "bg-rose-500",
      avatarBg: "bg-rose-50",
      skillBg: "bg-rose-50",
      skillText: "text-rose-700",
    },
  },
  {
    name: "Tashfia Jahir",
    photo: TashfiaImg,
    title: "DevOps Dev",
    roleLabel: "DevOps Dev",
    isSecondYear: true,
    bio: "Refactored the Code Assistant and designed the Refiner agent architecture. Reviewed the judge-refiner loop and introduced priority-based issue targeting into prompt refinement.",
    skills: ["Python", "Java", "ARM Assembly", "MAF", "Pydantic"],
    color: {
      ring: "ring-amber-400",
      badge: "bg-amber-100 text-amber-700 border-amber-200",
      dot: "bg-amber-500",
      avatarBg: "bg-amber-50",
      skillBg: "bg-amber-50",
      skillText: "text-amber-700",
    },
  },
  {
    name: "Daniel Prestwich",
    photo: DanielImg,
    title: "Backend Dev",
    roleLabel: "Backend Dev",
    isSecondYear: true,
    bio: "Co-developed the Code Assistant workflow and worked on MCP server implementation, contributing to Azure-hosted tool deployment and API endpoint development.",
    skills: ["Python", "Java", "FastAPI", "Azure", "JavaScript"],
    color: {
      ring: "ring-teal-400",
      badge: "bg-teal-100 text-teal-700 border-teal-200",
      dot: "bg-teal-500",
      avatarBg: "bg-teal-50",
      skillBg: "bg-teal-50",
      skillText: "text-teal-700",
    },
  },
  {
    name: "Han Zhu",
    photo: HanImg,
    title: "Integration Dev",
    roleLabel: "Integration Dev",
    isSecondYear: true,
    bio: "Built the Travel Assistant, implemented the Refiner agent's persistence layer, and designed the standardised MCP input schema to support multiple assistant workflows.",
    skills: ["Python", "Java", "MCP Schema", "Computer Vision"],
    color: {
      ring: "ring-cyan-400",
      badge: "bg-cyan-100 text-cyan-700 border-cyan-200",
      dot: "bg-cyan-500",
      avatarBg: "bg-cyan-50",
      skillBg: "bg-cyan-50",
      skillText: "text-cyan-700",
    },
  },
];

const mentors = [
  { name: "Saeed Misaghian", initials: "SM", title: "Industry Lead Mentor" },
  { name: "Neenu Vincent", initials: "NV", title: "Industry Mentor" },
  { name: "Leyre de la Calzada Alonso", initials: "LA", title: "Industry Mentor" },
];

/* ────────────────────────────────────────────
   Member card
──────────────────────────────────────────── */

function MemberCard({ member, index }: { member: TeamMember; index: number }) {
  const { color } = member;
  return (
    <Reveal delay={index * 60}>
      <div className="group flex flex-col rounded-2xl border border-slate-200/80 bg-white shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden h-full">
        {/* Photo + header */}
        <div className="flex flex-col items-center pt-7 pb-4 px-5">
          <div
            className={`relative rounded-full ring-2 ring-offset-2 ${color.ring} overflow-hidden h-20 w-20 flex-shrink-0 shadow-sm`}
          >
            <Image
              src={member.photo}
              alt={member.name}
              width={80}
              height={80}
              className="h-20 w-20 object-cover"
            />
          </div>

          <div className="mt-3 text-center space-y-1.5">
            <h2 className="text-base font-semibold text-slate-900 leading-tight">{member.name}</h2>
            <div className="flex items-center justify-center gap-1.5 flex-wrap">
              <span
                className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${color.badge}`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
                {member.roleLabel}
              </span>
              {member.isSecondYear && (
                <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                  2nd Year
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="mx-5 border-t border-slate-100" />

        {/* Bio */}
        <div className="px-5 py-4 flex-1">
          <p className="text-xs text-slate-600 leading-relaxed">{member.bio}</p>
        </div>

        {/* Skills */}
        <div className="px-5 pb-5 flex flex-wrap gap-1.5">
          {member.skills.map((skill) => (
            <span
              key={skill}
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${color.skillBg} ${color.skillText}`}
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    </Reveal>
  );
}

/* ────────────────────────────────────────────
   Mentor card
──────────────────────────────────────────── */

function MentorCard({ mentor, index }: { mentor: typeof mentors[0]; index: number }) {
  return (
    <Reveal delay={index * 80}>
      <div className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white px-5 py-4 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center flex-shrink-0 shadow-sm">
          <span className="text-sm font-bold text-white">{mentor.initials}</span>
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{mentor.name}</p>
          <p className="text-xs text-slate-500 mt-0.5">{mentor.title}</p>
          <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-xs font-medium text-blue-700">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            Microsoft
          </span>
        </div>
      </div>
    </Reveal>
  );
}

/* ────────────────────────────────────────────
   Page
──────────────────────────────────────────── */

export default function Team() {
  return (
    <div className="space-y-14 pt-2">

      {/* ─── Hero ─────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
          <span className="text-xs font-medium text-indigo-700">Trinity College Dublin · Microsoft Partnership</span>
        </div>

        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 bg-clip-text text-transparent">
              Meet the Team
            </span>
          </h1>
          <p className="mt-3 max-w-2xl text-base text-slate-500 leading-relaxed">
            Eight software engineering students from Trinity College Dublin, building an agentic
            AI prompt refinement tool in partnership with Microsoft across four sprints.
          </p>
        </div>

        {/* Sprint summary pills */}
        <div className="flex flex-wrap gap-2">
          {[
            { label: "4 Sprints", icon: "📅" },
            { label: "8 Engineers", icon: "👥" },
            { label: "4 × 3rd Year", icon: "🎓" },
            { label: "4 × 2nd Year", icon: "🌱" },
            { label: "Microsoft Azure", icon: "☁️" },
          ].map(({ label, icon }) => (
            <span
              key={label}
              className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 shadow-sm"
            >
              {icon} {label}
            </span>
          ))}
        </div>
      </div>

      {/* ─── Team grid ───────────────────────────────────── */}
      <div>
        <Reveal>
          <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <span className="h-5 w-1 rounded-full bg-gradient-to-b from-indigo-500 to-violet-500" />
            Team Members
          </h2>
        </Reveal>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {team.map((member, i) => (
            <MemberCard key={member.name} member={member} index={i} />
          ))}
        </div>
      </div>

      {/* ─── Mentors ──────────────────────────────────────── */}
      <div>
        <Reveal>
          <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <span className="h-5 w-1 rounded-full bg-gradient-to-b from-blue-500 to-blue-700" />
            Industry Mentors
            <span className="ml-1 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
              Microsoft
            </span>
          </h2>
        </Reveal>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {mentors.map((mentor, i) => (
            <MentorCard key={mentor.name} mentor={mentor} index={i} />
          ))}
        </div>
      </div>

      {/* ─── Project sprint timeline ─────────────────────── */}
      <Reveal>
        <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">
          <div className="px-6 pt-5 pb-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-900">Sprint Timeline</h2>
            <p className="text-xs text-slate-500 mt-0.5">How the project evolved across four development sprints</p>
          </div>
          <div className="divide-y divide-slate-100">
            {[
              {
                sprint: "Sprint 1",
                dates: "Jan 19 – Feb 15, 2026",
                color: "bg-indigo-500",
                title: "Foundation & Demo Workflows",
                desc: "Established architecture, GitLab setup, CI/CD pipeline, and built three demo multi-agent workflows (Code, Resume, Travel) using the Microsoft Agent Framework.",
              },
              {
                sprint: "Sprint 2",
                dates: "Feb 16 – Mar 1, 2026",
                color: "bg-violet-500",
                title: "Judge & Refiner Agents",
                desc: "Delivered the core judge-refiner multi-agent workflow, defined the MCP interface strategy, and resolved team alignment challenges with stakeholder guidance.",
              },
              {
                sprint: "Sprint 3",
                dates: "Mar 2 – Mar 13, 2026",
                color: "bg-purple-500",
                title: "MCP Integration & Web Interface",
                desc: "Validated MCP tool invocation through GitHub Copilot, identified architectural improvements, and developed the frontend interface for the prompt refinement tool.",
              },
              {
                sprint: "Sprint 4",
                dates: "Mar 16 – Apr 10, 2026",
                color: "bg-pink-500",
                title: "Presentation-Ready Final Version",
                desc: "Single-pass refinement architecture, shared Azure deployment consolidation, CI/CD hardening, and final polish for the demo-ready product.",
              },
            ].map((s) => (
              <div key={s.sprint} className="flex items-start gap-4 px-6 py-4 hover:bg-slate-50/60 transition-colors">
                <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-0.5">
                  <div className={`h-2.5 w-2.5 rounded-full ${s.color}`} />
                  <div className="h-full w-px bg-slate-100 flex-1" style={{ minHeight: "2rem" }} />
                </div>
                <div className="space-y-0.5 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-slate-900">{s.sprint}</span>
                    <span className="text-xs text-slate-400 font-mono">{s.dates}</span>
                  </div>
                  <p className="text-sm font-medium text-slate-700">{s.title}</p>
                  <p className="text-xs text-slate-500 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>

      {/* ─── Footer ───────────────────────────────────────── */}
      <Reveal>
        <div className="flex items-center justify-center pb-4">
          <span className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm text-slate-600 shadow-sm">
            <svg className="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Software Engineering · Trinity College Dublin · 2026
          </span>
        </div>
      </Reveal>

    </div>
  );
}
