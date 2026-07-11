import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Enhance the responsive CSS
old_responsive = """        /* --- RESPONSIVE --- */
        @media (max-width: 900px) {
            .nav-links { display: none; }
        }
        
        @media (max-width: 600px) {
            .hero-ctas { flex-direction: column; align-items: flex-start; }
            .btn { width: 100%; }
        }"""

new_responsive = """        /* --- RESPONSIVE --- */
        @media (max-width: 900px) {
            .nav-links { display: none; }
        }
        
        @media (max-width: 600px) {
            nav { height: 80px; padding: 0 20px; }
            .nav-logo { font-size: 18px; }
            .logo-mark { height: 36px; }
            
            .nav-right .btn-nav-white { display: none; }
            .nav-right .btn-nav-cta { padding: 8px 16px; font-size: 13px; }
            
            .hero { padding-top: 80px; padding-left: 20px; padding-right: 20px; }
            .hero-content { margin-top: 0 !important; }
            
            .hero h1 { font-size: 42px !important; line-height: 1.1; margin-bottom: 24px; }
            .hero-subline { font-size: 16px !important; margin-bottom: 32px; }
            
            .hero-ctas { flex-direction: column; align-items: stretch; width: 100%; }
            .btn { width: 100%; padding: 14px 20px; font-size: 15px; }
            
            /* SDK Mobile Tweaks */
            #sdk { padding: 80px 20px !important; }
            #sdk h2 { font-size: 32px !important; margin-bottom: 16px !important; }
            #sdk h3 { font-size: 20px !important; margin-bottom: 24px !important; }
            #sdk p { font-size: 16px !important; margin-bottom: 24px !important; }
        }"""

content = content.replace(old_responsive, new_responsive)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

