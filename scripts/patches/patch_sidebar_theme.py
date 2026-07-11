import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# 1. Change bg-neutral-950 to bg-[#111111] (Carbon)
content = content.replace('bg-neutral-950', 'bg-[#111111]')

# 2. Fix isotype.png path
content = content.replace('src="/isotype.png"', 'src="/dev-portal/isotype.png"')
content = content.replace("style={{ filter: \"brightness(0) invert(1)\" }}", "")

# 3. Add Theme toggle icon logic
# Import Sun and Moon from lucide-react if not present
if 'Sun,' not in content and 'Moon,' not in content:
    content = content.replace('LogOut,', 'LogOut, Sun, Moon,')

# Add a theme state and toggle handler (Mock for now, but UI functional)
if 'const [isThemeDark, setIsThemeDark]' not in content:
    hook_code = """
  const [isThemeDark, setIsThemeDark] = useState(true);
  const toggleTheme = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsThemeDark(!isThemeDark);
    // In a real app we would toggle a class on the html element
    if (!isThemeDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  };
"""
    content = content.replace('const [isCollapsed, setIsCollapsed] = useState(false);', 'const [isCollapsed, setIsCollapsed] = useState(false);' + hook_code)

# Let's add the Moon/Sun toggle in the profile button bottom section
# Find the Profile block
profile_html = '''
            {!isCollapsed ? (
              <button onClick={() => setShowProfileMenu(!showProfileMenu)} className="w-full flex items-center px-3 py-2.5 rounded-lg hover:bg-neutral-900 transition-colors duration-200">
                <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">
                  <img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 min-w-0 ml-3 text-left">
                  <p className="text-sm font-medium text-white truncate">Santiago</p>
                  <p className="text-xs text-neutral-500 truncate">Santi21435@gmail.com</p>
                </div>
                <div 
                    onClick={toggleTheme} 
                    className="p-1.5 rounded-md hover:bg-neutral-800 text-neutral-400 hover:text-white transition-all ml-2"
                    title="Toggle Theme"
                >
                    {isThemeDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </div>
              </button>
'''
content = re.sub(r'\{\!isCollapsed \? \(\n\s+<button onClick=\{.*?className="w-full flex items-center px-3 py-2\.5 rounded-lg hover:bg-neutral-900 transition-colors duration-200">\n\s+<div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">\n\s+<img src="https://images\.unsplash\.com/photo.*? className="w-full h-full object-cover".*?/>\n\s+</div>\n\s+<div className="flex-1 min-w-0 ml-3 text-left">\n\s+<p className="text-sm font-medium text-white truncate">Santiago</p>\n\s+<p className="text-xs text-neutral-500 truncate">Santi21435@gmail\.com</p>\n\s+</div>\n\s+</button>', profile_html.strip(), content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
