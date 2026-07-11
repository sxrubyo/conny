import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# I will add a fetch for the chart data
if 'const [chartData, setChartData] = useState<any[]>(lineChartData);' not in content:
    content = content.replace('const [sales, setSales] = useState<any[]>([]);', 'const [sales, setSales] = useState<any[]>([]);\n  const [chartData, setChartData] = useState<any[]>([]);')
    
    fetch_logic = """
            const resChart = await fetch("/api/dev/chart", { headers: { "x-master-key": token } });
            if (resChart.ok) {
                const data = await resChart.json();
                setChartData(data.chartData || []);
            }
"""
    content = content.replace('setSales(data.sales || []);', 'setSales(data.sales || []);\n' + fetch_logic)
    
    # Replace lineChartData usage with chartData
    content = content.replace('data={lineChartData}', 'data={chartData.length > 0 ? chartData : lineChartData}')

with open(filename, 'w') as f:
    f.write(content)
