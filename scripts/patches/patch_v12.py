with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Remove canvas and noise
import re
content = re.sub(r'<!-- FLUID BACKGROUND -->.*?<div class="noise-overlay"></div>', '<!-- BACKGROUND IMAGE -->\n    <div class="bg-image"></div>\n    <div class="bg-overlay"></div>', content, flags=re.DOTALL)

# Remove the javascript for canvas
content = re.sub(r'const canvas = document.getElementById\(\'fluid-canvas\'\);.*?animate\(\);', '', content, flags=re.DOTALL)

# Add CSS for bg-image
old_canvas_css = """        /* --- FLUID CANVAS BACKGROUND --- */
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
        }"""

new_bg_css = """        /* --- STATIC BACKGROUND IMAGE --- */
        .bg-image {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url('/brand-assets/Bkbublee.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: -2;
        }
        
        .bg-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            /* Optional: a subtle dark gradient overlay to ensure text readability */
            background: linear-gradient(to right, rgba(5,5,10,0.8) 0%, rgba(5,5,10,0.3) 100%);
            pointer-events: none;
        }"""

content = content.replace(old_canvas_css, new_bg_css)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

