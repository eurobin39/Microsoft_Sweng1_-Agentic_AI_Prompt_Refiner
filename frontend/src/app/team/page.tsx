const teamMembers = [
  {
    name: "Rachel Ranjith",
    role: "Product Owner",
    year: "3rd Year",
    bio: "Led sprint planning, team coordination, and project organisation across multiple stages of development. Helped define the project direction with mentors and clients, guided architectural decisions such as moving toward an API-first Azure-hosted MCP approach, and supported delivery through documentation, demos, issue planning, and code reviews.",
  },
  {
    name: "Conor Kelly",
    role: "Scrum Master",
    year: "3rd Year",
    bio: "Supported team delivery through issue planning, technical coordination, and mentoring. Helped shape the MCP and evaluation workflow, supervised implementation work across the team, contributed to documentation and reviews, and also collaborated on assistant workflow development including the travel assistant.",
  },
  {
    name: "Euro Bae",
    role: "Team Member",
    year: "3rd Year",
    bio: "Led major parts of the system architecture and technical direction for the prompt refinement framework. Worked closely with the Microsoft client to clarify requirements, designed architecture diagrams, supported MCP integration, and contributed to testing, CI/CD, assistant development, demos, and project-wide technical alignment.",
  },
  {
    name: "Ódhran Mulvihill",
    role: "Team Member",
    year: "3rd Year",
    bio: "Contributed to backend and project support work, including FastAPI endpoint improvements, health-check updates, and technical documentation. Also supported demo preparation and helped document the role and use of the multi-agent framework.",
  },
  {
    name: "Pratyaksh Agarwal",
    role: "Team Member",
    year: "2nd Year",
    bio: "Worked on backend agent development, especially the Judge agent and structured evaluation flow. Designed schema-based outputs, integrated the Judge into the multi-agent framework, connected audit logging, and also contributed to the Resume Assistant.",
  },
  {
    name: "Daniel Prestwich",
    role: "Team Member",
    year: "2nd Year",
    bio: "Contributed to MCP server and backend development, including Azure-hosting exploration and code assistant work. Helped implement project tasks under team guidance, supported technical pivots in hosting strategy, and contributed to assistant-related development.",
  },
  {
    name: "Han Zhu",
    role: "Team Member",
    year: "2nd Year",
    bio: "Worked on assistant workflow and prompt-refinement tooling across multiple parts of the project. Contributed to the Travel and Weather Assistant, designed a standardised MCP input schema for multiple assistants, and implemented persistence tooling for the Refiner agent to save structured audit logs.",
  },
  {
    name: "Tashfia Jahir",
    role: "Team Member",
    year: "2nd Year",
    bio: "Focused on refinement workflow design and backend agent development. Studied how the Judge and Refiner interact, explored prioritised refinement behaviour, contributed to the Refiner agent implementation, and supported demos and communication of the project’s future direction.",
  },
];

export default function Team() {
  return (
    <div className="space-y-6 pt-2">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Team</h1>
        <p className="text-slate-500">Meet the team behind this project.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {teamMembers.map((member) => (
          <div
            key={member.name}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold text-slate-900">{member.name}</h2>
            <p className="mt-1 text-sm font-medium text-slate-600">{member.role}</p>
            <p className="mt-1 text-xs text-slate-400">{member.year}</p>
            <p className="mt-4 text-sm leading-6 text-slate-500">{member.bio}</p>
          </div>
        ))}
      </div>
    </div>
  );
}