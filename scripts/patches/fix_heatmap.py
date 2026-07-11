import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add state and fetch
if 'const [heatmapData, setHeatmapData] = useState<number[][]>([]);' not in content:
    content = content.replace('const [chartData, setChartData] = useState<any[]>([]);', 'const [chartData, setChartData] = useState<any[]>([]);\n  const [heatmapData, setHeatmapData] = useState<number[][]>([]);')
    
    fetch_heatmap = """
            const resHeatmap = await fetch("/api/dev/heatmap", { headers: { "x-master-key": token } });
            if (resHeatmap.ok) {
                const dataHeat = await resHeatmap.json();
                setHeatmapData(dataHeat.heatmapData || []);
            }
"""
    content = content.replace('setChartData(data.chartData || []);', 'setChartData(data.chartData || []);\n' + fetch_heatmap)

    # replace getHeatmapColor
    new_get_color = """
  const getHeatmapColor = (dIndex: number, hIndex: number) => {
    if (heatmapData.length === 0) return 'bg-[#2e2e2e] dark:bg-[#2e2e2e] bg-neutral-200';
    const val = heatmapData[dIndex] ? heatmapData[dIndex][hIndex] : 0;
    if (val > 2000) return 'bg-[#b91c1c] relative overflow-hidden after:content-[""] after:absolute after:inset-0 after:opacity-30 after:bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.2)_25%,rgba(255,255,255,0.2)_50%,transparent_50%,transparent_75%,rgba(255,255,255,0.2)_75%,rgba(255,255,255,0.2)_100%)] after:bg-[length:8px_8px]';
    if (val > 1000) return 'bg-[#c24a1a]';
    if (val > 500) return 'bg-[#7a2e10]';
    return 'bg-[#2e2e2e] dark:bg-[#2e2e2e] bg-neutral-200';
  };
"""
    content = re.sub(r'const getHeatmapColor = \(dIndex: number, hIndex: number\) => \{.*?return \'bg-\[#2e2e2e\] dark:bg-\[#2e2e2e\] bg-neutral-200\';\n  \};', new_get_color.strip(), content, flags=re.DOTALL)

with open(filename, 'w') as f:
    f.write(content)
