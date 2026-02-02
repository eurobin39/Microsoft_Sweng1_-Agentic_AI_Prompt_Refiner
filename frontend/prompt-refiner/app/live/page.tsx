import Layout from "@/components/Layout";

export default function LivePage() {
  return (
    <Layout>
       <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs uppercase tracking-wider text-gray-400">Step 2: Monitoring</span>
        </div>
      
      <h1 className="text-5xl font-bold mb-6">Live Evaluation</h1>
      <p className="text-xl text-gray-400 mb-8">
        Real-time execution of your prompts across multiple models.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card h-64 rounded-2xl border border-white/10 p-6 flex items-center justify-center text-gray-500">
           Live Console Output
        </div>
        <div className="glass-card h-64 rounded-2xl border border-white/10 p-6 flex items-center justify-center text-gray-500">
           Model Consensus Graph
        </div>
      </div>
    </Layout>
  );
}