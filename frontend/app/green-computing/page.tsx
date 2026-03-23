export default function GreenComputingPage() {
  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">
        <section className="rounded-2xl shadow-sm p-4 bg-slate-50">
            <h2 className="text-xl font-semibold mb-2">Sprint 1 — Architecture & Design</h2>
            <ul className="list-disc list-inside space-y-1">
                <li>Single shared Azure OpenAI deployment → eliminates idle compute and redundant resource allocation</li>
                <li>Multi-agent task decomposition: each agent handles a focused sub-task with only the context it needs, reducing per-request token usage</li>
                <li>Prompt refinement as an efficiency loop: automated refinement converges on good prompts in fewer iterations than manual trial-and-error</li>
                <li>Azure/Microsoft Foundry deployment: PUE ~1.18, renewable energy commitments, managed dynamic scaling, no idle on-premises hardware</li>
            </ul>
        </section>
    </main>
  );
}