with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Change Dashboard to Menu
content = content.replace('{ id: "dashboard", name: "Dashboard", icon: Home, href: "/panel/" },', 
                          '{ id: "dashboard", name: "Menu", icon: Home, href: "/panel/" },')

# Remove Notifications, Profile, Settings, Help
content = content.replace('{ id: "notifications", name: "Notifications", icon: Bell, href: "/notifications", badge: "12" },\n', '')
content = content.replace('{ id: "profile", name: "Profile", icon: User, href: "/profile" },\n', '')
content = content.replace('{ id: "settings", name: "Settings", icon: Settings, href: "/settings" },\n', '')
content = content.replace('{ id: "help", name: "Help & Support", icon: HelpCircle, href: "/help" },\n', '')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
