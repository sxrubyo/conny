import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add state for dashboard metrics
state_injection = """  const [dashboardData, setDashboardData] = useState<any>(null);
  
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const token = localStorage.getItem("dev_master_key") || "";
        const res = await fetch("/api/dev/dashboard", {
            headers: { "x-master-key": token }
        });
        if (res.ok) {
            const data = await res.json();
            setDashboardData(data.metrics);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchDashboard();
  }, []);
"""
content = content.replace('const [sidebarWidth, setSidebarWidth] = useState(240);', 'const [sidebarWidth, setSidebarWidth] = useState(240);\n' + state_injection)

# Replace the hardcoded KPI array with dashboardData or fallback
hardcoded_kpi = """{[
              { label: "Total Revenue", val: "$24,500", growth: "+12.5%", up: true },
              { label: "Total Order", val: "1,240", growth: "+8.2%", up: true },
              { label: "New customer", val: "320", growth: "-4.3%", up: false },
              { label: "Conversion rate", val: "3.2%", growth: "+2.1%", up: true },
            ]"""

dynamic_kpi = """(dashboardData || [
              { label: "Total Conversations", value: "-", growth: "0%", up: true },
              { label: "Messages Sent", value: "-", growth: "0%", up: true },
              { label: "Active Instances", value: "-", growth: "0%", up: true },
              { label: "Avg Response Time", value: "-", growth: "0%", up: true },
            ])"""
content = content.replace(hardcoded_kpi, dynamic_kpi)

# Fix the render of kpi.val -> kpi.value
content = content.replace('{kpi.val}', '{kpi.value || kpi.val}')

with open(filename, 'w') as f:
    f.write(content)
