with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Subtle animations (fade and blur on load)
# We can wrap the main content in a div with an animation class.
# We will define keyframes in a style tag at the top of the component.
animation_styles = """
  <style>{`
    @keyframes subtleReveal {
      0% { opacity: 0; filter: blur(4px); transform: scale(0.99); }
      100% { opacity: 1; filter: blur(0px); transform: scale(1); }
    }
    .animate-premium {
      animation: subtleReveal 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }
    .transition-premium {
      transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
  `}</style>
"""
content = content.replace('<div className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full">', animation_styles + '\n        <div className="flex-1 p-4 lg:p-6 max-w-[1400px] mx-auto w-full animate-premium">')

# 2. Reduce font sizes and padding to make it look "100% scale premium"
content = content.replace('text-2xl lg:text-3xl', 'text-xl lg:text-2xl') # Header greeting
content = content.replace('text-2xl font-bold', 'text-lg font-bold') # KPI values
content = content.replace('p-5', 'p-4') # KPI padding
content = content.replace('p-6', 'p-4') # Other cards padding
content = content.replace('mb-8', 'mb-6') # Top bar margin
content = content.replace('mb-6', 'mb-4') # Row margins
content = content.replace('gap-6', 'gap-4') # Grid gaps
content = content.replace('h-[250px]', 'h-[220px]') # Chart height

# 3. Add hover effects with slight blur to cards
content = content.replace('transition-colors', 'transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)]')
content = content.replace('hover:border-[#e05a2b]/50', 'hover:border-red-500/30 dark:hover:border-red-500/30')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
