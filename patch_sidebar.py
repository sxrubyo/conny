import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

dev_nav = """
            <nav class="sidebar-nav" id="dev-sidebar-nav" style="display: none;">
                <button class="nav-item active" data-view="dev-instances" title="Instancias PM2">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line>
                    </svg>
                    <span class="nav-text">Instancias</span>
                </button>
                <button class="nav-item" data-view="dev-prompts" title="Editor de Prompts">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span class="nav-text">Prompts</span>
                </button>
                <button class="nav-item" data-view="dev-models" title="Modelos LLM">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    <span class="nav-text">LLMs</span>
                </button>
                <button class="nav-item" data-view="dev-tokens" title="Tokens y Admins">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    <span class="nav-text">Accesos</span>
                </button>
                <button class="nav-item" data-view="dev-logs" title="Terminal Logs">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line>
                    </svg>
                    <span class="nav-text">Terminal</span>
                </button>
            </nav>
"""

# Insert dev nav after normal nav
idx = html.find('</nav>')
if idx != -1:
    idx += 6
    html = html[:idx] + dev_nav + html[idx:]

# Give normal nav an ID so we can toggle it
html = html.replace('<nav class="sidebar-nav">', '<nav class="sidebar-nav" id="client-sidebar-nav">')

# Hide the settings footer for devs (or we can keep it, but dev settings might be different)
# We will do that in JS.

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
