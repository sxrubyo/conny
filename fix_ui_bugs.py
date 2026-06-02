import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Fix the inline display styles that break the tab system!
html = html.replace(
    '<section id="view-calendar" class="tab-view" style="display: flex; flex-direction: column; height: 100vh; padding: 0;">',
    '<section id="view-calendar" class="tab-view" style="padding: 0;">\n<div style="display: flex; flex-direction: column; height: 100vh; width: 100%;">'
)

# We have to close the div for view-calendar
html = re.sub(
    r'(<div id="calendar-grid-content".*?</div>\s*</div>\s*)</section>',
    r'\1</div>\n</section>',
    html, flags=re.DOTALL
)

html = html.replace(
    '<section id="view-library" class="tab-view" style="display: flex; flex-direction: column; height: 100vh; padding: 0;">',
    '<section id="view-library" class="tab-view" style="padding: 0;">\n<div style="display: flex; flex-direction: column; height: 100vh; width: 100%;">'
)

# We have to close the div for view-library
html = re.sub(
    r'(<div id="library-empty-state".*?</div>\s*</div>\s*)</section>',
    r'\1</div>\n</section>',
    html, flags=re.DOTALL
)

# Fix Calendar Buttons ("Mes Anterior" -> "<")
html = html.replace(
    '<button id="calendar-prev-btn" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">&lt; Mes Anterior</button>',
    '<button id="calendar-prev-btn" title="Mes Anterior" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 50%; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: background 0.2s;">&lt;</button>'
)
html = html.replace(
    '<button id="calendar-next-btn" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">Mes Siguiente &gt;</button>',
    '<button id="calendar-next-btn" title="Mes Siguiente" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 50%; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: background 0.2s;">&gt;</button>'
)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
