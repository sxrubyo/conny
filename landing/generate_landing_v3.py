import os

html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bublee AI | El Motor de IA para Agencias</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap" rel="stylesheet">
    
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>

    <style>
        /* LIGHT THEME (Default) */
        :root {
            --bg-void: #F8F9FA;
            --bg-surface: #FFFFFF;
            --bg-elevated: #F1F3F5;
            --border: #E5E7EB;
            --border-glow: rgba(147, 51, 234, 0.2);
            --accent-primary: #9333EA;
            --accent-secondary: #25D366;
            --accent-money: #10B981;
            --accent-warm: #F59E0B;
            
            --text-primary: #111827;
            --text-secondary: #4B5563;
            --text-muted: #9CA3AF;
            
            --gradient-hero: linear-gradient(135deg, #9333EA 0%, #25D366 100%);
            --gradient-money: linear-gradient(135deg, #10B981 0%, #059669 100%);
            --gradient-card: linear-gradient(145deg, #FFFFFF 0%, #F8F9FA 100%);
            
            --text-hero: clamp(40px, 5vw, 76px);
            --text-h2: clamp(28px, 3.5vw, 48px);
            
            --font-head: 'Plus Jakarta Sans', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-code: 'Fira Code', monospace;
            
            --nav-bg: rgba(248, 249, 250, 0.85);
            --invert-logo: 0;
        }

        /* DARK THEME (Toggled via class) */
        :root.dark-theme {
            --bg-void: #0A0A0F;
            --bg-surface: #111118;
            --bg-elevated: #1A1A24;
            --border: #2A2A3A;
            --border-glow: rgba(147, 51, 234, 0.4);
            
            --text-primary: #F5F5FF;
            --text-secondary: #9090B0;
            --text-muted: #50506A;
            
            --gradient-card: linear-gradient(145deg, #1A1A24 0%, #111118 100%);
            
            --nav-bg: rgba(10, 10, 15, 0.85);
            --invert-logo: 1;
        }

        /* Reset & Base */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
            scroll-behavior: smooth;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        h1, h2, h3, h4 {
            font-family: var(--font-head);
            line-height: 1.2;
            color: var(--text-primary);
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* Background Effects */
        .bg-mesh {
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 50% 50%, rgba(147, 51, 234, 0.05) 0%, transparent 40%),
                        radial-gradient(circle at 80% 20%, rgba(37, 211, 102, 0.03) 0%, transparent 30%);
            animation: meshMove 20s infinite alternate ease-in-out;
            z-index: -2;
            pointer-events: none;
        }

        .bg-noise {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: -1;
            opacity: 0.02;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }

        /* Layout Utils */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }
        
        .section {
            padding: 120px 0;
            position: relative;
        }

        .text-gradient {
            background: var(--gradient-hero);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .text-money {
            background: var(--gradient-money);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px 28px;
            border-radius: 100px;
            font-family: var(--font-head);
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s ease;
            cursor: pointer;
            gap: 8px;
            border: 1px solid transparent;
        }

        .btn-primary {
            background: var(--accent-primary);
            color: white;
            box-shadow: 0 4px 20px rgba(147, 51, 234, 0.3);
        }

        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 25px rgba(147, 51, 234, 0.5);
        }

        .btn-ghost {
            background: transparent;
            color: var(--text-secondary);
        }
        
        .btn-ghost:hover {
            color: var(--text-primary);
            transform: translateX(4px);
        }

        /* Code/Terminal */
        .code-block {
            font-family: var(--font-code);
            background: #000;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            color: #A6ACCD;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }
        
        .code-block .copy-btn {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        
        .code-block .copy-btn:hover {
            background: var(--border);
        }

        /* Navbar */
        nav {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 100;
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            background: var(--nav-bg);
            animation: slideDown 0.4s forwards;
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .nav-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 80px;
        }

        .logo {
            display: flex;
            align-items: center;
        }

        .logo-mark {
            height: 40px;
            object-fit: contain;
            filter: invert(var(--invert-logo)); /* Ensure visibility on light mode if logo is white */
            transition: filter 0.3s ease;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 32px;
        }

        .nav-links a {
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 15px;
            transition: color 0.2s;
        }

        .nav-links a:hover {
            color: var(--text-primary);
        }
        
        .theme-toggle-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s, transform 0.2s;
            padding: 8px;
            border-radius: 50%;
        }
        
        .theme-toggle-btn:hover {
            color: var(--accent-primary);
            transform: scale(1.1);
        }

        /* Hero */
        .hero {
            padding-top: 200px;
            padding-bottom: 100px;
            text-align: center;
        }

        .hero-center {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            padding: 8px 20px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 32px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
            transition: all 0.3s ease;
        }

        .hero h1 {
            font-size: var(--text-hero);
            letter-spacing: -0.02em;
            line-height: 1.15;
            margin-bottom: 32px;
        }

        .hero p.subhead {
            font-size: 20px;
            line-height: 1.7;
            color: var(--text-secondary);
            margin-bottom: 48px;
            max-width: 800px;
        }

        .hero-ctas {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            margin-bottom: 64px;
            flex-wrap: wrap;
        }

        .stats-strip {
            display: flex;
            gap: 24px;
            justify-content: center;
            color: var(--text-muted);
            font-size: 15px;
            font-weight: 500;
            flex-wrap: wrap;
        }
        
        .stats-strip span {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-surface);
            padding: 10px 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }

        /* Calculator */
        .calculator {
            background: var(--bg-surface);
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            text-align: center;
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .calc-wrapper {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 0;
        }
        
        .calc-wrapper h2 {
            font-size: var(--text-h2);
            margin-bottom: 48px;
        }

        .calc-controls {
            margin-bottom: 64px;
        }
        
        .calc-label {
            display: block;
            font-weight: 600;
            font-size: 18px;
            margin-bottom: 24px;
            color: var(--text-secondary);
        }

        input[type=range] {
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
            margin-bottom: 48px;
        }
        
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 28px;
            width: 28px;
            border-radius: 50%;
            background: var(--accent-primary);
            cursor: pointer;
            margin-top: -12px;
            box-shadow: 0 0 20px rgba(147, 51, 234, 0.4);
            border: 2px solid white;
        }
        
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 6px;
            cursor: pointer;
            background: var(--border);
            border-radius: 3px;
        }

        .price-tiers {
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .price-btn {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 14px 28px;
            border-radius: 12px;
            cursor: pointer;
            font-family: var(--font-head);
            font-weight: 700;
            font-size: 16px;
            transition: all 0.2s;
        }
        
        .price-btn.active {
            background: rgba(147, 51, 234, 0.1);
            border-color: var(--accent-primary);
            color: var(--accent-primary);
        }

        .calc-results {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
        }
        
        .result-card {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px 24px;
            text-align: left;
            transition: transform 0.3s, background 0.3s ease, border-color 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }
        
        .result-card.update {
            animation: flipUpdate 0.4s ease;
        }
        
        .res-label {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 12px;
        }
        
        .res-value {
            font-size: 36px;
            font-weight: 800;
            font-family: var(--font-head);
        }
        
        .res-value.money { color: var(--accent-money); }

        .progress-bar {
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            margin-top: 16px;
            overflow: hidden;
            transition: background 0.3s ease;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--gradient-money);
            width: 90%;
            transition: width 0.3s;
        }

        /* How it Works */
        .section-title {
            text-align: center;
            font-size: var(--text-h2);
            margin-bottom: 80px;
        }

        .steps-container {
            display: flex;
            flex-direction: column;
            gap: 80px;
            position: relative;
        }
        
        .steps-line {
            position: absolute;
            left: 32px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--border);
            z-index: 0;
            transition: background 0.3s ease;
        }
        
        .steps-line-fill {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            background: var(--accent-primary);
            height: 0%;
            transition: height 0.5s ease-out;
        }

        .step {
            display: grid;
            grid-template-columns: 64px 1fr 1fr;
            gap: 48px;
            position: relative;
            z-index: 1;
            align-items: center;
        }

        .step-num {
            width: 64px;
            height: 64px;
            background: var(--bg-elevated);
            border: 2px solid var(--border);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-head);
            font-weight: 800;
            font-size: 24px;
            transition: all 0.3s;
        }
        
        .step.active .step-num {
            border-color: var(--accent-primary);
            color: var(--accent-primary);
            box-shadow: 0 0 20px var(--border-glow);
            background: var(--bg-surface);
        }

        .step-content h3 {
            font-size: 28px;
            margin-bottom: 16px;
        }
        
        .step-content p {
            color: var(--text-secondary);
            font-size: 18px;
            line-height: 1.6;
        }

        .term-window {
            background: #000;
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .term-header {
            background: #1A1A24;
            padding: 12px 20px;
            display: flex;
            gap: 8px;
        }
        
        .term-dot { width: 12px; height: 12px; border-radius: 50%; }
        .term-dot.r { background: #FF5F56; }
        .term-dot.y { background: #FFBD2E; }
        .term-dot.g { background: #27C93F; }
        
        .term-body {
            padding: 24px;
            font-family: var(--font-code);
            font-size: 15px;
            color: #A6ACCD;
            min-height: 120px;
            line-height: 1.6;
        }
        
        .typewriter-text::after {
            content: '█';
            animation: blink 1s step-start infinite;
            color: var(--accent-primary);
        }

        /* Industry Cards */
        .industries-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 32px;
        }

        .industry-card {
            background: var(--gradient-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }
        
        .industry-card:hover {
            transform: translateY(-8px);
            border-color: var(--accent-primary);
            box-shadow: 0 20px 40px rgba(147, 51, 234, 0.08);
        }

        .ind-icon {
            font-size: 40px;
            margin-bottom: 24px;
        }

        .industry-card h3 {
            font-size: 22px;
            margin-bottom: 12px;
        }

        .industry-card p {
            color: var(--text-secondary);
            font-size: 16px;
            margin-bottom: 32px;
        }

        .ind-price {
            display: inline-block;
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-money);
            padding: 6px 16px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 700;
        }

        /* Architecture */
        .arch-container {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 32px;
            padding: 80px 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow: hidden;
            position: relative;
            box-shadow: 0 10px 30px rgba(0,0,0,0.02);
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .hub {
            background: var(--accent-primary);
            color: white;
            padding: 24px 48px;
            border-radius: 100px;
            font-family: var(--font-head);
            font-weight: 800;
            font-size: 22px;
            z-index: 10;
            box-shadow: 0 0 30px rgba(147, 51, 234, 0.3);
            animation: pulse-glow 3s infinite;
        }

        .spokes {
            display: flex;
            justify-content: center;
            gap: 40px;
            width: 100%;
            margin-top: 120px;
            position: relative;
            z-index: 10;
        }
        
        .spoke {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            width: 200px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.02);
            transition: background 0.3s ease, border-color 0.3s ease;
        }
        
        .spoke.dashed {
            border-style: dashed;
            opacity: 0.7;
            background: transparent;
        }
        
        .spoke-icon {
            color: var(--accent-secondary);
            margin-bottom: 12px;
        }

        .spoke-title {
            font-weight: 700;
            margin-bottom: 8px;
            font-size: 16px;
        }
        
        .spoke-meta {
            font-family: var(--font-code);
            font-size: 12px;
            color: var(--text-muted);
        }

        .arch-svg {
            position: absolute;
            top: 130px;
            left: 0;
            width: 100%;
            height: 180px;
            z-index: 1;
        }
        
        .arch-line {
            fill: none;
            stroke: var(--border);
            stroke-width: 3;
            stroke-dasharray: 600;
            stroke-dashoffset: 600;
            transition: stroke-dashoffset 1.5s ease-out, stroke 0.3s ease;
        }
        
        .arch-line.active {
            stroke-dashoffset: 0;
            stroke: var(--accent-primary);
        }

        /* Competitive Table */
        .table-wrapper {
            overflow-x: auto;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.02);
            transition: background 0.3s ease, border-color 0.3s ease;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        
        th, td {
            padding: 24px 32px;
            border-bottom: 1px solid var(--border);
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        th {
            font-family: var(--font-head);
            font-weight: 700;
            color: var(--text-secondary);
            font-size: 15px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: var(--bg-elevated);
            transition: background 0.3s ease;
        }
        
        .col-bublee {
            background: rgba(147, 51, 234, 0.05);
            border-left: 2px solid rgba(147, 51, 234, 0.2);
            border-right: 2px solid rgba(147, 51, 234, 0.2);
        }
        
        th.col-bublee {
            color: var(--accent-primary);
            border-top: 2px solid rgba(147, 51, 234, 0.2);
        }

        tr:last-child td.col-bublee {
            border-bottom: 2px solid rgba(147, 51, 234, 0.2);
        }
        
        tr:last-child td {
            border-bottom: none;
        }

        .icon-check { color: var(--accent-secondary); }
        .icon-x { color: var(--text-muted); }

        /* Quick Start */
        .qs-term {
            max-width: 900px;
            margin: 48px auto 0;
            text-align: left;
            font-size: 16px;
        }

        /* Open Source */
        .os-section {
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            text-align: center;
            background: var(--bg-surface);
            transition: background 0.3s ease, border-color 0.3s ease;
        }
        
        .os-stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 48px;
            flex-wrap: wrap;
        }
        
        .os-stat {
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--bg-elevated);
            padding: 16px 32px;
            border-radius: 100px;
            border: 1px solid var(--border);
            font-size: 16px;
            font-weight: 500;
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .os-val {
            font-family: var(--font-code);
            font-weight: 700;
            color: var(--text-primary);
            font-size: 18px;
        }

        /* Footer */
        footer {
            padding: 80px 0 40px;
            text-align: center;
        }
        
        .footer-logo {
            justify-content: center;
            margin-bottom: 32px;
        }

        .footer-links {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 40px;
        }
        
        .footer-links a {
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 500;
        }
        
        .footer-links a:hover {
            color: var(--text-primary);
        }

        .footer-tagline {
            color: var(--text-muted);
            font-size: 15px;
            margin-bottom: 16px;
        }

        /* Animations & Reveal */
        .reveal {
            opacity: 0;
            transform: translateY(40px);
            transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .reveal.active {
            opacity: 1;
            transform: translateY(0);
        }
        
        .delay-1 { transition-delay: 0.1s; }
        .delay-2 { transition-delay: 0.2s; }
        .delay-3 { transition-delay: 0.3s; }

        @keyframes meshMove {
            0% { transform: scale(1) translate(0, 0); }
            100% { transform: scale(1.1) translate(-2%, -2%); }
        }

        @keyframes slideDown {
            to { transform: translateY(0); }
        }

        @keyframes flipUpdate {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
        
        @keyframes blink {
            50% { opacity: 0; }
        }

        @keyframes pulse-glow {
            0% { box-shadow: 0 0 20px rgba(147, 51, 234, 0.2); }
            50% { box-shadow: 0 0 40px rgba(147, 51, 234, 0.4); }
            100% { box-shadow: 0 0 20px rgba(147, 51, 234, 0.2); }
        }

        /* Responsive */
        @media (max-width: 992px) {
            .hero p.subhead { margin: 0 auto 48px; }
            .hero-ctas { justify-content: center; }
            .stats-strip { justify-content: center; }
            
            .step { grid-template-columns: 1fr; text-align: center; gap: 24px; }
            .step-num { margin: 0 auto; }
            .steps-line { left: 50%; }
            
            .calc-results { grid-template-columns: 1fr 1fr; }
            
            .spokes { flex-wrap: wrap; gap: 24px; }
            .arch-svg { display: none; }
        }
        
        @media (max-width: 768px) {
            .nav-links { display: none; }
            .calc-results { grid-template-columns: 1fr; }
            .table-wrapper { padding: 0; border: none; box-shadow: none; }
        }

    </style>
</head>
<body>

    <div class="bg-mesh"></div>
    <div class="bg-noise"></div>

    <nav>
        <div class="container nav-inner">
            <a href="#" class="logo">
                <img src="/isotype" alt="Bublee Logo" class="logo-mark" onerror="this.style.display='none'">
            </a>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="#how-it-works">How it Works</a>
                <a href="#pricing">Pricing</a>
                <button id="theme-toggle" class="theme-toggle-btn" aria-label="Toggle theme">
                    <i data-lucide="moon" size="20"></i>
                </button>
            </div>
            <a href="/app" class="btn btn-primary" style="margin-left:auto;">Sign In</a>
        </div>
    </nav>

    <header class="hero container">
        <div class="hero-center reveal">
            <div class="hero-badge">
                <i data-lucide="bot" size="18"></i> Open Source · MIT License
            </div>
            <h1 id="hero-h1">
                Turn WhatsApp Into Your Agency's Recurring Revenue <span class="text-gradient">Machine</span>
            </h1>
            <p class="subhead">Deploy unlimited AI receptionists for your clients. One core. One command. Infinite instances. 85–95% margin.</p>
            
            <div class="hero-ctas">
                <div class="code-block" style="width: auto;">
                    <span>npm install -g bublee-ai</span>
                    <button class="copy-btn" onclick="copyText('npm install -g bublee-ai', this)">
                        <i data-lucide="copy" size="14"></i>
                    </button>
                </div>
                <a href="#how-it-works" class="btn btn-ghost">See the business model &rarr;</a>
            </div>

            <div class="stats-strip">
                <span><i data-lucide="zap" size="18" style="color:var(--accent-warm)"></i> 10 min setup</span>
                <span><i data-lucide="server" size="18"></i> $6/mo server</span>
                <span><i data-lucide="trending-up" size="18" style="color:var(--accent-money)"></i> 85% margins</span>
                <span><i data-lucide="unlock" size="18"></i> 0 vendor lock-in</span>
            </div>
        </div>
    </header>

    <section id="calculator" class="section calculator">
        <div class="container calc-wrapper reveal">
            <h2>Calculate Your MRR Before Writing a Single Line</h2>
            
            <div class="calc-controls">
                <span class="calc-label">How many clients? (<span id="client-count">10</span>)</span>
                <input type="range" id="client-slider" min="1" max="100" value="10" step="1">
                
                <span class="calc-label" style="margin-top: 32px;">Average Monthly Charge per Client</span>
                <div class="price-tiers">
                    <button class="price-btn" data-price="147">$147/mo</button>
                    <button class="price-btn active" data-price="297">$297/mo</button>
                    <button class="price-btn" data-price="497">$497/mo</button>
                </div>
            </div>

            <div class="calc-results">
                <div class="result-card">
                    <div class="res-label">Monthly Revenue</div>
                    <div class="res-value money" id="res-mrr">$2,970</div>
                </div>
                <div class="result-card">
                    <div class="res-label">Your Cost (LLM APIs)</div>
                    <div class="res-value" id="res-cost">$100</div>
                </div>
                <div class="result-card">
                    <div class="res-label">Net Margin</div>
                    <div class="res-value" id="res-margin">96%</div>
                    <div class="progress-bar"><div class="progress-fill" id="bar-margin"></div></div>
                </div>
                <div class="result-card">
                    <div class="res-label">Annual Projection</div>
                    <div class="res-value text-gradient" id="res-arr">$35,640</div>
                </div>
            </div>
        </div>
    </section>

    <section id="how-it-works" class="section">
        <div class="container">
            <h2 class="section-title reveal">How It Works</h2>
            
            <div class="steps-container">
                <div class="steps-line">
                    <div class="steps-line-fill" id="step-line-fill"></div>
                </div>

                <div class="step reveal" id="step-1">
                    <div class="step-num">1</div>
                    <div class="step-content">
                        <h3>Install & Train (5 min)</h3>
                        <p>Set up Bublee core on a cheap VPS. Create your first persona.</p>
                    </div>
                    <div class="term-window">
                        <div class="term-header">
                            <div class="term-dot r"></div><div class="term-dot y"></div><div class="term-dot g"></div>
                        </div>
                        <div class="term-body typewriter-text" data-text="$ npm install -g bublee-ai\n$ bublee persona create my-receptionist\n> Persona 'my-receptionist' ready."></div>
                    </div>
                </div>

                <div class="step reveal delay-1" id="step-2">
                    <div class="step-num">2</div>
                    <div class="step-content">
                        <h3>Clone to Clients (1 min each)</h3>
                        <p>Deploy isolated instances for each client. They share zero state.</p>
                    </div>
                    <div class="term-window">
                        <div class="term-header">
                            <div class="term-dot r"></div><div class="term-dot y"></div><div class="term-dot g"></div>
                        </div>
                        <div class="term-body typewriter-text" data-text="$ bublee sync --add /opt/client-pizza\n$ bublee sync --add /opt/client-salon\n> Deployed 2 isolated instances."></div>
                    </div>
                </div>

                <div class="step reveal delay-2" id="step-3">
                    <div class="step-num">3</div>
                    <div class="step-content">
                        <h3>Collect Monthly</h3>
                        <p>Clients pay you. You push core updates to everyone in one command.</p>
                    </div>
                    <div class="term-window">
                        <div class="term-header">
                            <div class="term-dot r"></div><div class="term-dot y"></div><div class="term-dot g"></div>
                        </div>
                        <div class="term-body typewriter-text" data-text="$ bublee sync -y\n> Syncing core updates...\n> Updated 50/50 instances successfully."></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section id="industries" class="section">
        <div class="container">
            <h2 class="section-title reveal">Built for Any Industry</h2>
            
            <div class="industries-grid">
                <div class="industry-card reveal">
                    <div class="ind-icon">🍕</div>
                    <h3>Restaurants</h3>
                    <p>Reservations, menu queries, opening hours.</p>
                    <span class="ind-price">$147–297/mo</span>
                </div>
                <div class="industry-card reveal delay-1">
                    <div class="ind-icon">💇</div>
                    <h3>Salons & Spas</h3>
                    <p>Bookings, prices, services, upsells.</p>
                    <span class="ind-price">$197–397/mo</span>
                </div>
                <div class="industry-card reveal delay-2">
                    <div class="ind-icon">🏠</div>
                    <h3>Real Estate</h3>
                    <p>Lead qualification, property listings.</p>
                    <span class="ind-price">$297–597/mo</span>
                </div>
                <div class="industry-card reveal">
                    <div class="ind-icon">🦷</div>
                    <h3>Medical/Dental</h3>
                    <p>Consultations, reminders, FAQs.</p>
                    <span class="ind-price">$347–697/mo</span>
                </div>
                <div class="industry-card reveal delay-1">
                    <div class="ind-icon">🛒</div>
                    <h3>E-commerce</h3>
                    <p>Orders, tracking, returns, support.</p>
                    <span class="ind-price">$197–497/mo</span>
                </div>
                <div class="industry-card reveal delay-2">
                    <div class="ind-icon">🏋️</div>
                    <h3>Gyms</h3>
                    <p>Classes, schedules, memberships.</p>
                    <span class="ind-price">$197–397/mo</span>
                </div>
            </div>
        </div>
    </section>

    <section id="architecture" class="section">
        <div class="container">
            <h2 class="section-title reveal">Hub-and-Spoke Architecture</h2>
            
            <div class="arch-container reveal">
                <svg class="arch-svg" viewBox="0 0 800 150">
                    <path d="M400,20 Q200,80 160,130" class="arch-line" id="l1" />
                    <path d="M400,20 Q300,80 320,130" class="arch-line" id="l2" />
                    <path d="M400,20 Q500,80 480,130" class="arch-line" id="l3" />
                    <path d="M400,20 Q600,80 640,130" class="arch-line" id="l4" />
                </svg>
                
                <div class="hub">Your Bublee Core</div>
                
                <div class="spokes">
                    <div class="spoke reveal delay-1">
                        <i data-lucide="message-circle" class="spoke-icon"></i>
                        <div class="spoke-title">Restaurant A</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke reveal delay-2">
                        <i data-lucide="send" class="spoke-icon"></i>
                        <div class="spoke-title">Salon B</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke reveal delay-3">
                        <i data-lucide="message-circle" class="spoke-icon"></i>
                        <div class="spoke-title">Medical C</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke dashed reveal delay-3">
                        <i data-lucide="plus" class="spoke-icon"></i>
                        <div class="spoke-title">Add Client</div>
                        <div class="spoke-meta">bublee sync --add</div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section id="compare" class="section">
        <div class="container">
            <h2 class="section-title reveal">Why Agencies Choose Bublee</h2>
            
            <div class="table-wrapper reveal">
                <table>
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Voiceflow</th>
                            <th>n8n / Zapier</th>
                            <th>Custom Dev Team</th>
                            <th class="col-bublee">Bublee ✓</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="reveal">
                            <td>Cost</td>
                            <td>$50+/mo per client</td>
                            <td>Per execution ($$)</td>
                            <td>$10k+ build</td>
                            <td class="col-bublee text-money" style="font-weight:bold;">$6/mo flat (VPS)</td>
                        </tr>
                        <tr class="reveal">
                            <td>Setup Time</td>
                            <td>Hours per bot</td>
                            <td>Days (complex logic)</td>
                            <td>Months</td>
                            <td class="col-bublee">15 minutes</td>
                        </tr>
                        <tr class="reveal">
                            <td>Vendor Lock-in</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Yes</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Yes</td>
                            <td><i data-lucide="check" class="icon-check" size="20"></i> No</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> No (Open Source)</td>
                        </tr>
                        <tr class="reveal">
                            <td>Unlimited Instances</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Pay per instance</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Pay per run</td>
                            <td><i data-lucide="check" class="icon-check" size="20"></i> Yes</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> Yes</td>
                        </tr>
                        <tr class="reveal">
                            <td>1-Command Updates</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> Yes</td>
                        </tr>
                        <tr class="reveal">
                            <td>Net Margins</td>
                            <td>~30%</td>
                            <td>~40%</td>
                            <td>Low (high fixed cost)</td>
                            <td class="col-bublee text-money" style="font-weight:bold;">85–95%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </section>

    <section id="quick-start" class="section os-section">
        <div class="container quick-start reveal">
            <h2 style="font-size: var(--text-h2); margin-bottom: 24px;">From zero to your first paying client in 15 minutes.</h2>
            <p style="color:var(--text-secondary); margin-bottom: 40px; font-size: 20px;">Open terminal. Run command. Collect recurring revenue.</p>
            
            <div class="term-window qs-term">
                <div class="term-header">
                    <div class="term-dot r"></div><div class="term-dot y"></div><div class="term-dot g"></div>
                    <div style="margin-left:auto; display:flex;">
                        <button class="copy-btn" onclick="copyText('npm install -g bublee-ai && bublee init', this)" style="background:transparent; border:none; color:inherit; cursor:pointer;">
                            <i data-lucide="copy" size="14"></i>
                        </button>
                    </div>
                </div>
                <div class="term-body typewriter-text" data-text="$ npm install -g bublee-ai\n$ bublee init\n> Initializing Bublee Core...\n> Core ready.\n$ bublee persona create demo-client\n> Persona 'demo-client' isolated and deployed.\n> Status: ONLINE."></div>
            </div>
            
            <div class="os-stats reveal">
                <div class="os-stat">
                    <i data-lucide="github" size="24"></i>
                    <span class="os-val" id="gh-stars">Loading...</span> Stars
                </div>
                <div class="os-stat">
                    <i data-lucide="book-open" size="24"></i>
                    <span class="os-val">MIT License</span>
                </div>
                <div class="os-stat">
                    <i data-lucide="package" size="24"></i>
                    <span class="os-val">NPM</span>
                </div>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <a href="#" class="logo footer-logo">
                <img src="/isotype" alt="Bublee Logo" class="logo-mark" onerror="this.style.display='none'">
            </a>
            <div class="footer-links">
                <a href="https://github.com/sxrubyo/bublee">GitHub</a>
                <a href="#">NPM</a>
                <a href="#">Discussions</a>
                <a href="#">Documentation</a>
            </div>
            <p class="footer-tagline">Built for agencies. Designed for profit. Engineered for scale.</p>
            <p style="font-size:13px; color:var(--text-muted);">Created by sxrubyo &middot; MIT License &middot; Open Source</p>
        </div>
    </footer>

    <script>
        // Init Lucide Icons
        lucide.createIcons();

        // Theme Toggle Logic
        const themeToggleBtn = document.getElementById('theme-toggle');
        
        function setTheme(isDark) {
            if (isDark) {
                document.documentElement.classList.add('dark-theme');
                themeToggleBtn.innerHTML = '<i data-lucide="sun" size="20"></i>';
                localStorage.setItem('bublee-theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark-theme');
                themeToggleBtn.innerHTML = '<i data-lucide="moon" size="20"></i>';
                localStorage.setItem('bublee-theme', 'light');
            }
            lucide.createIcons();
        }

        const savedTheme = localStorage.getItem('bublee-theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            setTheme(true);
        } else {
            setTheme(false);
        }

        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.classList.contains('dark-theme');
            setTheme(!isDark);
        });

        // Copy Function
        function copyText(text, btn) {
            navigator.clipboard.writeText(text);
            const originalIcon = btn.innerHTML;
            btn.innerHTML = '<i data-lucide="check" size="14" style="color:var(--accent-secondary)"></i> Copied!';
            lucide.createIcons();
            setTimeout(() => {
                btn.innerHTML = originalIcon;
            }, 2000);
        }

        // Calculator Logic
        const slider = document.getElementById('client-slider');
        const countDisplay = document.getElementById('client-count');
        const priceBtns = document.querySelectorAll('.price-btn');
        let currentPrice = 297;

        function updateCalc() {
            // Snapping logic as requested
            let v = parseInt(slider.value);
            if(v < 5) v = v; // let 1-4 slide
            else if(v >= 5 && v < 10) v = 5;
            else if(v >= 10 && v < 25) v = 10;
            else if(v >= 25 && v < 50) v = 25;
            else if(v >= 50 && v < 100) v = 50;
            else if(v == 100) v = 100;
            
            countDisplay.innerText = v;
            
            const rev = v * currentPrice;
            const cost = v * 10; // avg cost
            const marginPct = Math.round(((rev - cost) / rev) * 100) || 0;
            const arr = rev * 12;

            document.getElementById('res-mrr').innerText = '$' + rev.toLocaleString();
            document.getElementById('res-cost').innerText = '$' + cost.toLocaleString();
            document.getElementById('res-margin').innerText = Math.max(marginPct, 0) + '%';
            document.getElementById('bar-margin').style.width = Math.max(marginPct, 0) + '%';
            document.getElementById('res-arr').innerText = '$' + arr.toLocaleString();

            // Animate cards
            document.querySelectorAll('.result-card').forEach(c => {
                c.classList.remove('update');
                void c.offsetWidth; // trigger reflow
                c.classList.add('update');
            });
        }

        slider.addEventListener('input', updateCalc);

        priceBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                priceBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentPrice = parseInt(e.target.getAttribute('data-price'));
                updateCalc();
            });
        });

        // Intersection Observer for Reveals, SVG Lines, and Typewriters
        const observerOptions = { threshold: 0.15, rootMargin: "0px 0px -50px 0px" };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    
                    // Activate SVG lines if architecture section
                    if(entry.target.classList.contains('arch-container')) {
                        document.querySelectorAll('.arch-line').forEach(l => l.classList.add('active'));
                    }
                    
                    // How it works steps line
                    if(entry.target.id === 'how-it-works') {
                        document.getElementById('step-line-fill').style.height = '100%';
                    }

                    // Typewriter effect
                    if(entry.target.classList.contains('term-window') || entry.target.querySelector('.typewriter-text')) {
                        const tw = entry.target.classList.contains('typewriter-text') ? entry.target : entry.target.querySelector('.typewriter-text');
                        if(tw && !tw.hasAttribute('data-typed')) {
                            tw.setAttribute('data-typed', 'true');
                            const text = tw.getAttribute('data-text');
                            tw.innerText = '';
                            let i = 0;
                            const typeInt = setInterval(() => {
                                if(text.charAt(i) === '\\\\' && text.charAt(i+1) === 'n') {
                                    tw.innerHTML += '<br>';
                                    i++;
                                } else {
                                    tw.innerHTML += text.charAt(i);
                                }
                                i++;
                                if(i >= text.length) clearInterval(typeInt);
                            }, 30);
                        }
                    }
                }
            });
        }, observerOptions);

        document.querySelectorAll('.reveal, .term-window').forEach(el => observer.observe(el));
        
        // Fetch GitHub Stars
        fetch('https://api.github.com/repos/sxrubyo/bublee')
            .then(res => res.json())
            .then(data => {
                if(data.stargazers_count) {
                    document.getElementById('gh-stars').innerText = data.stargazers_count;
                } else {
                    document.getElementById('gh-stars').innerText = '100+';
                }
            })
            .catch(() => {
                document.getElementById('gh-stars').innerText = '100+';
            });

    </script>
</body>
</html>"""

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(html_content)
