content = """"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/modern-side-bar";
import { Topbar } from "@/components/ui/topbar";
import { FileText, Download, Trash2, RefreshCw } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDark, setIsDark] = useState(true);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("dev_master_key") || "";
      const res = await fetch("/api/dev/documents", { headers: { "x-master-key": token } });
      if (res.ok) {
          const data = await res.json();
          setDocuments(data.documents || []);
      }
    } catch(e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const formatSize = (bytes: number) => {
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (ts: number) => {
      return new Date(ts * 1000).toLocaleDateString();
  };

  return (
    <div className="flex h-screen w-full bg-neutral-50 dark:bg-[#161616] overflow-hidden font-sans">
      <Sidebar />
      <main className="flex-1 overflow-y-auto custom-scrollbar p-8 text-neutral-900 dark:text-white">
        <div className="max-w-6xl mx-auto">
            <Topbar title="Documents" subtitle="Knowledge base files across all instances." isDark={isDark} setIsDark={setIsDark} />
            
            <div className="flex justify-end mb-4">
                <button onClick={fetchDocuments} className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-[#2a2a2a] rounded-md hover:bg-neutral-100 dark:hover:bg-[#252525] transition-colors">
                    <RefreshCw className={`w-5 h-5 text-neutral-600 dark:text-neutral-400 ${loading ? "animate-spin" : ""}`} />
                </button>
            </div>

            <div className="bg-white dark:bg-[#1e1e1e] border border-neutral-200 dark:border-[#2a2a2a] rounded-[12px] overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-neutral-50 dark:bg-[#252525] border-b border-neutral-200 dark:border-[#2a2a2a] text-neutral-500 dark:text-[#888] font-medium uppercase tracking-[0.06em] text-[11px]">
                        <tr>
                            <th className="px-6 py-4">File Name</th>
                            <th className="px-6 py-4">Instance</th>
                            <th className="px-6 py-4">Size</th>
                            <th className="px-6 py-4">Last Modified</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-200 dark:divide-[#2a2a2a]">
                        {loading && documents.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-neutral-500">Loading documents...</td>
                            </tr>
                        ) : documents.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-neutral-500">No documents found.</td>
                            </tr>
                        ) : (
                            documents.map(doc => (
                                <tr key={doc.id} className="hover:bg-neutral-50 dark:hover:bg-[#252525] transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-4 h-4 text-[#e05a2b]" />
                                            <span className="font-medium">{doc.filename}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-neutral-600 dark:text-[#ccc]">{doc.instance}</td>
                                    <td className="px-6 py-4 text-neutral-500 dark:text-[#888]">{formatSize(doc.size)}</td>
                                    <td className="px-6 py-4 text-neutral-500 dark:text-[#888]">{formatDate(doc.modified)}</td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button className="p-2 text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors" title="Download">
                                                <Download className="w-4 h-4" />
                                            </button>
                                            <button className="p-2 text-neutral-400 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors" title="Delete">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
      </main>
    </div>
  );
}
"""
with open('/home/ubuntu/bublee-dev-react/src/app/panel/documents/page.tsx', 'w') as f:
    f.write(content)
