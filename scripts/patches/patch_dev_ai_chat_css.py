import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix the Tailwind classes used in the patch to be inline styles so they work without Tailwind.
html = html.replace('class="absolute inset-0 w-full h-full overflow-hidden pointer-events-none"', 'style="position: absolute; inset: 0; width: 100%; height: 100%; overflow: hidden; pointer-events: none;"')

html = html.replace('class="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal blur-[128px]"', 'style="position: absolute; top: 0; left: 25%; width: 24rem; height: 24rem; background-color: rgba(139, 92, 246, 0.1); border-radius: 9999px; mix-blend-mode: normal; filter: blur(128px); animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;"')

html = html.replace('class="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal blur-[128px]"', 'style="position: absolute; bottom: 0; right: 25%; width: 24rem; height: 24rem; background-color: rgba(99, 102, 241, 0.1); border-radius: 9999px; mix-blend-mode: normal; filter: blur(128px); animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite 700ms;"')

html = html.replace('class="absolute top-1/4 right-1/3 w-64 h-64 bg-fuchsia-500/10 rounded-full mix-blend-normal blur-[96px]"', 'style="position: absolute; top: 25%; right: 33.333333%; width: 16rem; height: 16rem; background-color: rgba(217, 70, 239, 0.1); border-radius: 9999px; mix-blend-mode: normal; filter: blur(96px); animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite 1000ms;"')

html = html.replace('class="w-full max-w-2xl mx-auto relative z-10 space-y-12 transition-all duration-700 ease-out translate-y-0 opacity-100"', 'style="width: 100%; max-width: 42rem; margin-left: auto; margin-right: auto; position: relative; z-index: 10; transition: all 700ms ease-out; transform: translateY(0); opacity: 1; padding: 24px;"')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
