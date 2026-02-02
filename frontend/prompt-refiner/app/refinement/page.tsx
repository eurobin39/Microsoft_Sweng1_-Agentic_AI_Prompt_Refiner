import Layout from "@/components/Layout";
import CommonButton from "@/components/CommonButton";

export default function RefinementPage() {
  return (
    <Layout>
      <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
          <span className="w-2 h-2 rounded-full bg-purple-500" />
          <span className="text-xs uppercase tracking-wider text-gray-400">Step 3</span>
      </div>

      <h1 className="text-5xl font-bold mb-6">Prompt Refinement</h1>
      <p className="text-xl text-gray-400 mb-8">
        AI-suggested optimizations to reduce hallucination rates.
      </p>

      <div className="glass-card p-8 rounded-2xl border border-white/10 mb-6">
         <h3 className="text-lg font-medium mb-4">Suggested Improvements</h3>
         <div className="space-y-4">
            <div className="p-4 bg-white/5 rounded-lg border-l-2 border-green-500">
              <p className="text-gray-300">Added specific constraints to the system prompt.</p>
            </div>
            <div className="p-4 bg-white/5 rounded-lg border-l-2 border-green-500">
              <p className="text-gray-300">Clarified output format to JSON only.</p>
            </div>
         </div>
      </div>
      
      <CommonButton>Apply Refinements</CommonButton>
    </Layout>
  );
}