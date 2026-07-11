import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# NAVBAR
content = content.replace('>Features<', '>Características<')
content = content.replace('>How it works<', '>Cómo funciona<')
content = content.replace('>Pricing<', '>Precios<')
content = content.replace('>Sign in<', '>Iniciar sesión<')
content = content.replace('>Get Template &rarr;<', '>Obtener Plantilla &rarr;<')

# HERO
content = content.replace('✦ Next-Gen AI Receptionist Platform', '✦ Plataforma de IA Next-Gen')

# H1 translation and styling
old_h1 = """            <h1 class="fade-up d-2">
                One Agent.<br>
                <span class="text-accent-infinite">Infinite</span> Clients.
            </h1>"""
new_h1 = """            <h1 class="fade-up d-2">
                Un Agente.<br>
                <span class="text-accent-infinite">Infinitos</span> <span style="font-weight: 600;">Clientes.</span>
            </h1>"""
content = content.replace(old_h1, new_h1)

# Hero subline
old_subline = """Deploy unlimited AI receptionists for your agency.<br>
                85% margins. Zero vendor lock-in."""
new_subline = """Despliega recepcionistas de IA ilimitados para tu agencia.<br>
                Márgenes del 85%. Sin ataduras tecnológicas."""
content = content.replace(old_subline, new_subline)

# Hero buttons
content = content.replace('Get Started Free &rarr;', 'Comienza Gratis &rarr;')
content = content.replace('See how it works', 'Mira cómo funciona')

# SDK SECTION
content = content.replace('Introducing Bublee SDK', 'Presentando Bublee SDK')
content = content.replace('Build AI agents that actually ship.', 'Construye agentes de IA listos para producción.')
content = content.replace('Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.', 'Bublee SDK es un framework moderno para construir, orquestar y desplegar aplicaciones de IA con código mínimo.')
content = content.replace('Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.', 'Crea agentes inteligentes, conecta herramientas, gestiona memoria y escala desde prototipos a producción — todo a través de una experiencia de desarrollo limpia y fluida.')
content = content.replace('Designed for founders, developers, and teams building the next generation of AI products.', 'Diseñado para fundadores, desarrolladores y equipos creando la próxima generación de productos de IA.')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
