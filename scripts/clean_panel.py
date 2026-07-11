import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# The file got messed up with multiple duplicated fetchSales functions due to regex replaces.
# Let's remove all fetchSales and insert one clean version.
# find the start of the first useEffect(() => { const fetchSales
start_idx = content.find('  useEffect(() => {\n    const fetchSales')
if start_idx != -1:
    # find the start of the next useEffect, which is intelligent date
    end_idx = content.find('  useEffect(() => {\n    // intelligent date', start_idx)
    
    # We might have multiple of these fetchSales blocks. Let's remove them all first.
    content = re.sub(r'  useEffect\(\(\) => \{\n    const fetchSales.*?  \}, \[\]\);\n\n\n', '', content, flags=re.DOTALL)
    content = re.sub(r'  useEffect\(\(\) => \{\n    const fetchSales.*?  \}, \[\]\);\n\n', '', content, flags=re.DOTALL)

clean_fetch = """  useEffect(() => {
    const fetchAllData = async () => {
        try {
            const token = localStorage.getItem("dev_master_key") || "";
            
            // Sales
            fetch("/api/dev/sales", { headers: { "x-master-key": token } })
                .then(res => res.json())
                .then(data => { if(data.sales) setSales(data.sales); })
                .catch(e => console.error(e));

            // Chart
            fetch("/api/dev/chart", { headers: { "x-master-key": token } })
                .then(res => res.json())
                .then(data => { if(data.chartData) setChartData(data.chartData); })
                .catch(e => console.error(e));

            // Heatmap
            fetch("/api/dev/heatmap", { headers: { "x-master-key": token } })
                .then(res => res.json())
                .then(data => { if(data.heatmapData) setHeatmapData(data.heatmapData); })
                .catch(e => console.error(e));

        } catch(e) {}
    };
    fetchAllData();
  }, []);

"""

# Insert it before the intelligent date hook
content = content.replace('  useEffect(() => {\n    // intelligent date', clean_fetch + '  useEffect(() => {\n    // intelligent date')

with open(filename, 'w') as f:
    f.write(content)
