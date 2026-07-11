import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add useRouter import
if 'useRouter' not in content:
    content = content.replace("import { usePathname } from 'next/navigation';", "import { usePathname, useRouter } from 'next/navigation';")

# Add router instance
if 'const router = useRouter();' not in content:
    content = content.replace('const pathname = usePathname();', 'const pathname = usePathname();\n  const router = useRouter();')

# Fix handleItemClick
old_handle = """  const handleItemClick = (itemId: string, href: string) => {
    if(itemId === "logout") {
        window.location.href = '/api/auth/login';
        return;
    }

    // Force trailing slash or whatever mapping needed if using /dev-portal
    if (href && href !== window.location.pathname) {
        window.location.href = href;
        return;
    }

    setActiveItem(itemId);
    if (window.innerWidth < 768) {
      setIsOpen(false);
    }
  };"""

new_handle = """  const handleItemClick = (itemId: string, href: string) => {
    if(itemId === "logout") {
        window.location.href = '/dev-portal/login/';
        return;
    }

    if (href) {
        router.push(href);
        setActiveItem(itemId);
        if (window.innerWidth < 768) {
            setIsOpen(false);
        }
        return;
    }

    setActiveItem(itemId);
    if (window.innerWidth < 768) {
      setIsOpen(false);
    }
  };"""

content = content.replace(old_handle, new_handle)

# Let's also check the bottom profile link
content = content.replace("handleItemClick('settings', '/settings')", "handleItemClick('settings', '/settings/')")

with open(filename, 'w') as f:
    f.write(content)
