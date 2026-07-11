import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

old_h1 = '<h1 className="text-xl lg:text-lg font-bold text-neutral-900 dark:text-white tracking-tight">{greeting}</h1>'
new_h1 = '<h1 className="text-4xl lg:text-5xl font-extrabold text-neutral-900 dark:text-white tracking-tight leading-tight">{greeting}</h1>'

old_p = '<p className="text-neutral-500 dark:text-[#888888] text-sm mt-1">Resumen general de rendimiento</p>'
new_p = '<p className="text-neutral-500 dark:text-[#888888] text-lg lg:text-xl mt-2 font-medium">Resumen general de rendimiento</p>'

content = content.replace(old_h1, new_h1)
content = content.replace(old_p, new_p)

# Also check for Caveat font import because the previous summarizer said "Implemented a custom Caveat font import for the name Santiago"
if 'Caveat' not in content:
    content = content.replace('import { ExpandingSearchDock } from "@/components/ui/expanding-search-dock-shadcnui";', 'import { ExpandingSearchDock } from "@/components/ui/expanding-search-dock-shadcnui";\nimport { Caveat } from "next/font/google";\n\nconst caveat = Caveat({ subsets: ["latin"] });')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
