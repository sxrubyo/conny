import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/instances/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add a modal for settings
imports = 'import { Plus, Trash2, RefreshCw, Server, Activity, Settings2, Play, Square, AlertCircle, X, Save } from "lucide-react";'
content = content.replace('import { Plus, Trash2, RefreshCw, Server, Activity, Settings2, Play, Square, AlertCircle } from "lucide-react";', imports)

states = """
  const [configuringInstance, setConfiguringInstance] = useState<any | null>(null);
  const [instancePrompt, setInstancePrompt] = useState("");
  const [savingPrompt, setSavingPrompt] = useState(false);
"""
content = content.replace('const [loading, setLoading] = useState(true);', 'const [loading, setLoading] = useState(true);\n' + states)

configure_func = """
  const openConfigure = async (inst: any) => {
      setConfiguringInstance(inst);
      setInstancePrompt("Loading prompt...");
      try {
          const token = localStorage.getItem("dev_master_key") || "";
          const res = await fetch(`/api/dev/instances/${inst.name}/prompt`, {
              headers: { "x-master-key": token }
          });
          if (res.ok) {
              const data = await res.json();
              setInstancePrompt(data.prompt || "");
          } else {
              setInstancePrompt("Error loading prompt.");
          }
      } catch (e) {
          setInstancePrompt("Error loading prompt.");
      }
  };

  const saveConfigure = async () => {
      if(!configuringInstance) return;
      setSavingPrompt(true);
      try {
          const token = localStorage.getItem("dev_master_key") || "";
          const res = await fetch(`/api/dev/instances/${configuringInstance.name}/prompt`, {
              method: "POST",
              headers: { 
                  "Content-Type": "application/json",
                  "x-master-key": token 
              },
              body: JSON.stringify({ prompt: instancePrompt })
          });
          if (res.ok) {
              setConfiguringInstance(null);
          } else {
              alert("Error saving prompt.");
          }
      } catch (e) {
          alert("Error saving prompt.");
      }
      setSavingPrompt(false);
  };
"""
content = content.replace('useEffect(() => {', configure_func + '\n  useEffect(() => {')

# Add onClick to Configure button
content = content.replace('title="Configure"\n                      >', 'title="Configure"\n                        onClick={() => openConfigure(inst)}\n                      >')

modal_jsx = """
      {configuringInstance && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl shadow-2xl w-full max-w-3xl flex flex-col max-h-[90vh]">
                <div className="flex items-center justify-between p-5 border-b border-neutral-200 dark:border-neutral-800">
                    <div>
                        <h2 className="text-xl font-bold text-neutral-900 dark:text-white">Configure: {configuringInstance.name}</h2>
                        <p className="text-sm text-neutral-500 mt-1">Update system prompt and configuration.</p>
                    </div>
                    <button onClick={() => setConfiguringInstance(null)} className="p-2 text-neutral-500 hover:text-neutral-900 dark:hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-5 flex-1 overflow-y-auto">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">System Prompt</label>
                            <textarea 
                                value={instancePrompt}
                                onChange={(e) => setInstancePrompt(e.target.value)}
                                className="w-full h-96 p-4 bg-neutral-50 dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-lg text-sm text-neutral-900 dark:text-neutral-200 font-mono resize-none focus:outline-none focus:ring-2 focus:ring-[#e05a2b]"
                                placeholder="Loading..."
                            />
                        </div>
                    </div>
                </div>
                <div className="p-5 border-t border-neutral-200 dark:border-neutral-800 flex justify-end gap-3">
                    <button onClick={() => setConfiguringInstance(null)} className="px-4 py-2 font-medium text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md transition-colors">
                        Cancel
                    </button>
                    <button onClick={saveConfigure} disabled={savingPrompt} className="flex items-center gap-2 px-4 py-2 font-medium bg-[#e05a2b] text-white rounded-md hover:bg-[#c94e24] transition-colors disabled:opacity-50">
                        {savingPrompt ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Save Prompt
                    </button>
                </div>
            </div>
        </div>
      )}
"""
content = content.replace('</main>\n    </div>', modal_jsx + '\n      </main>\n    </div>')

with open(filename, 'w') as f:
    f.write(content)
