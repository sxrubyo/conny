import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Replace hardcoded countrySales state
if 'const [sales, setSales] = useState<any[]>([]);' not in content:
    content = content.replace('const [greeting, setGreeting] = useState<string>("Dashboard");', 'const [greeting, setGreeting] = useState<string>("Dashboard");\n  const [sales, setSales] = useState<any[]>([]);')
    
    fetch_logic = """
  useEffect(() => {
    const fetchSales = async () => {
        try {
            const token = localStorage.getItem("dev_master_key") || "";
            const res = await fetch("/api/dev/sales", { headers: { "x-master-key": token } });
            if (res.ok) {
                const data = await res.json();
                setSales(data.sales || []);
            }
        } catch(e) {}
    };
    fetchSales();
  }, []);
"""
    content = content.replace('useEffect(() => {', fetch_logic + '\n  useEffect(() => {')

# Replace countrySales map
content = content.replace('{countrySales.map((c, i) => (', '{sales.length === 0 ? <div className="col-span-2 text-center text-sm text-neutral-500 py-4">No sales data yet</div> : sales.map((c: any, i: number) => (')
content = content.replace('c.flag', 'c.country_code')
content = content.replace('c.sales', 'c.sales_amount + " Products"')

# Also remove const countrySales = [...]
content = re.sub(r'const countrySales = \[.*?\];', '', content, flags=re.DOTALL)

with open(filename, 'w') as f:
    f.write(content)
