with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Add font import
font_import = """import { LineChart, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Caveat } from 'next/font/google';

const caveat = Caveat({ subsets: ['latin'] });
"""
content = content.replace('import { LineChart, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";', font_import)

# Change header sizes
old_header = """<h1 className="text-xl lg:text-2xl font-bold text-neutral-900 dark:text-white tracking-tight">{greeting}</h1>
              <p className="text-neutral-500 dark:text-[#888888] text-sm mt-1">Resumen general de rendimiento</p>"""

new_header = """<h1 className="text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
                {greeting.split('Santiago').map((part, i, arr) => (
                  <React.Fragment key={i}>
                    {part}
                    {i < arr.length - 1 && (
                      <span className={`${caveat.className} text-[#b91c1c] text-4xl lg:text-5xl font-normal mx-1`}>Santiago</span>
                    )}
                  </React.Fragment>
                ))}
              </h1>
              <p className="text-neutral-500 dark:text-[#888888] text-base mt-2">Resumen general de rendimiento</p>"""
content = content.replace(old_header, new_header)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
