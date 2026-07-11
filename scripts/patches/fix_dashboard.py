import re

filename = '/home/ubuntu/bublee/src/bublee/admin/dashboard.py'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace(
    'return ["Hola! Soy Bublee, tu recepcionista nueva", "Cuéntame, cómo se llama tu negocio?"]',
    'return ["¡Hola! 👋 Soy Bublee, una inteligencia artificial creada para atender tu WhatsApp automáticamente.", "Antes de empezar a responderle a tus clientes, necesito conocer bien tu negocio.", "¿Cómo se llama tu empresa o clínica?"]'
)

with open(filename, 'w') as f:
    f.write(content)
