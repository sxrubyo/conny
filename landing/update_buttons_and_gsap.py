import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    html = f.read()

# 1. Remove the Open Source Badge
badge_regex = r'<div class="hero-badge">.*?</div>'
html = re.sub(badge_regex, '', html, flags=re.DOTALL)

# 2. Add "Get Started" next to "Sign In" in the Navbar
nav_right_old = """<div class="nav-right">
                <button id="theme-toggle" class="theme-toggle-btn" aria-label="Toggle theme">
                    <i data-lucide="moon" size="20"></i>
                </button>
                <a href="/app" class="btn btn-primary">Sign In</a>
            </div>"""

nav_right_new = """<div class="nav-right">
                <button id="theme-toggle" class="theme-toggle-btn" aria-label="Toggle theme">
                    <i data-lucide="moon" size="20"></i>
                </button>
                <a href="/app" class="btn btn-ghost" style="padding: 10px 16px;">Sign In</a>
                <a href="#how-it-works" class="btn btn-primary">Get Started</a>
            </div>"""
html = html.replace(nav_right_old, nav_right_new)

# 3. Add GSAP & ScrollTrigger to <head>
gsap_scripts = """
    <!-- GSAP for Premium Animations -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
"""
if "gsap.min.js" not in html:
    html = html.replace('<!-- Lucide Icons -->', gsap_scripts + '\n    <!-- Lucide Icons -->')

# 4. Replace simple IntersectionObserver with GSAP logic in <script>
gsap_logic = """
        // GSAP Animations
        gsap.registerPlugin(ScrollTrigger);

        // Hero Animation
        const tl = gsap.timeline();
        tl.from(".hero h1", { y: 40, opacity: 0, duration: 1, ease: "power4.out", delay: 0.2 })
          .from(".hero p.subhead", { y: 20, opacity: 0, duration: 0.8, ease: "power3.out" }, "-=0.6")
          .from(".hero-ctas", { y: 20, opacity: 0, duration: 0.8, ease: "power3.out" }, "-=0.6");

        // Staggered Industry Cards
        gsap.from(".industry-card", {
            scrollTrigger: {
                trigger: ".industries-grid",
                start: "top 80%",
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: "back.out(1.2)"
        });

        // Architecture Spokes Animation
        gsap.from(".spoke", {
            scrollTrigger: {
                trigger: ".arch-container",
                start: "top 70%",
            },
            scale: 0.8,
            y: 30,
            opacity: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: "elastic.out(1, 0.8)"
        });
        
        // Lines animation
        gsap.to(".arch-line", {
            scrollTrigger: {
                trigger: ".arch-container",
                start: "top 70%",
            },
            strokeDashoffset: 0,
            stroke: "var(--accent-primary)",
            duration: 1.5,
            stagger: 0.2,
            ease: "power2.inOut"
        });

        // Competitive Table Fade In
        gsap.from("#compare tr", {
            scrollTrigger: {
                trigger: ".table-wrapper",
                start: "top 80%",
            },
            x: -20,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: "power2.out"
        });
"""

if "gsap.registerPlugin" not in html:
    # Insert before the IntersectionObserver or replace it
    html = html.replace('// Intersection Observer', gsap_logic + '\n        // Intersection Observer')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(html)
