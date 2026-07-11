import re

content = """"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/modern-side-bar";
import { Plus, Trash2, RefreshCw, Server, Activity, Settings2, Play, Square, AlertCircle } from "lucide-react";

export default function InstancesPage() {
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInstances = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("dev_master_key") || "";
      const res = await fetch("/api/dev/instances", {
        headers: {
            "x-master-key": token
        }
      });
      if (!res.ok) {
          throw new Error("Could not load instances");
      }
      const data = await res.json();
      setInstances(data.instances || []);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to load instances");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchInstances();
  }, []);

  const createInstance = async () => {
    try {
      const token = localStorage.getItem("dev_master_key") || "";
      const res = await fetch("/api/dev/instances/new", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "x-master-key": token
        },
        body: JSON.stringify({ name: "nueva-instancia" })
      });
      if (res.ok) fetchInstances();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen w-full bg-neutral-50 dark:bg-[#111111] overflow-hidden font-sans">
      <Sidebar />
      <main className="flex-1 overflow-y-auto custom-scrollbar p-8 text-neutral-900 dark:text-white">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Instances</h1>
              <p className="text-neutral-500 dark:text-neutral-400">Manage all Bublee instances running on this server.</p>
            </div>
            <div className="flex gap-3">
              <button onClick={fetchInstances} className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors">
                <RefreshCw className={`w-5 h-5 text-neutral-600 dark:text-neutral-300 ${loading ? "animate-spin" : ""}`} />
              </button>
              <button onClick={createInstance} className="flex items-center gap-2 px-4 py-2 bg-[#e05a2b] text-white font-medium rounded-md hover:bg-[#c94e24] transition-colors">
                <Plus className="w-4 h-4" /> New Instance
              </button>
            </div>
          </div>

          {error && (
            <div className="flex items-center justify-between p-4 bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 rounded-xl">
                <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    <span className="font-medium">{error}</span>
                </div>
                <button onClick={fetchInstances} className="px-3 py-1 text-sm font-medium bg-red-500/20 hover:bg-red-500/30 rounded-md transition-colors">
                    Retry
                </button>
            </div>
          )}

          <div className="grid gap-4">
            {loading && instances.length === 0 ? (
                // Skeletons
                <>
                    {[1, 2, 3].map(i => (
                        <div key={i} className="flex items-center justify-between p-5 bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl animate-pulse">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-neutral-200 dark:bg-neutral-800 rounded-lg"></div>
                                <div className="space-y-2">
                                    <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-800 rounded"></div>
                                    <div className="h-4 w-48 bg-neutral-200 dark:bg-neutral-800 rounded"></div>
                                </div>
                            </div>
                        </div>
                    ))}
                </>
            ) : (
                instances.map(inst => (
                  <div key={inst.name} className="flex items-center justify-between p-5 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors shadow-sm">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-950 rounded-lg border border-neutral-200 dark:border-neutral-800 flex items-center justify-center">
                        <Server className="w-6 h-6 text-neutral-500 dark:text-neutral-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg text-neutral-900 dark:text-white">{inst.name}</h3>
                        <div className="flex items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                          <span className="flex items-center gap-1 font-medium capitalize">
                            <span className={`w-2 h-2 rounded-full ${inst.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                            <span className={inst.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                                {inst.status}
                            </span>
                          </span>
                          <span>•</span>
                          <span>{inst.sector || 'N/A'}</span>
                          <span>•</span>
                          <span>Port: {inst.port}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      {inst.status === 'online' ? (
                          <button className="flex items-center justify-center w-10 h-10 border border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/20 rounded-md transition-colors" title="Stop">
                            <Square className="w-4 h-4 fill-current" />
                          </button>
                      ) : (
                          <button className="flex items-center justify-center w-10 h-10 border border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:bg-emerald-500/10 hover:text-emerald-500 hover:border-emerald-500/20 rounded-md transition-colors" title="Start">
                            <Play className="w-4 h-4 fill-current" />
                          </button>
                      )}
                      
                      <button className="flex items-center justify-center w-10 h-10 border border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md transition-colors" title="Configure">
                        <Settings2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ))
            )}
            {!loading && instances.length === 0 && !error && (
              <div className="text-center py-12 text-neutral-500 border border-dashed border-neutral-200 dark:border-neutral-800 rounded-xl">
                No instances found.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
"""

with open('/home/ubuntu/bublee-dev-react/src/app/panel/instances/page.tsx', 'w') as f:
    f.write(content)
