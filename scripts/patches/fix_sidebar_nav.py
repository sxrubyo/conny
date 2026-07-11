import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

nav_replacement = """import { Home, BarChart3, Settings, HelpCircle, FileText, Server, Menu, X, Shield, ScrollText } from "lucide-react";

const navigationItems: NavigationItem[] = [
  { id: "dashboard", name: "Home", icon: Home, href: "/panel/" },
  { id: "instances", name: "Instances", icon: Server, href: "/panel/instances/" },
  { id: "analytics", name: "Analytics", icon: BarChart3, href: "/panel/analytics/" },
  { id: "documents", name: "Documents", icon: FileText, href: "/panel/documents/" },
  { id: "security", name: "Security & API", icon: Shield, href: "/settings?tab=security" },
  { id: "logs", name: "System Logs", icon: ScrollText, href: "/panel/logs/" },
];"""

content = re.sub(r'import { Home, BarChart3, Settings, HelpCircle, FileText, Server, Menu, X } from "lucide-react";\n\nconst navigationItems: NavigationItem\[\] = \[\n.*?\];', nav_replacement, content, flags=re.DOTALL)

with open(filename, 'w') as f:
    f.write(content)
