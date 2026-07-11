with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Spacing
content = content.replace('padding-top: 60px;', 'padding-top: 80px;')

# Navbar
content = content.replace('>Características<', '>Features<')
content = content.replace('>Cómo funciona<', '>How it works<')
content = content.replace('>Precios<', '>Pricing<')
content = content.replace('>Iniciar sesión<', '>Sign in<')
content = content.replace('>Obtener Plantilla &rarr;<', '>Get Template &rarr;<')

# Hero Eyebrow
content = content.replace('✦ Plataforma de IA Next-Gen', '✦ Next-Gen AI Receptionist Platform')

# Hero H1
old_h1 = """            <h1 class="fade-up d-2">
                Un Agente<br>
                Clientes <span class="text-accent-infinite">Infinitos</span>.
            </h1>"""
new_h1 = """            <h1 class="fade-up d-2">
                One Agent.<br>
                <span class="text-accent-infinite">Infinite</span> Clients.
            </h1>"""
content = content.replace(old_h1, new_h1)

# Hero Subline
old_subline = """Despliega recepcionistas de IA ilimitados para tu agencia.<br>
                Márgenes del 85%. Sin ataduras tecnológicas."""
new_subline = """Deploy unlimited AI receptionists for your agency.<br>
                85% margins. Zero vendor lock-in."""
content = content.replace(old_subline, new_subline)

# Hero Buttons
content = content.replace('Comienza Gratis &rarr;', 'Get Started Free &rarr;')
content = content.replace('Mira cómo funciona', 'See how it works')

# SDK Section
content = content.replace('Presentando Bublee SDK', 'Introducing Bublee SDK')
content = content.replace('Construye agentes de IA listos para producción.', 'Build AI agents that actually ship.')
content = content.replace('Bublee SDK es un framework moderno para construir, orquestar y desplegar aplicaciones de IA con código mínimo.', 'Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.')
content = content.replace('Crea agentes inteligentes, conecta herramientas, gestiona memoria y escala desde prototipos a producción — todo a través de una experiencia de desarrollo limpia y fluida.', 'Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.')
content = content.replace('Diseñado para fundadores, desarrolladores y equipos creando la próxima generación de productos de IA.', 'Designed for founders, developers, and teams building the next generation of AI products.')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
