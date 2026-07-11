import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Update the SDK Section Layout
old_sdk = """    <!-- SDK SECTION -->
    <section id="sdk" style="position:relative; z-index: 10; min-height: 100vh; display: flex; align-items: center; padding: 120px 6vw; background-color: #05050A;">
        <div class="sdk-content" style="max-width: 800px; width: 100%; text-align: left;">
            <div class="eyebrow-badge" style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 32px; border: 1px solid rgba(124, 58, 237, 0.4); color: #E9D5FF; background: rgba(124, 58, 237, 0.1); padding: 8px 20px; border-radius: 100px; font-weight: 500; font-size: 14px; letter-spacing: 0.02em;">
                <i data-lucide="terminal" size="16"></i> Introducing Bublee SDK
            </div>
            <h2 style="font-family: var(--font-head); font-size: clamp(40px, 6vw, 72px); margin-bottom: 40px; text-shadow: 0 4px 20px rgba(0,0,0,0.5); letter-spacing: -0.03em; line-height: 1.05; font-weight: 800; color: white;">
                Build AI agents that actually ship.
            </h2>
            <p style="font-size: 24px; color: rgba(255,255,255,0.9); margin-bottom: 32px; line-height: 1.6; font-weight: 400; letter-spacing: -0.01em;">
                Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.
            </p>
            <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 40px; line-height: 1.7; font-weight: 400;">
                Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.
            </p>
            <p style="font-size: 14px; color: var(--text-muted); line-height: 1.6; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                Designed for founders, developers, and teams building the next generation of AI products.
            </p>
        </div>
    </section>"""

new_sdk = """    <!-- SDK SECTION -->
    <section id="sdk" style="position:relative; z-index: 10; min-height: 100vh; display: flex; align-items: center; padding: 120px 6vw; background-color: rgba(5, 5, 10, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);">
        <div class="sdk-content" style="max-width: 800px; width: 100%; text-align: left;">
            <h2 style="font-family: var(--font-head); font-size: clamp(40px, 6vw, 72px); margin-bottom: 16px; text-shadow: 0 4px 20px rgba(0,0,0,0.5); letter-spacing: -0.03em; line-height: 1.05; font-weight: 800; color: white;">
                Introducing Bublee SDK
            </h2>
            <h3 style="font-size: clamp(24px, 3vw, 32px); color: var(--text-secondary); margin-bottom: 40px; font-weight: 500; letter-spacing: -0.01em; font-family: var(--font-head);">
                Build AI agents that actually ship.
            </h3>
            <p style="font-size: 20px; color: rgba(255,255,255,0.9); margin-bottom: 32px; line-height: 1.6; font-weight: 400;">
                Bublee SDK is a modern framework for building, orchestrating, and deploying AI-powered applications with minimal code.
            </p>
            <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 40px; line-height: 1.7; font-weight: 400;">
                Create intelligent agents, connect tools, manage memory, execute workflows, and scale from prototype to production — all through a clean developer-first experience.
            </p>
            <p style="font-size: 14px; color: var(--text-muted); line-height: 1.6; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                Designed for founders, developers, and teams building the next generation of AI products.
            </p>
        </div>
    </section>"""

content = content.replace(old_sdk, new_sdk)

# 2. Update Mouse Glow to be very subtle ("no notoria")
old_glow = """        .mouse-glow {
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
        }"""
new_glow = """        .mouse-glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.05) 0%, rgba(0,0,0,0) 60%);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 5;
            mix-blend-mode: screen;
            opacity: 0;
            transition: opacity 0.5s ease;
        }"""
content = content.replace(old_glow, new_glow)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

