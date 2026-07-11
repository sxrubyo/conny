import os

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bublee AI | One Agent. Infinite Clients.</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
    
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>

    <style>
        /* DESIGN SYSTEM - Premium Dark SaaS / Fluid Aesthetic */
        :root {
            --bg-base: #05050A; /* Deep dark background */
            --nav-bg: rgba(5, 5, 10, 0.5);
            
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            
            --accent-violet: #7C3AED;
            --accent-magenta: #C026D3;
            --accent-amber: #F59E0B;
            --accent-blue: #3B82F6;
            
            --font-head: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-body);
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }

        /* --- FLUID CANVAS BACKGROUND --- */
        .canvas-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            overflow: hidden;
            background-color: var(--bg-base);
            /* Soften the whole thing */
            filter: blur(120px) saturate(1.5);
            -webkit-filter: blur(120px) saturate(1.5);
            transform: translateZ(0); /* Hardware acceleration */
        }

        canvas {
            width: 100%;
            height: 100%;
            display: block;
        }
        
        /* Subtle noise overlay to make it look expensive */
        .noise-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: none;
            opacity: 0.04;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }

        /* --- NAVBAR --- */
        nav {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 100;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            background: var(--nav-bg);
            padding: 0 4vw;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-logo {
            display: flex;
            align-items: center;
            font-family: var(--font-head);
            font-weight: 800;
            font-size: 22px;
            letter-spacing: -0.02em;
            color: white;
            text-decoration: none;
        }

        .violet-dot {
            width: 10px;
            height: 10px;
            background-color: var(--accent-violet);
            border-radius: 50%;
            margin-right: 8px;
            box-shadow: 0 0 12px var(--accent-violet);
        }

        .nav-links {
            display: flex;
            gap: 40px;
        }

        .nav-links a {
            color: var(--text-secondary);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
            text-decoration: none;
            transition: color 0.2s;
        }

        .nav-links a:hover {
            color: white;
        }

        .btn-nav-cta {
            background-color: var(--accent-amber);
            color: #000;
            font-weight: 600;
            font-size: 14px;
            padding: 10px 24px;
            border-radius: 100px;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-nav-cta:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5);
        }

        /* --- HERO SECTION --- */
        .hero {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 0 6vw;
            padding-top: 80px; /* Offset for nav */
        }

        .hero-content {
            max-width: 800px;
        }

        .eyebrow-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 32px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .hero h1 {
            font-family: var(--font-head);
            font-size: clamp(64px, 8vw, 120px);
            line-height: 1.05;
            letter-spacing: -0.04em;
            margin-bottom: 32px;
            color: white;
            text-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .hero-subline {
            font-size: clamp(18px, 2vw, 24px);
            line-height: 1.6;
            color: var(--text-secondary);
            margin-bottom: 48px;
            max-width: 600px;
            font-weight: 400;
        }

        .hero-ctas {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 16px 36px;
            border-radius: 100px;
            font-weight: 600;
            font-size: 16px;
            text-decoration: none;
            transition: all 0.3s ease;
            gap: 10px;
        }

        .btn-primary {
            background: #FFFFFF;
            color: #05050A;
            box-shadow: 0 4px 20px rgba(255,255,255,0.15);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(255,255,255,0.3);
        }

        .btn-ghost {
            background: transparent;
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .btn-ghost:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.4);
        }

        /* --- RESPONSIVE --- */
        @media (max-width: 900px) {
            .nav-links { display: none; }
        }
        
        @media (max-width: 600px) {
            .hero-ctas { flex-direction: column; align-items: flex-start; }
            .btn { width: 100%; }
        }

        /* Entrance Animations */
        .fade-up {
            animation: fadeUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(30px);
        }
        
        @keyframes fadeUp {
            to { opacity: 1; transform: translateY(0); }
        }
        
        .d-1 { animation-delay: 0.1s; }
        .d-2 { animation-delay: 0.3s; }
        .d-3 { animation-delay: 0.5s; }
        .d-4 { animation-delay: 0.7s; }

    </style>
