import re
with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Replace the top avatar logic to point to settings
old_avatar = """<div className="h-9 w-9 rounded-full bg-[#e05a2b] flex items-center justify-center text-white text-xs font-bold shrink-0">
                SR
              </div>"""
new_avatar = """<button onClick={() => window.location.href='/settings'} className="h-9 w-9 rounded-full bg-red-900/80 hover:bg-red-800 transition-colors flex items-center justify-center text-white text-xs font-bold shrink-0">
                SR
              </button>"""
content = content.replace(old_avatar, new_avatar)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
