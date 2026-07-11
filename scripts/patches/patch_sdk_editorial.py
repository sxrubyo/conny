import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

old_sdk = """    <!-- SDK SECTION -->
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
    </section>"""

new_sdk = """    <!-- SDK SECTION -->
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

content = content.replace(old_sdk, new_sdk)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
