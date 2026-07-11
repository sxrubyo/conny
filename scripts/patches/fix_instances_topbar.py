import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/instances/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add Topbar import
content = content.replace('import { Sidebar } from "@/components/ui/modern-side-bar";', 'import { Sidebar } from "@/components/ui/modern-side-bar";\nimport { Topbar } from "@/components/ui/topbar";')

# Add isDark state
if 'const [isDark, setIsDark] = useState(true);' not in content:
    content = content.replace('const [savingPrompt, setSavingPrompt] = useState(false);', 'const [savingPrompt, setSavingPrompt] = useState(false);\n  const [isDark, setIsDark] = useState(true);')

old_header = """          <div className="flex items-center justify-between">
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
          </div>"""

new_header = """          <Topbar title="Instances" subtitle="Manage all Bublee instances running on this server." isDark={isDark} setIsDark={setIsDark} />
          <div className="flex justify-end gap-3 mb-4">
              <button onClick={fetchInstances} className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors">
                <RefreshCw className={`w-5 h-5 text-neutral-600 dark:text-neutral-300 ${loading ? "animate-spin" : ""}`} />
              </button>
              <button onClick={createInstance} className="flex items-center gap-2 px-4 py-2 bg-[#e05a2b] text-white font-medium rounded-md hover:bg-[#c94e24] transition-colors">
                <Plus className="w-4 h-4" /> New Instance
              </button>
          </div>"""

content = content.replace(old_header, new_header)

with open(filename, 'w') as f:
    f.write(content)
