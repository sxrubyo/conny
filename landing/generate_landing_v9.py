import os

html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bublee AI | La Nueva Era De Agentes</title>
    
    <!-- GSAP for Premium Animations -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>

    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>

    <style>
        /* DESIGN SYSTEM - Professional Dark/White Aesthetic */
        :root {
            --bg-void: #000000; 
            --bg-surface: rgba(10, 10, 15, 0.45); 
            --bg-elevated: rgba(20, 20, 25, 0.6);
            --bg-code: rgba(0, 0, 0, 0.5);
            --border: rgba(255, 255, 255, 0.15);
            --border-hover: rgba(255, 255, 255, 0.3);
            
            --accent-primary: #FFFFFF;
            --accent-secondary: #E2E8F0;
            --accent-money: #4ADE80;
            
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            
            --gradient-hero: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
            
            --text-hero: clamp(56px, 8vw, 110px);
            --text-h2: clamp(40px, 5vw, 64px);
            
            --font-head: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            --font-body: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
            --font-code: 'Fira Code', 'Menlo', monospace;
            
            --nav-bg: rgba(0, 0, 0, 0.4);
            --shadow-text: 0 4px 32px rgba(0,0,0,0.6);
        }

        /* Reset & Base */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }

        /* Static Background Image */
        .bg-image {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url('/brand-assets/Background-bublee.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: -2;
            /* No animation to keep it professional and static */
        }
        
        .bg-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.3); /* Subtle darkening for perfect text contrast */
            z-index: -1;
            pointer-events: none;
        }

        h1, h2, h3, h4 {
            font-family: var(--font-head);
            line-height: 1.05;
            color: var(--text-primary);
            letter-spacing: -0.03em;
            font-weight: 700;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* Layout Utils */
        .container {
            width: 100%;
            max-width: 1440px;
            margin: 0 auto;
            padding: 0 5vw;
        }
        
        .nav-container {
            width: 100%;
            max-width: 1800px;
            margin: 0 auto;
            padding: 0 4vw;
        }
        
        .section {
            padding: 160px 0;
            position: relative;
        }

        .text-gradient {
            background: var(--gradient-hero);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Shadcn-style Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px 32px;
            border-radius: 100px;
            font-family: var(--font-body);
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            gap: 12px;
            letter-spacing: -0.01em;
        }

        .btn-primary {
            background: var(--text-primary);
            color: var(--bg-void);
            box-shadow: 0 4px 24px rgba(255, 255, 255, 0.2);
            border: 1px solid transparent;
        }

        .btn-primary:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 32px rgba(255, 255, 255, 0.3);
            background: #F8FAFC;
        }

        .btn-ghost {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            border: 1px solid var(--border);
            backdrop-filter: blur(8px);
        }
        
        .btn-ghost:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--border-hover);
        }

        /* Navbar */
        nav {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 100;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            background: var(--nav-bg);
        }

        .nav-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 80px;
        }

        .logo {
            display: flex;
            align-items: center;
            font-family: var(--font-head);
            font-weight: 700;
            font-size: 24px;
            letter-spacing: -0.04em;
        }

        .logo-mark {
            height: 32px;
            object-fit: contain;
            margin-right: 12px;
            filter: invert(1);
        }

        .nav-links {
            display: flex;
            gap: 40px;
        }

        .nav-links a {
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            transition: color 0.2s;
            letter-spacing: -0.01em;
        }

        .nav-links a:hover {
            color: var(--text-primary);
        }

        /* Hero */
        .hero {
            padding-top: 260px;
            padding-bottom: 120px;
            text-align: left;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        .hero h1 {
            font-size: var(--text-hero);
            margin-bottom: 32px;
            text-shadow: var(--shadow-text);
            max-width: 1200px;
            line-height: 0.95;
        }

        .hero p.subhead {
            font-size: 24px;
            line-height: 1.5;
            color: var(--text-secondary);
            margin-bottom: 64px;
            max-width: 700px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
            font-weight: 400;
            letter-spacing: -0.01em;
        }

        .hero-ctas {
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        /* Cards & Surfaces (Shadcn-style Glass) */
        .glass-panel {
            background: var(--bg-surface);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 24px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-top: 80px;
            width: 100%;
        }

        .stat-card {
            padding: 40px;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-hover);
        }

        .stat-value {
            font-size: 56px;
            font-family: var(--font-head);
            font-weight: 700;
            letter-spacing: -0.04em;
            margin-bottom: 8px;
            color: var(--text-primary);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 16px;
            font-weight: 500;
        }

        /* Features (Benefits) */
        .section-title {
            font-size: var(--text-h2);
            margin-bottom: 80px;
            max-width: 800px;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 32px;
        }

        .feature-card {
            padding: 48px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            transition: border-color 0.3s ease, background 0.3s ease;
        }

        .feature-card:hover {
            border-color: var(--border-hover);
            background: rgba(255,255,255,0.03);
        }

        .feature-icon {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            background: rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-primary);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .feature-card h3 {
            font-size: 28px;
        }

        .feature-card p {
            color: var(--text-secondary);
            font-size: 18px;
            line-height: 1.6;
        }

        /* Footer */
        footer {
            padding: 100px 0 60px;
            border-top: 1px solid var(--border);
            background: var(--bg-void); /* Solid base for footer */
        }

        .footer-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 64px;
            margin-bottom: 80px;
        }

        .footer-col h4 {
            font-size: 16px;
            color: var(--text-primary);
            margin-bottom: 24px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .footer-col a {
            display: block;
            color: var(--text-secondary);
            margin-bottom: 16px;
            font-size: 15px;
            transition: color 0.2s;
        }

        .footer-col a:hover {
            color: var(--text-primary);
        }

        .footer-bottom {
            padding-top: 40px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 14px;
        }

        /* Animations */
        .reveal-up {
            opacity: 0;
            transform: translateY(40px);
        }

        /* Responsive */
        @media (max-width: 992px) {
            .stats-grid { grid-template-columns: 1fr; }
            .features-grid { grid-template-columns: 1fr; }
            .footer-grid { grid-template-columns: 1fr; gap: 40px; }
            .hero { padding-top: 180px; }
        }
        
        @media (max-width: 768px) {
            .nav-links { display: none; }
            .hero-ctas { flex-direction: column; align-items: stretch; }
            .btn { width: 100%; }
        }
    </style>
</head>
<body>

    <!-- Static Background Image -->
    <div class="bg-image"></div>
    <div class="bg-overlay"></div>

    <nav>
        <div class="nav-container nav-inner">
            <a href="#" class="logo">
                <img src="/isotype" alt="Bublee" class="logo-mark" onerror="this.style.display='none'">
                BUBLEE
            </a>
            
            <div class="nav-links">
                <a href="#soluciones">Soluciones</a>
                <a href="#arquitectura">Arquitectura</a>
                <a href="#precios">Precios</a>
            </div>

            <div style="display: flex; gap: 16px;">
                <a href="/app" class="btn btn-ghost" style="padding: 10px 20px; font-size: 14px;">Iniciar Sesión</a>
            </div>
        </div>
    </nav>

    <header class="hero container">
        <h1>
            <span class="text-gradient">La Nueva Era De Agentes</span>
        </h1>
        <p class="subhead">Despliega agentes de IA ilimitados para tus clientes. Estética refinada. Conversión asegurada. Diseño memorable y arquitectónicamente superior.</p>
        
        <div class="hero-ctas">
            <a href="#comenzar" class="btn btn-primary">
                Comenzar Ahora <i data-lucide="arrow-right" size="18"></i>
            </a>
            <a href="#arquitectura" class="btn btn-ghost">
                Explorar Arquitectura
            </a>
        </div>

        <div class="stats-grid">
            <div class="stat-card glass-panel reveal-up">
                <div class="stat-value">95%</div>
                <div class="stat-label">Margen de Ganancia Promedio</div>
            </div>
            <div class="stat-card glass-panel reveal-up">
                <div class="stat-value">∞</div>
                <div class="stat-label">Instancias Ilimitadas</div>
            </div>
            <div class="stat-card glass-panel reveal-up">
                <div class="stat-value">$6</div>
                <div class="stat-label">Costo Mensual Base (VPS)</div>
            </div>
        </div>
    </header>

    <section id="soluciones" class="section container">
        <h2 class="section-title reveal-up">Diseñado para la supremacía operativa de tu agencia.</h2>
        
        <div class="features-grid">
            <div class="feature-card glass-panel reveal-up">
                <div class="feature-icon"><i data-lucide="zap" size="24"></i></div>
                <h3>Despliegue Instantáneo</h3>
                <p>Clona y despliega agentes completamente aislados para docenas de clientes en segundos usando un solo núcleo centralizado.</p>
            </div>
            <div class="feature-card glass-panel reveal-up">
                <div class="feature-icon"><i data-lucide="shield" size="24"></i></div>
                <h3>Privacidad Absoluta</h3>
                <p>Cero cruce de datos. Cada instancia opera en su propio contenedor seguro garantizando la confidencialidad de tus clientes.</p>
            </div>
            <div class="feature-card glass-panel reveal-up">
                <div class="feature-icon"><i data-lucide="refresh-cw" size="24"></i></div>
                <h3>Sincronización Global</h3>
                <p>Actualiza la lógica central una vez y propaga las mejoras a toda tu cartera de clientes con un solo comando de terminal.</p>
            </div>
            <div class="feature-card glass-panel reveal-up">
                <div class="feature-icon"><i data-lucide="bar-chart-2" size="24"></i></div>
                <h3>Métricas en Tiempo Real</h3>
                <p>Monitorea conversaciones, tasas de conversión y uso de API desde un dashboard central unificado y minimalista.</p>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <a href="#" class="logo" style="margin-bottom: 24px;">
                        BUBLEE
                    </a>
                    <p style="color: var(--text-secondary); font-size: 15px; max-width: 300px;">
                        La infraestructura definitiva para agencias que construyen el futuro con IA.
                    </p>
                </div>
                <div class="footer-col">
                    <h4>Plataforma</h4>
                    <a href="#">Características</a>
                    <a href="#">Precios</a>
                    <a href="#">Documentación</a>
                </div>
                <div class="footer-col">
                    <h4>Empresa</h4>
                    <a href="#">Acerca de</a>
                    <a href="#">Contacto</a>
                    <a href="#">Privacidad</a>
                </div>
            </div>
            <div class="footer-bottom">
                <span>&copy; 2026 Bublee AI. Todos los derechos reservados.</span>
                <span>Open Source &middot; MIT License</span>
            </div>
        </div>
    </footer>

    <script>
        // Init Icons
        lucide.createIcons();

        // GSAP Scroll Animations
        gsap.registerPlugin(ScrollTrigger);

        // Hero staggered entrance
        const tl = gsap.timeline();
        tl.from(".hero h1", { y: 40, opacity: 0, duration: 1.2, ease: "power4.out" })
          .from(".hero p.subhead", { y: 20, opacity: 0, duration: 1, ease: "power3.out" }, "-=0.8")
          .from(".hero-ctas", { y: 20, opacity: 0, duration: 1, ease: "power3.out" }, "-=0.8");

        // Scroll reveals
        gsap.utils.toArray('.reveal-up').forEach((el, i) => {
            gsap.to(el, {
                scrollTrigger: {
                    trigger: el,
                    start: "top 85%",
                },
                y: 0,
                opacity: 1,
                duration: 0.8,
                ease: "power3.out",
                delay: el.classList.contains('stat-card') ? i * 0.1 : 0
            });
        });
    </script>
</body>
</html>"""

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(html_content)
