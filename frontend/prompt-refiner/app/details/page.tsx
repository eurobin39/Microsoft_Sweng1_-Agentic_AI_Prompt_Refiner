import Layout from "@/components/Layout";
import CommonButton from "@/components/CommonButton";

export default function DetailsPage() {
  return (
    <Layout>
      <h1 className="text-5xl font-bold mb-6">Execution Details</h1>
      
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-white/5 border-b border-white/10">
            <tr>
              <th className="p-4 text-sm font-medium text-gray-400">Timestamp</th>
              <th className="p-4 text-sm font-medium text-gray-400">Model</th>
              <th className="p-4 text-sm font-medium text-gray-400">Status</th>
              <th className="p-4 text-sm font-medium text-gray-400">Tokens</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {[1, 2, 3].map((row) => (
              <tr key={row} className="hover:bg-white/5">
                <td className="p-4 text-gray-300 font-mono text-sm">2026-02-02 14:30:{10 + row}</td>
                <td className="p-4 text-gray-300">GPT-4</td>
                <td className="p-4"><span className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs">Success</span></td>
                <td className="p-4 text-gray-300">420</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-8">
        <CommonButton variant="secondary">Export Logs</CommonButton>
      </div>
    </Layout>
  );
}