export default function GreenComputingPage() {
  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">

        <h1 className="text-3xl font-bold text-green-700 mb-1">
          Green Computing
        </h1>
        <p className="text-slate-600 max-w-2xl">
          How our system reduces computational and environmental impact across sprints.
        </p>

        <section className="rounded-2xl shadow-sm p-4 bg-white border-l-4 border-green-400 transition hover:shadow-md hover:-translate-y-1">
            <h2 className="text-xl font-semibold mb-2 text-slate-800">🍃 Sprint 1 — Architecture & Design</h2>
            <ul className="list-disc list-inside space-y-1">
                <li>Single shared Azure OpenAI deployment → eliminates idle compute and redundant resource allocation</li>
                <li>Multi-agent task decomposition: each agent handles a focused sub-task with only the context it needs, reducing per-request token usage</li>
                <li>Prompt refinement as an efficiency loop: automated refinement converges on good prompts in fewer iterations than manual trial-and-error</li>
                <li>Azure/Microsoft Foundry deployment: PUE ~1.18, renewable energy commitments, managed dynamic scaling, no idle on-premises hardware</li>
            </ul>
        </section>

        <section className="rounded-2xl shadow-sm p-4 bg-white border-l-4 border-blue-400 transition hover:shadow-md hover:-translate-y-1">
            <h2 className="text-xl font-semibold mb-2 text-slate-800">♻️ Sprint 2 — WebSockets & RESTful Design</h2>
            <ul className="list-disc list-inside space-y-1">
                <li>WebSocket connection between frontend and backend: persistent two-way channel, only necessary data is sent</li>
                <li>FastAPI with async RESTful endpoints: frontend and backend don't need to be loaded simultaneously, reducing compute overhead</li>
            </ul>
        </section>

        <section className="rounded-2xl shadow-sm p-4 bg-white border-l-4 border-emerald-500 transition hover:shadow-md hover:-translate-y-1">
            <h2 className="text-xl font-semibold mb-2 text-slate-800">🌍 Sprint 3 — On-Demand Invocation & Observability</h2>
            <ul className="list-disc list-inside space-y-1">
                <li>MCP-based tool invoked only when explicitly triggered by the developer</li>
                <li>Local hosting during development reduces reliance on always-on cloud services</li>
                <li>Logging tracks tool invocation frequency, surfaces redundant LLM calls for optimization</li>
            </ul>
        </section>
    </main>
  );
}