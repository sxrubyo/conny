with open('/home/ubuntu/bublee/src/bublee/demo/handler.py', 'r') as f:
    js = f.read()

old_text = ' SESIÓN ACTIVA: Tienes una sesión de demo de 30 minutos con este usuario. NO es una conversación nueva.'
new_text = ' SESIÓN ACTIVA: Tienes una sesión de demo con este usuario. Si esta es tu primera interacción con ellos, haz la introducción COMPLETA explicando que eres una IA de prueba. Si ya te presentaste antes, simplemente continúa.'

if old_text in js:
    js = js.replace(old_text, new_text)
    with open('/home/ubuntu/bublee/src/bublee/demo/handler.py', 'w') as f:
        f.write(js)
    print("Fixed!")
else:
    print("Text not found")
