import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/analytics/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add Topbar import
content = content.replace('import { Sidebar } from "@/components/ui/modern-side-bar";', 'import { Sidebar } from "@/components/ui/modern-side-bar";\nimport { Topbar } from "@/components/ui/topbar";')

# Add isDark state
content = content.replace('const [error, setError] = useState<string | null>(null);', 'const [error, setError] = useState<string | null>(null);\n  const [isDark, setIsDark] = useState(true);')

# Replace old header with Topbar
old_header = """          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Analytics</h1>
              <p className="text-neutral-500 dark:text-neutral-400">Global metrics across all instances.</p>
            </div>
            <button onClick={fetchAnalytics} className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors">
              <RefreshCw className={`w-5 h-5 text-neutral-600 dark:text-neutral-300 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>"""

new_header = """          <Topbar title="Analytics" subtitle="Global metrics across all instances." isDark={isDark} setIsDark={setIsDark} />
          <div className="flex justify-end mb-4">
              <button onClick={fetchAnalytics} className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors">
                  <RefreshCw className={`w-5 h-5 text-neutral-600 dark:text-neutral-300 ${loading ? "animate-spin" : ""}`} />
              </button>
          </div>"""

content = content.replace(old_header, new_header)

with open(filename, 'w') as f:
    f.write(content)
