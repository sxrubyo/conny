with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Make default theme dark instead of light
old_logic = """const currentTheme = localStorage.getItem('bublee_theme');
if (currentTheme === 'dark') {
    document.body.classList.add('dark-theme');
    if (themeToggle) themeToggle.checked = true;
} else {
    document.body.classList.remove('dark-theme');
}"""

new_logic = """const currentTheme = localStorage.getItem('bublee_theme') || 'dark'; // Default to dark theme
if (currentTheme === 'dark') {
    document.body.classList.add('dark-theme');
    if (themeToggle) themeToggle.checked = true;
} else {
    document.body.classList.remove('dark-theme');
}"""

js = js.replace(old_logic, new_logic)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
