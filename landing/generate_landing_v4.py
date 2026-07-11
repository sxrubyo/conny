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
            --bg-void: #FAFAFC;
            --bg-surface: #FFFFFF;
            --bg-elevated: #F4F4F7;
            --border: #E8E8ED;
            --border-glow: rgba(147, 51, 234, 0.15);
            --accent-primary: #9333EA;
            --accent-secondary: #25D366;
            --accent-money: #10B981;
            --accent-warm: #F59E0B;
            
            --text-primary: #0A0A0F;
            --text-secondary: #50506A;
            --text-muted: #9090B0;
            
            --gradient-hero: linear-gradient(135deg, #9333EA 0%, #25D366 100%);
            --gradient-money: linear-gradient(135deg, #10B981 0%, #059669 100%);
            --gradient-card: linear-gradient(145deg, #FFFFFF 0%, #FAFAFC 100%);
            
            --text-hero: clamp(48px, 6vw, 84px);
            --text-h2: clamp(32px, 4vw, 56px);
            
            --font-head: 'Plus Jakarta Sans', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-code: 'Fira Code', monospace;
            
            --nav-bg: rgba(250, 250, 252, 0.85);
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
            line-height: 1.15;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* Layout Utils */
        .container {
            width: 100%;
            max-width: 1440px;
            margin: 0 auto;
            padding: 0 5vw;
        }
        
        .nav-container {
            width: 100%;
            max-width: 1800px;
            margin: 0 auto;
            padding: 0 4vw;
        }
        
        .section {
            padding: 140px 0;
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
            padding: 14px 32px;
            border-radius: 100px;
            font-family: var(--font-head);
            font-weight: 700;
            font-size: 15px;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
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
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(147, 51, 234, 0.4);
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
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
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
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border-bottom: 1px solid var(--border);
            background: var(--nav-bg);
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .nav-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 90px;
        }

        .nav-left {
            flex: 1;
            display: flex;
            align-items: center;
        }
        
        .nav-center {
            flex: 2;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
        }
        
        .nav-right {
            flex: 1;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 24px;
        }

        .logo {
            display: flex;
            align-items: center;
        }

        .logo-mark {
            height: 52px;
            object-fit: contain;
            transition: filter 0.3s ease;
            /* Si en modo claro el logo blanco se pierde, esto puede activarse: filter: invert(var(--invert-logo)); */
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
            padding-top: 220px;
            padding-bottom: 120px;
            text-align: center;
        }

        .hero-center {
            max-width: 1000px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: transparent;
            border: 1px solid var(--border);
            padding: 8px 20px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 40px;
            transition: border-color 0.3s;
        }
        
        .hero-badge:hover {
            border-color: var(--accent-primary);
        }

        .hero h1 {
            font-size: var(--text-hero);
            margin-bottom: 32px;
        }

        .hero p.subhead {
            font-size: 22px;
            line-height: 1.6;
            color: var(--text-secondary);
            margin-bottom: 56px;
            max-width: 800px;
        }

        .hero-ctas {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            margin-bottom: 80px;
            flex-wrap: wrap;
        }

        /* Calculator - Cardless Approach */
        .calculator {
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            background: var(--bg-surface);
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .calc-wrapper {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .calc-wrapper h2 {
            font-size: var(--text-h2);
            margin-bottom: 64px;
            text-align: center;
        }

        .calc-controls {
            margin-bottom: 80px;
        }
        
        .calc-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 20px;
            margin-bottom: 24px;
            color: var(--text-primary);
        }

        input[type=range] {
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
            margin-bottom: 48px;
        }
        
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 32px;
            width: 32px;
            border-radius: 50%;
            background: var(--bg-surface);
            cursor: pointer;
            margin-top: -14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border: 3px solid var(--accent-primary);
        }
        
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: var(--border);
            border-radius: 2px;
        }

        .price-tiers {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .price-btn {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 20px;
            border-radius: 12px;
            cursor: pointer;
            font-family: var(--font-head);
            font-weight: 700;
            font-size: 18px;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }
        
        .price-btn span {
            font-size: 13px;
            font-weight: 500;
            font-family: var(--font-body);
            opacity: 0.7;
        }
        
        .price-btn.active {
            background: var(--bg-surface);
            border-color: var(--accent-primary);
            color: var(--accent-primary);
            box-shadow: 0 8px 30px rgba(147, 51, 234, 0.08);
        }

        .calc-results {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 40px;
            text-align: center;
            padding-top: 48px;
            border-top: 1px solid var(--border);
        }
        
        .result-item {
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: transform 0.3s;
        }
        
        .result-item.update {
            animation: flipUpdate 0.4s ease;
        }
        
        .res-label {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .res-value {
            font-size: 48px;
            font-weight: 800;
            font-family: var(--font-head);
            letter-spacing: -0.02em;
        }
        
        .res-value.money { color: var(--accent-money); }

        /* How it Works */
        .section-title {
            text-align: center;
            font-size: var(--text-h2);
            margin-bottom: 100px;
        }

        .steps-container {
            display: flex;
            flex-direction: column;
            gap: 120px;
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
            gap: 64px;
            position: relative;
            z-index: 1;
            align-items: center;
        }

        .step-num {
            width: 64px;
            height: 64px;
            background: var(--bg-surface);
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
        }

        .step-content h3 {
            font-size: 32px;
            margin-bottom: 20px;
        }
        
        .step-content p {
            color: var(--text-secondary);
            font-size: 18px;
            line-height: 1.7;
        }

        .term-window {
            background: #05050A;
            border: 1px solid #1A1A24;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .term-header {
            background: #0A0A0F;
            padding: 16px 24px;
            display: flex;
            gap: 8px;
            border-bottom: 1px solid #1A1A24;
        }
        
        .term-dot { width: 12px; height: 12px; border-radius: 50%; }
        .term-dot.r { background: #FF5F56; }
        .term-dot.y { background: #FFBD2E; }
        .term-dot.g { background: #27C93F; }
        
        .term-body {
            padding: 32px 24px;
            font-family: var(--font-code);
            font-size: 15px;
            color: #A6ACCD;
            min-height: 140px;
            line-height: 1.6;
        }
        
        .typewriter-text::after {
            content: '█';
            animation: blink 1s step-start infinite;
            color: var(--accent-primary);
        }

        /* Industry Grid */
        .industries-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 24px;
        }

        .industry-card {
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 40px;
            transition: all 0.3s ease;
        }
        
        .industry-card:hover {
            border-color: var(--accent-primary);
            background: var(--bg-surface);
            box-shadow: 0 20px 40px rgba(0,0,0,0.02);
        }

        .ind-icon {
            color: var(--accent-primary);
            margin-bottom: 24px;
            background: var(--bg-elevated);
            width: 64px;
            height: 64px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .industry-card h3 {
            font-size: 24px;
            margin-bottom: 16px;
        }

        .industry-card p {
            color: var(--text-secondary);
            font-size: 16px;
            margin-bottom: 32px;
        }

        .ind-price {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--accent-money);
            font-family: var(--font-code);
            font-weight: 600;
            font-size: 14px;
        }

        /* Architecture */
        .arch-container {
            background: transparent;
            padding: 100px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
        }

        .hub {
            background: var(--accent-primary);
            color: white;
            padding: 24px 48px;
            border-radius: 100px;
            font-family: var(--font-head);
            font-weight: 800;
            font-size: 24px;
            z-index: 10;
            box-shadow: 0 0 40px rgba(147, 51, 234, 0.4);
            animation: pulse-glow 3s infinite;
        }

        .spokes {
            display: flex;
            justify-content: center;
            gap: 64px;
            width: 100%;
            margin-top: 120px;
            position: relative;
            z-index: 10;
        }
        
        .spoke {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            width: 220px;
            transition: all 0.3s ease;
        }
        
        .spoke.dashed {
            border-style: dashed;
            opacity: 0.7;
            background: transparent;
        }
        
        .spoke-icon {
            color: var(--text-secondary);
            margin-bottom: 16px;
        }

        .spoke-title {
            font-weight: 700;
            margin-bottom: 8px;
            font-size: 18px;
        }
        
        .spoke-meta {
            font-family: var(--font-code);
            font-size: 13px;
            color: var(--text-muted);
        }

        .arch-svg {
            position: absolute;
            top: 150px;
            left: 0;
            width: 100%;
            height: 200px;
            z-index: 1;
        }
        
        .arch-line {
            fill: none;
            stroke: var(--border);
            stroke-width: 2;
            stroke-dasharray: 600;
            stroke-dashoffset: 600;
            transition: stroke-dashoffset 1.5s ease-out, stroke 0.3s ease;
        }
        
        .arch-line.active {
            stroke-dashoffset: 0;
            stroke: var(--accent-primary);
            opacity: 0.5;
        }

        /* Competitive Table */
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        
        th, td {
            padding: 32px;
            border-bottom: 1px solid var(--border);
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        th {
            font-family: var(--font-head);
            font-weight: 700;
            color: var(--text-secondary);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: transparent;
        }
        
        .col-bublee {
            background: rgba(147, 51, 234, 0.03);
            border-left: 1px solid rgba(147, 51, 234, 0.2);
            border-right: 1px solid rgba(147, 51, 234, 0.2);
        }
        
        th.col-bublee {
            color: var(--text-primary);
            border-top: 1px solid rgba(147, 51, 234, 0.2);
            font-size: 16px;
        }

        tr:last-child td.col-bublee {
            border-bottom: 1px solid rgba(147, 51, 234, 0.2);
        }
        
        tr:last-child td {
            border-bottom: none;
        }

        .icon-check { color: var(--accent-secondary); }
        .icon-x { color: var(--text-muted); }

        /* Footer */
        footer {
            padding: 120px 0 60px;
            text-align: center;
            border-top: 1px solid var(--border);
        }
        
        .footer-logo {
            justify-content: center;
            margin-bottom: 40px;
        }

        .footer-links {
            display: flex;
            justify-content: center;
            gap: 48px;
            margin-bottom: 48px;
        }
        
        .footer-links a {
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 500;
        }
        
        .footer-links a:hover {
            color: var(--text-primary);
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
            .step { grid-template-columns: 1fr; text-align: center; gap: 32px; }
            .step-num { margin: 0 auto; }
            .steps-line { left: 50%; }
            .calc-results { grid-template-columns: 1fr; gap: 32px; }
            .price-tiers { grid-template-columns: 1fr; }
            .spokes { flex-wrap: wrap; gap: 24px; }
            .arch-svg { display: none; }
        }
        
        @media (max-width: 768px) {
            .nav-center { display: none; }
            .nav-container { padding: 0 5vw; }
            .table-wrapper { padding: 0; border: none; box-shadow: none; }
            th, td { padding: 16px; font-size: 14px; }
        }

    </style>
</head>
<body>

    <div class="bg-mesh"></div>

    <nav>
        <div class="nav-container nav-inner">
            <div class="nav-left">
                <a href="#" class="logo">
                    <img src="/isotype" alt="Bublee Logo" class="logo-mark" onerror="this.style.display='none'">
                </a>
            </div>
            
            <div class="nav-center nav-links">
                <a href="#features">Features</a>
                <a href="#how-it-works">How it Works</a>
                <a href="#pricing">Pricing</a>
            </div>

            <div class="nav-right">
                <button id="theme-toggle" class="theme-toggle-btn" aria-label="Toggle theme">
                    <i data-lucide="moon" size="20"></i>
                </button>
                <a href="/app" class="btn btn-primary">Sign In</a>
            </div>
        </div>
    </nav>

    <header class="hero container">
        <div class="hero-center reveal">
            <div class="hero-badge">
                <i data-lucide="git-branch" size="16"></i> Open Source · MIT License
            </div>
            <h1 id="hero-h1">
                Turn WhatsApp Into Your Agency's Recurring Revenue <span class="text-gradient">Machine</span>
            </h1>
            <p class="subhead">Deploy unlimited AI receptionists for your clients. One core. One command. Infinite instances. 85–95% margin.</p>
            
            <div class="hero-ctas">
                <div class="code-block" style="width: auto;">
                    <span>npm install -g bublee-ai</span>
                    <button class="copy-btn" onclick="copyText('npm install -g bublee-ai', this)" aria-label="Copy to clipboard">
                        <i data-lucide="copy" size="16"></i>
                    </button>
                </div>
                <a href="#how-it-works" class="btn btn-ghost">See the business model &rarr;</a>
            </div>
        </div>
    </header>

    <section id="calculator" class="section calculator">
        <div class="container calc-wrapper reveal">
            <h2>Calculate Your MRR</h2>
            
            <div class="calc-controls">
                <div class="calc-label">
                    <span>Active Clients</span>
                    <span id="client-count" style="font-family: var(--font-code); color: var(--accent-primary);">10</span>
                </div>
                <input type="range" id="client-slider" min="1" max="100" value="10" step="1">
                
                <div class="calc-label" style="margin-top: 48px; margin-bottom: 16px;">
                    <span>Average Monthly Charge</span>
                </div>
                <div class="price-tiers">
                    <button class="price-btn" data-price="147">
                        $147
                        <span>/ month</span>
                    </button>
                    <button class="price-btn active" data-price="297">
                        $297
                        <span>/ month</span>
                    </button>
                    <button class="price-btn" data-price="497">
                        $497
                        <span>/ month</span>
                    </button>
                </div>
            </div>

            <div class="calc-results">
                <div class="result-item">
                    <div class="res-label">Monthly Revenue</div>
                    <div class="res-value money" id="res-mrr">$2,970</div>
                </div>
                <div class="result-item">
                    <div class="res-label">API Cost</div>
                    <div class="res-value" id="res-cost">$100</div>
                </div>
                <div class="result-item">
                    <div class="res-label">Annual Projection</div>
                    <div class="res-value text-gradient" id="res-arr">$35,640</div>
                </div>
            </div>
        </div>
    </section>

    <section id="features" class="section">
        <div class="container">
            <h2 class="section-title reveal">Built for Any Industry</h2>
            
            <div class="industries-grid">
                <div class="industry-card reveal">
                    <div class="ind-icon"><i data-lucide="utensils-crossed" size="32" stroke-width="1.5"></i></div>
                    <h3>Restaurants</h3>
                    <p>Reservations, menu queries, and opening hours automatically handled.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $147–297/mo</div>
                </div>
                <div class="industry-card reveal delay-1">
                    <div class="ind-icon"><i data-lucide="scissors" size="32" stroke-width="1.5"></i></div>
                    <h3>Salons & Spas</h3>
                    <p>Bookings, service prices, upsells, and appointment reminders.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $197–397/mo</div>
                </div>
                <div class="industry-card reveal delay-2">
                    <div class="ind-icon"><i data-lucide="home" size="32" stroke-width="1.5"></i></div>
                    <h3>Real Estate</h3>
                    <p>Immediate lead qualification and property listing details on demand.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $297–597/mo</div>
                </div>
                <div class="industry-card reveal">
                    <div class="ind-icon"><i data-lucide="activity" size="32" stroke-width="1.5"></i></div>
                    <h3>Medical/Dental</h3>
                    <p>Patient consultations, pre-screening, FAQs, and scheduling.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $347–697/mo</div>
                </div>
                <div class="industry-card reveal delay-1">
                    <div class="ind-icon"><i data-lucide="shopping-cart" size="32" stroke-width="1.5"></i></div>
                    <h3>E-commerce</h3>
                    <p>Order tracking, returns processing, and instant customer support.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $197–497/mo</div>
                </div>
                <div class="industry-card reveal delay-2">
                    <div class="ind-icon"><i data-lucide="dumbbell" size="32" stroke-width="1.5"></i></div>
                    <h3>Gyms</h3>
                    <p>Class schedules, membership renewals, and facility information.</p>
                    <div class="ind-price"><i data-lucide="trending-up" size="14"></i> $197–397/mo</div>
                </div>
            </div>
        </div>
    </section>

    <section id="how-it-works" class="section">
        <div class="container">
            <h2 class="section-title reveal">Deploy at Scale</h2>
            
            <div class="steps-container">
                <div class="steps-line">
                    <div class="steps-line-fill" id="step-line-fill"></div>
                </div>

                <div class="step reveal" id="step-1">
                    <div class="step-num">1</div>
                    <div class="step-content">
                        <h3>Install & Train</h3>
                        <p>Set up Bublee core on a single VPS. Create your first persona using natural language rules and knowledge base documents.</p>
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
                        <h3>Clone to Clients</h3>
                        <p>Deploy completely isolated instances for each client. They share zero state, meaning strict data privacy across your portfolio.</p>
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
                        <h3>1-Click Core Sync</h3>
                        <p>Clients pay you monthly. When you update the core AI engine, push improvements to all instances simultaneously with a single command.</p>
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
                        <i data-lucide="message-circle" class="spoke-icon" size="24"></i>
                        <div class="spoke-title">Restaurant A</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke reveal delay-2">
                        <i data-lucide="send" class="spoke-icon" size="24"></i>
                        <div class="spoke-title">Salon B</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke reveal delay-3">
                        <i data-lucide="message-circle" class="spoke-icon" size="24"></i>
                        <div class="spoke-title">Medical C</div>
                        <div class="spoke-meta">.env | db | persona</div>
                    </div>
                    <div class="spoke dashed reveal delay-3">
                        <i data-lucide="plus" class="spoke-icon" size="24"></i>
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
                            <th>Custom Build</th>
                            <th class="col-bublee">Bublee ✓</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="reveal">
                            <td>Cost Structure</td>
                            <td>$50+/mo per client</td>
                            <td>Per execution ($$)</td>
                            <td>$10k+ fixed cost</td>
                            <td class="col-bublee text-money" style="font-weight:bold;">$6/mo flat (VPS)</td>
                        </tr>
                        <tr class="reveal">
                            <td>Vendor Lock-in</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Yes</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Yes</td>
                            <td><i data-lucide="check" class="icon-check" size="20"></i> No</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> No (Open Source)</td>
                        </tr>
                        <tr class="reveal">
                            <td>Multi-Tenant Architecture</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Pay per instance</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Complex logic</td>
                            <td><i data-lucide="check" class="icon-check" size="20"></i> Built-in</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> Built-in</td>
                        </tr>
                        <tr class="reveal">
                            <td>Global Upgrades</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual updates</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual updates</td>
                            <td><i data-lucide="x" class="icon-x" size="20"></i> Manual deployments</td>
                            <td class="col-bublee"><i data-lucide="check" class="icon-check" size="20"></i> 1-Command CLI</td>
                        </tr>
                    </tbody>
                </table>
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
                <a href="#">Documentation</a>
            </div>
            <p style="color:var(--text-muted); font-size: 14px; max-width: 400px; margin: 0 auto;">
                Built for agencies. Designed for profit. Engineered for scale.<br>
                MIT License &middot; Open Source
            </p>
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
            btn.innerHTML = '<i data-lucide="check" size="16" style="color:var(--accent-secondary)"></i>';
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
            let v = parseInt(slider.value);
            if(v < 5) v = v; 
            else if(v >= 5 && v < 10) v = 5;
            else if(v >= 10 && v < 25) v = 10;
            else if(v >= 25 && v < 50) v = 25;
            else if(v >= 50 && v < 100) v = 50;
            else if(v == 100) v = 100;
            
            countDisplay.innerText = v;
            
            const rev = v * currentPrice;
            const cost = v * 10;
            const arr = rev * 12;

            document.getElementById('res-mrr').innerText = '$' + rev.toLocaleString();
            document.getElementById('res-cost').innerText = '$' + cost.toLocaleString();
            document.getElementById('res-arr').innerText = '$' + arr.toLocaleString();

            document.querySelectorAll('.result-item').forEach(c => {
                c.classList.remove('update');
                void c.offsetWidth;
                c.classList.add('update');
            });
        }

        slider.addEventListener('input', updateCalc);

        priceBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                priceBtns.forEach(b => b.classList.remove('active'));
                const targetBtn = e.target.closest('.price-btn');
                targetBtn.classList.add('active');
                currentPrice = parseInt(targetBtn.getAttribute('data-price'));
                updateCalc();
            });
        });

        // Intersection Observer
        const observerOptions = { threshold: 0.1, rootMargin: "0px 0px -50px 0px" };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    
                    if(entry.target.classList.contains('arch-container')) {
                        document.querySelectorAll('.arch-line').forEach(l => l.classList.add('active'));
                    }
                    
                    if(entry.target.id === 'how-it-works') {
                        document.getElementById('step-line-fill').style.height = '100%';
                    }

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

    </script>
</body>
</html>"""

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(html_content)
