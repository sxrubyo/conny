with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Revert greeting logic
old_greeting_logic = """    const randomGreeting = possibleGreetings[Math.floor(Math.random() * possibleGreetings.length)];
    
    // Convert string like "Hola, Santiago" to a React element if it contains Santiago
    const greetingElement = (
      <span>
        {randomGreeting.replace('Santiago', '')}
        {randomGreeting.includes('Santiago') && (
          <span className={`${caveat.className} text-[#b91c1c] text-5xl ml-1`}>
            Santiago
          </span>
        )}
      </span>
    );
    
    setGreeting(greetingElement as any);"""

new_greeting_logic = """    const randomGreeting = possibleGreetings[Math.floor(Math.random() * possibleGreetings.length)];
    setGreeting(randomGreeting);"""

content = content.replace(old_greeting_logic, new_greeting_logic)

# 2. Revert Header HTML
old_h1 = '<h1 className="text-4xl lg:text-5xl font-extrabold text-neutral-900 dark:text-white tracking-tight leading-tight">{greeting}</h1>'
new_h1 = '<h1 className="text-2xl lg:text-3xl font-medium text-neutral-900 dark:text-white tracking-tight">{greeting}</h1>'

old_p = '<p className="text-neutral-500 dark:text-[#888888] text-lg lg:text-xl mt-2 font-medium">Resumen general de rendimiento</p>'
new_p = '<p className="text-neutral-500 dark:text-[#888888] text-base mt-1">Resumen general de rendimiento</p>'

content = content.replace(old_h1, new_h1)
content = content.replace(old_p, new_p)

# We changed useState<React.ReactNode> earlier, let's change it back to string
content = content.replace('useState<React.ReactNode>("Dashboard")', 'useState<string>("Dashboard")')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
