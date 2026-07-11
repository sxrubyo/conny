        // Init Lucide Icons
        lucide.createIcons();

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

        // Hero Text Stagger Animation
        document.addEventListener('DOMContentLoaded', () => {
            const h1Spans = document.querySelectorAll('#hero-h1 span');
            h1Spans.forEach((span, i) => {
                setTimeout(() => {
                    span.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
                    span.style.opacity = '1';
                    span.style.transform = 'translateY(0)';
                }, 100 * i);
            });
        });

        // WhatsApp Chat Animation Sequence
        const chatBody = document.getElementById('chat-body');
        
        function runChatSequence() {
            chatBody.innerHTML = ''; // reset
            
            const msg1 = document.createElement('div');
            msg1.className = 'wa-bubble wa-in';
            msg1.innerText = 'Hola, quiero reservar una mesa para 4 personas el viernes';
            
            const typing = document.createElement('div');
            typing.className = 'wa-bubble wa-out wa-typing';
            typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
            
            const msg2 = document.createElement('div');
            msg2.className = 'wa-bubble wa-out';
            msg2.innerText = '¡Hola! 😊 Claro que sí. ¿Para qué hora del viernes prefieres? Tenemos disponibilidad a las 7pm y 8:30pm';
            
            setTimeout(() => { chatBody.appendChild(msg1); msg1.style.opacity=1; msg1.style.transform='translateY(0)'; }, 1000);
            setTimeout(() => { chatBody.appendChild(typing); typing.style.opacity=1; typing.style.transform='translateY(0)'; }, 2000);
            setTimeout(() => { 
                chatBody.removeChild(typing); 
                chatBody.appendChild(msg2); 
                msg2.style.opacity=1; msg2.style.transform='translateY(0)'; 
            }, 4000);
            
            // Loop sequence
            setTimeout(runChatSequence, 8000);
        }
        
        runChatSequence();

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
        const observerOptions = { threshold: 0.2, rootMargin: "0px 0px -50px 0px" };
        
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
                                if(text.charAt(i) === '\\' && text.charAt(i+1) === 'n') {
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

