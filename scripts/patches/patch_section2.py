import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Add CSS for mouse-glow
css_glow = """        .mouse-glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.12) 0%, rgba(245, 158, 11, 0.05) 40%, rgba(0,0,0,0) 70%);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 5;
            mix-blend-mode: screen;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        body:hover .mouse-glow {
            opacity: 1;
        }"""
content = content.replace("    </style>", css_glow + "\n    </style>")

# 2. Add the section HTML
new_section = """    <section id="sdk" class="section container" style="position:relative; z-index: 10; padding-top: 60px;">
        <div class="sdk-content glass-panel reveal-up" style="max-width: 1000px; margin: 0 auto; padding: 80px 60px; text-align: center; background: rgba(5,5,10,0.4); border: 1px solid rgba(124, 58, 237, 0.2); box-shadow: 0 20px 80px rgba(0,0,0,0.5), inset 0 0 40px rgba(124, 58, 237, 0.05);">
            <div class="eyebrow-badge" style="margin-bottom: 24px; border-color: rgba(124, 58, 237, 0.4); color: #E9D5FF;">
                <i data-lucide="terminal" size="14" style="margin-right: 6px;"></i> Introducing Bublee SDK
            </div>
            <h2 style="font-size: clamp(36px, 5vw, 56px); margin-bottom: 32px; text-shadow: 0 4px 20px rgba(0,0,0,0.5); letter-spacing: -0.02em;">
                Build AI agents that actually ship.
            </h2>
            <p style="font-size: 22px; color: var(--text-primary); margin-bottom: 24px; line-height: 1.6; font-weight: 500;">
                Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.
            </p>
            <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 32px; line-height: 1.7; max-width: 800px; margin-left: auto; margin-right: auto;">
                Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.
            </p>
            <p style="font-size: 15px; color: var(--text-muted); line-height: 1.6; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">
                Designed for founders, developers, and teams building the next generation of AI products.
            </p>
        </div>
    </section>"""
content = content.replace("</header>", "</header>\n\n" + new_section)

# 3. Add the JS for the mouse glow
js_glow = """        // Mouse Glow Effect
        const glow = document.createElement('div');
        glow.className = 'mouse-glow';
        document.body.appendChild(glow);

        window.addEventListener('mousemove', (e) => {
            gsap.to(glow, {
                x: e.clientX,
                y: e.clientY,
                duration: 0.6,
                ease: "power2.out"
            });
        });"""
content = content.replace("        // Hero staggered entrance", js_glow + "\n\n        // Hero staggered entrance")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
