import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'r') as f:
    content = f.read()

# Replace <a href={item.url}>
content = content.replace(
'''<a href={item.url}>
                      <item.icon className="text-neutral-400" />
                      <span>{item.title}</span>
                    </a>''',
'''<button onClick={() => { window.location.href = item.url; }} className="w-full flex items-center justify-start text-left">
                      <item.icon className="text-neutral-400 mr-2" />
                      <span>{item.title}</span>
                    </button>'''
)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'w') as f:
    f.write(content)