</head>
<body>

    <!-- FLUID BACKGROUND -->
    <div class="canvas-container">
        <canvas id="fluid-canvas"></canvas>
    </div>
    <div class="noise-overlay"></div>

    <!-- NAVBAR -->
    <nav>
        <a href="#" class="nav-logo">
            <span class="violet-dot"></span> Bublee
        </a>
        <div class="nav-links">
            <a href="#">Features</a>
            <a href="#">How it works</a>
            <a href="#">Pricing</a>
            <a href="#">GitHub</a>
        </div>
        <a href="#" class="btn-nav-cta">Get Template &rarr;</a>
    </nav>

    <!-- HERO SECTION -->
    <section class="hero">
        <div class="hero-content">
            <div class="eyebrow-badge fade-up d-1">
                ✦ Open Source AI Receptionist
            </div>
            
            <h1 class="fade-up d-2">
                One Agent.<br>
                Infinite Clients.
            </h1>
            
            <p class="hero-subline fade-up d-3">
                Deploy unlimited AI receptionists for your agency.<br>
                85% margins. Zero vendor lock-in.
            </p>
            
            <div class="hero-ctas fade-up d-4">
                <a href="#" class="btn btn-primary">
                    Get Started Free &rarr;
                </a>
                <a href="#" class="btn btn-ghost">
                    See how it works
                </a>
            </div>
        </div>
    </section>

    <!-- FLUID CANVAS SCRIPT -->
    <script>
        lucide.createIcons();

        const canvas = document.getElementById('fluid-canvas');
        const ctx = canvas.getContext('2d');

        let width, height;
        
        function resize() {
            width = window.innerWidth;
            height = window.innerHeight;
            canvas.width = width;
            canvas.height = height;
        }
        
        window.addEventListener('resize', resize);
        resize();

        // Blob definition
        class Blob {
            constructor(x, y, radius, color, speedX, speedY) {
                this.x = x;
                this.y = y;
                this.baseRadius = radius;
                this.radius = radius;
                this.color = color;
                this.speedX = speedX;
                this.speedY = speedY;
                this.angle = Math.random() * Math.PI * 2;
                this.angleSpeed = (Math.random() - 0.5) * 0.02;
            }

            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                
                // Slowly morph size
                this.angle += this.angleSpeed;
                this.radius = this.baseRadius + Math.sin(this.angle) * (this.baseRadius * 0.2);

                // Bounce off soft edges (allow them to go slightly off screen)
                const margin = this.radius;
                if (this.x < -margin || this.x > width + margin) this.speedX *= -1;
                if (this.y < -margin || this.y > height + margin) this.speedY *= -1;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
            }
        }

        // Colors requested: deep violet #7C3AED, magenta #C026D3, warm amber #F59E0B, electric blue #3B82F6
        const blobs = [
            // Right side bias for the background (as requested: "text left, visual right")
            new Blob(width * 0.8, height * 0.3, width * 0.35, '#7C3AED', 0.5, 0.4),  // Violet
            new Blob(width * 0.6, height * 0.7, width * 0.4, '#C026D3', -0.4, 0.6), // Magenta
            new Blob(width * 0.9, height * 0.8, width * 0.25, '#F59E0B', 0.6, -0.3), // Amber
            new Blob(width * 0.4, height * 0.2, width * 0.3, '#3B82F6', -0.3, 0.5),  // Blue
            new Blob(width * 0.7, height * 0.5, width * 0.4, '#7C3AED', 0.2, -0.4)   // Extra Violet
        ];

        function animate() {
            // Clear with dark transparent background for slight trail effect
            ctx.fillStyle = 'rgba(5, 5, 10, 1)';
            ctx.fillRect(0, 0, width, height);

            blobs.forEach(blob => {
                blob.update();
                blob.draw();
            });

            requestAnimationFrame(animate);
        }

        animate();
    </script>
</body>
</html>"""

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(html_content)
