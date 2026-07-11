import re

with open('/home/ubuntu/bublee/src/bublee/demo/handler.py', 'r') as f:
    content = f.read()

# Add holaaa, holis, holaa to _conversational
new_conv = '"hola","holaa","holaaa","holis","buenas","hey","ey","holi"'
content = content.replace('"hola","buenas","hey","ey","holi"', new_conv)

# Update the LLM constraint to strictly forbid "recepcionista virtual"
content = content.replace('REGLA ESTRICTA DE INTRODUCCIÓN: NO digas "soy la recepcionista virtual"', 'REGLA ESTRICTA DE INTRODUCCIÓN: NUNCA uses la frase "soy la recepcionista virtual" (jamás, prohibido) porque el usuario creerá que te equivocaste de chat. DEBES explicar que eres una IA de prueba.')

with open('/home/ubuntu/bublee/src/bublee/demo/handler.py', 'w') as f:
    f.write(content)
