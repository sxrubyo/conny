import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Replace greeting logic
old_greeting_logic = """    const randomGreeting = possibleGreetings[Math.floor(Math.random() * possibleGreetings.length)];
    setGreeting(randomGreeting);
  }, []);"""

new_greeting_logic = """    const randomGreeting = possibleGreetings[Math.floor(Math.random() * possibleGreetings.length)];
    
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
    
    setGreeting(greetingElement as any);
  }, []);"""

content = content.replace(old_greeting_logic, new_greeting_logic)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
