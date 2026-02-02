import Layout from "@/components/Layout";
import CommonButton from "@/components/CommonButton";

export default function SetupPage() {
  return (
    <Layout>
      <div className="max-w-3xl">
        <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-xs uppercase tracking-wider text-gray-400">Step 1</span>
        </div>
        
        <h1 className="text-5xl font-bold mb-6">Project Setup</h1>
        <p className="text-xl text-gray-400 mb-12">
          Configure your agent parameters and select your model ensemble.
        </p>

        <div className="glass-card p-8 rounded-2xl border border-white/10 space-y-6">
           <div className="h-32 border-2 border-dashed border-white/10 rounded-xl flex items-center justify-center text-gray-500">
             Configuration Form Placeholder
           </div>
           <div className="flex justify-end">
             <CommonButton>Continue to Live</CommonButton>
           </div>
        </div>
      </div>
    </Layout>
  );
}