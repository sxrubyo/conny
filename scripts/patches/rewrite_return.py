import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Replace the block from return ( to <aside to ensure clean syntax
pattern = r'return \(\s*<>\s*<button.*?</button>\s*\{isOpen && \(\s*<div.*?\/>\s*\)\}\s*<aside'

new_str = """return (
    <>
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 rounded-md bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 md:hidden hover:bg-neutral-200 dark:hover:bg-neutral-200 dark:bg-neutral-800 transition-all duration-200"
      >
        {isOpen ? <X className="h-5 w-5 text-neutral-700 dark:text-neutral-300" /> : <Menu className="h-5 w-5 text-neutral-700 dark:text-neutral-300" />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden transition-opacity" onClick={toggleSidebar} />
      )}

      <aside"""

content = re.sub(pattern, new_str, content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
