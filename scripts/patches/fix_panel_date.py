import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Make the date dynamic
if 'const [currentDate, setCurrentDate] = useState("");' not in content:
    content = content.replace('const [greeting, setGreeting] = useState<string>("Dashboard");', 'const [greeting, setGreeting] = useState<string>("Dashboard");\n  const [currentDate, setCurrentDate] = useState("");')
    
    date_effect = """
  useEffect(() => {
    // intelligent date based on locale
    const date = new Date();
    const options: Intl.DateTimeFormatOptions = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
    setCurrentDate(date.toLocaleDateString(undefined, options));
  }, []);
"""
    content = content.replace('useEffect(() => {', date_effect + '\n  useEffect(() => {')
    content = content.replace('<span>Wed, 29 May 2024</span>', '<span>{currentDate}</span>')

with open(filename, 'w') as f:
    f.write(content)
