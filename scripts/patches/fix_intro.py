import re

files_to_fix = [
    '/home/ubuntu/bublee/src/bublee/demo/handler.py',
    '/home/ubuntu/bublee/src/interfaces/web/demo_handler.py',
    '/home/ubuntu/bublee/src/domain/send_guard.py',
    '/home/ubuntu/bublee/src/bublee/production/guard.py',
    '/home/ubuntu/bublee/src/core/admin_engines.py',
    '/home/ubuntu/bublee/src/core/runtime.py'
]

# In handler.py, there are multiple fallbacks for when the user says "Hola" or "qué es esto".
# Let's replace the abrupt fallbacks with a better introduction.

def replace_in_file(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            
        # Replace 1: "hola ||| necesito el nombre de tu negocio para arrancar"
        content = content.replace(
            '"hola ||| necesito el nombre de tu negocio para arrancar"',
            '"¡hola! soy Bublee 👋, un agente de IA para WhatsApp ||| me pasaron tu contacto para hacerte una demostración en vivo ||| antes de arrancar, ¿cómo se llama tu empresa o clínica?"'
        )
        
        # Replace 2: "antes de mostrarte cómo funciono, necesito el nombre de tu negocio o clínica ||| cuál es?"
        content = content.replace(
            '"antes de mostrarte cómo funciono, necesito el nombre de tu negocio o clínica ||| cuál es?"',
            '"¡hola! soy Bublee 👋, un agente de IA que atiende WhatsApp automáticamente ||| para mostrarte una demo en vivo, necesito adaptar mi tono ||| ¿cómo se llama tu empresa o clínica?"'
        )
        
        # Replace 3: send_guard.py and guard.py
        content = content.replace(
            'return f"un momentico ||| ¿cómo se llama tu negocio?"',
            'return f"¡hola! soy Bublee 👋, una IA para WhatsApp ||| me pasaron tu contacto para una demostración ||| ¿cómo se llama tu empresa o clínica?"'
        )
        content = content.replace(
            'return f"cuéntame, ¿cómo se llama tu negocio?"',
            'return f"¡hola! soy Bublee 👋 ||| para hacerte una demostración en vivo, necesito saber ¿cómo se llama tu empresa o clínica?"'
        )
        
        # Replace 4: admin_engines.py
        content = content.replace(
            'return ["Hola! Soy Bublee, tu recepcionista nueva", "Cuéntame, cómo se llama tu negocio?"]',
            'return ["¡Hola! 👋 Soy Bublee, una inteligencia artificial creada para atender tu WhatsApp automáticamente.", "Antes de empezar a responderle a tus clientes, necesito conocer bien tu negocio.", "¿Cómo se llama tu empresa o clínica?"]'
        )
        
        # Replace 5: runtime.py
        content = content.replace(
            '"hola! soy Bublee, tu nueva recepcionista virtual 👋\nantes de empezar a atender clientes necesito conocer bien el negocio\npara poder responder bien |||\ncuéntame: ¿cómo se llama el negocio y qué ofrecen?"',
            '"¡Hola! 👋 Soy Bublee, un agente de IA para atender tu WhatsApp automáticamente.\nantes de empezar a atender clientes, necesito conocer bien tu negocio.\n¿Cómo se llama tu empresa o clínica?"'
        )

        with open(filename, 'w') as f:
            f.write(content)
            
        print(f"Fixed {filename}")
    except FileNotFoundError:
        pass

for f in files_to_fix:
    replace_in_file(f)

