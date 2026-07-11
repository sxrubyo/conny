import re

filename = '/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add a state for language
if 'const [language, setLanguage] = useState("en");' not in content:
    content = content.replace('const [isDark, setIsDark] = useState(true);', 'const [isDark, setIsDark] = useState(true);\n  const [language, setLanguage] = useState("en");')

# Let's insert the select before the Dark mode toggle, or inside the same section (Preferences)
# "Theme" is inside:
# <label className={labelStyle} style={{ marginBottom: 0 }}>Theme</label>
# Let's see the context
theme_html = """
                                <div className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-[#1a1a1a] rounded-xl border border-neutral-200 dark:border-neutral-800">
                                    <label className={labelStyle} style={{ marginBottom: 0 }}>Theme</label>
"""

new_pref_html = """
                                <div className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-[#1a1a1a] rounded-xl border border-neutral-200 dark:border-neutral-800 mb-4">
                                    <label className="text-[11px] uppercase tracking-[0.06em] text-neutral-500 dark:text-[#888] font-medium" style={{ marginBottom: 0 }}>Language</label>
                                    <select 
                                        value={language}
                                        onChange={(e) => setLanguage(e.target.value)}
                                        className="bg-white dark:bg-[#111] border border-neutral-200 dark:border-[#333] text-sm rounded-md px-3 py-1 outline-none focus:border-[#e05a2b]"
                                    >
                                        <option value="en">English (US)</option>
                                        <option value="es">Español (ES)</option>
                                    </select>
                                </div>
                                <div className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-[#1a1a1a] rounded-xl border border-neutral-200 dark:border-neutral-800">
                                    <label className="text-[11px] uppercase tracking-[0.06em] text-neutral-500 dark:text-[#888] font-medium" style={{ marginBottom: 0 }}>Theme</label>
"""

content = content.replace(theme_html, new_pref_html)

with open(filename, 'w') as f:
    f.write(content)
