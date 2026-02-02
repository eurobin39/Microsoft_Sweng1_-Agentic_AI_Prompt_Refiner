import Layout from "@/components/Layout";

export default function ResultsPage() {
  return (
    <Layout>
      <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs uppercase tracking-wider text-gray-400">Step 4</span>
      </div>

      <h1 className="text-5xl font-bold mb-6">Benchmark Results</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[
          { label: "Accuracy", value: "94.2%" },
          { label: "Hallucination Rate", value: "0.8%" },
          { label: "Latency", value: "240ms" },
        ].map((stat, i) => (
          <div key={i} className="glass-card p-6 rounded-2xl border border-white/10 text-center">
            <div className="text-4xl font-bold mb-2">{stat.value}</div>
            <div className="text-sm text-gray-500 uppercase tracking-wide">{stat.label}</div>
          </div>
        ))}
      </div>
    </Layout>
  );
}