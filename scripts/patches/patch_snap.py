import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Add scroll-snap-type to html/body
old_body = """        body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }"""
new_body = """        html {
            scroll-snap-type: y mandatory;
            scroll-behavior: smooth;
        }
        
        body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
        }"""
content = content.replace(old_body, new_body)

# 2. Make .hero and #sdk 100vh and scroll-snap-align: start
old_hero = """        /* --- HERO SECTION --- */
        .hero {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 0 6vw;
            padding-top: 100px;
        }"""
new_hero = """        /* --- HERO SECTION --- */
        .hero {
            position: relative;
            z-index: 10;
            height: 100vh; /* Fixed height for snap */
            display: flex;
            align-items: center;
            padding: 0 6vw;
            padding-top: 100px;
            scroll-snap-align: start;
            scroll-snap-stop: always;
        }"""
content = content.replace(old_hero, new_hero)

# 3. Make #sdk section 100vh and snap
old_sdk = """    <section id="sdk" class="section container" style="position:relative; z-index: 10; padding-top: 60px;">
        <div class="sdk-content glass-panel reveal-up" style="max-width: 1000px; margin: 0 auto; padding: 80px 60px; text-align: center; background: rgba(5,5,10,0.4); border: 1px solid rgba(124, 58, 237, 0.2); box-shadow: 0 20px 80px rgba(0,0,0,0.5), inset 0 0 40px rgba(124, 58, 237, 0.05);">"""
new_sdk = """    <section id="sdk" style="position:relative; z-index: 10; height: 100vh; display: flex; align-items: center; justify-content: center; scroll-snap-align: start; scroll-snap-stop: always; padding-top: 80px;">
        <div class="sdk-content glass-panel reveal-up container" style="max-width: 1000px; width: 90vw; margin: 0 auto; padding: 80px 60px; text-align: center; background: rgba(5,5,10,0.4); border: 1px solid rgba(124, 58, 237, 0.2); box-shadow: 0 20px 80px rgba(0,0,0,0.5), inset 0 0 40px rgba(124, 58, 237, 0.05);">"""
content = content.replace(old_sdk, new_sdk)

# Hide the rest of the old page content temporarily or make them snap too.
# Let's just make the old sections snap so they don't break the flow.
content = content.replace('.section {', '.section {\n            scroll-snap-align: start;\n            min-height: 100vh;\n            display: flex;\n            flex-direction: column;\n            justify-content: center;')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
