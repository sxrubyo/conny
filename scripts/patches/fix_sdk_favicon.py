import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Favicon
favicon_html = """    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/brand-assets/Logo_Bublee_Petalo_Claro.png">"""
content = content.replace("    <title>Bublee AI | One Agent. Infinite Clients.</title>", "    <title>Bublee AI | One Agent. Infinite Clients.</title>\n" + favicon_html)


# 2. Add SDK Section after the hero section
new_section = """
    <!-- SDK SECTION -->
    <section id="sdk" style="position:relative; z-index: 10; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 80px 6vw;">
        <div class="sdk-content" style="max-width: 1000px; width: 100%; margin: 0 auto; padding: 80px 60px; text-align: center; background: rgba(5,5,10,0.5); backdrop-filter: blur(24px); border: 1px solid rgba(124, 58, 237, 0.2); border-radius: 32px; box-shadow: 0 30px 80px rgba(0,0,0,0.6), inset 0 0 40px rgba(124, 58, 237, 0.08);">
            <div class="eyebrow-badge" style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 32px; border: 1px solid rgba(124, 58, 237, 0.4); color: #E9D5FF; background: rgba(124, 58, 237, 0.1); padding: 8px 20px; border-radius: 100px; font-weight: 500; font-size: 15px;">
                <i data-lucide="terminal" size="16"></i> Introducing Bublee SDK
            </div>
            <h2 style="font-family: var(--font-head); font-size: clamp(36px, 5vw, 64px); margin-bottom: 40px; text-shadow: 0 4px 20px rgba(0,0,0,0.5); letter-spacing: -0.02em; line-height: 1.1; font-weight: 700;">
                Build AI agents that actually ship.
            </h2>
            <p style="font-size: 24px; color: #FFFFFF; margin-bottom: 32px; line-height: 1.6; font-weight: 500;">
                Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.
            </p>
            <p style="font-size: 20px; color: var(--text-secondary); margin-bottom: 40px; line-height: 1.7; max-width: 800px; margin-left: auto; margin-right: auto;">
                Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.
            </p>
            <p style="font-size: 15px; color: var(--text-muted); line-height: 1.6; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">
                Designed for founders, developers, and teams building the next generation of AI products.
            </p>
        </div>
    </section>
"""

# The hero section ends with:
#             </div>
#         </div>
#     </section>
# We will replace that ending to inject the new section
content = content.replace("""            </div>
        </div>
    </section>""", """            </div>
        </div>
    </section>""" + new_section)

# 3. Add Mouse Glow logic
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
content = content.replace("        lucide.createIcons();", "        lucide.createIcons();\n" + js_glow)


with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

