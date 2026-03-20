// LiveTranslate — main.js

document.addEventListener('DOMContentLoaded', () => {

    // ── 1. Initialize Lucide icons ──
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // ── 2. Navbar scroll state ──
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 20);
        handleScrollTop();
    }, { passive: true });

    // ── 3. Mobile menu toggle ──
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks   = document.getElementById('nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });

        // Close menu when a link is clicked
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
            });
        });
    }

    // ── 4. Scroll animations (IntersectionObserver) ──
    const animatedEls = document.querySelectorAll('.fade-in-up');
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1 }
    );

    animatedEls.forEach(el => observer.observe(el));

    // ── 5. Language pill hover cycling (auto-highlight) ──
    const pills = document.querySelectorAll('.lang-pill');
    let currentPill = 0;
    let pillInterval = null;

    function cyclePills() {
        pills.forEach(p => p.classList.remove('active'));
        pills[currentPill].classList.add('active');
        currentPill = (currentPill + 1) % pills.length;
    }

    const stripSection = document.querySelector('.language-strip');
    if (stripSection) {
        pillInterval = setInterval(cyclePills, 1800);

        stripSection.addEventListener('mouseenter', () => clearInterval(pillInterval));
        stripSection.addEventListener('mouseleave', () => {
            pillInterval = setInterval(cyclePills, 1800);
        });

        pills.forEach((pill, idx) => {
            pill.addEventListener('click', () => {
                clearInterval(pillInterval);
                pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                currentPill = (idx + 1) % pills.length;
                pillInterval = setInterval(cyclePills, 1800);
            });
        });
    }

    // ── 6. FAQ Accordion ──
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const btn = item.querySelector('.faq-question');
        if (!btn) return;

        btn.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');

            // Close all
            faqItems.forEach(i => {
                i.classList.remove('open');
                i.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
            });

            // Open clicked if it was closed
            if (!isOpen) {
                item.classList.add('open');
                btn.setAttribute('aria-expanded', 'true');
            }
        });
    });

    // ── 7. Scroll Spy — Active nav link ──
    const sections = document.querySelectorAll('section[id]');
    const navAnchors = document.querySelectorAll('.nav-links a[href^="#"]');

    const sectionObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.getAttribute('id');
                    navAnchors.forEach(a => {
                        a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
                    });
                }
            });
        },
        { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
    );

    sections.forEach(sec => sectionObserver.observe(sec));

    // ── 8. Hero Typewriter — cycle translations ──
    const typewriterLang = document.getElementById('typewriter-lang');
    const typewriterText = document.getElementById('typewriter-text');
    const typewriterLine = document.getElementById('typewriter-line');

    if (typewriterLang && typewriterText && typewriterLine) {
        const translations = [
            { lang: 'Vietnamese:', text: 'Thành phố sống động với ánh đèn neon và crôm.', color: 'rgba(0, 212, 170, 0.9)' },
            { lang: 'Japanese:',    text: '都市はネオンとクロムで生き生きとしている。',       color: '#f9a8d4' },
            { lang: 'Chinese:',     text: '这座城市充满了霓虹灯和金属光泽。',                 color: '#fcd34d' },
            { lang: 'Korean:',      text: '도시는 네온과 크롬으로 생동감 있다.',               color: '#86efac' },
            { lang: 'Spanish:',     text: 'La ciudad está viva con neón y cromo.',            color: '#fb923c' },
            { lang: 'French:',      text: 'La ville est vivante avec du néon et du chrome.',  color: '#c4b5fd' },
        ];
        let twIdx = 0;

        function runTypewriter() {
            twIdx = (twIdx + 1) % translations.length;
            const t = translations[twIdx];

            // Fade out current line
            typewriterLine.style.opacity = '0';
            typewriterLine.style.transform = 'translateY(4px)';
            typewriterLine.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

            setTimeout(() => {
                typewriterLang.textContent = t.lang;
                typewriterText.textContent = t.text;
                typewriterLine.style.color = t.color;

                // Fade in
                typewriterLine.style.opacity = '1';
                typewriterLine.style.transform = 'translateY(0)';
            }, 320);
        }

        setInterval(runTypewriter, 2800);
    }

    // ── 9. Stats Counter Animation ──
    const statNumbers = document.querySelectorAll('.stat-number[data-target]');

    const counterObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-target'), 10);
                    let start = 0;
                    const duration = 1200;
                    const step = (timestamp) => {
                        if (!start) start = timestamp;
                        const progress = Math.min((timestamp - start) / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
                        el.textContent = Math.floor(eased * target) + '+';
                        if (progress < 1) requestAnimationFrame(step);
                        else el.textContent = target + '+';
                    };
                    requestAnimationFrame(step);
                    counterObserver.unobserve(el);
                }
            });
        },
        { threshold: 0.5 }
    );

    statNumbers.forEach(el => counterObserver.observe(el));

    // ── 10. Scroll-to-top Button ──
    const scrollTopBtn = document.getElementById('scroll-top');

    function handleScrollTop() {
        if (!scrollTopBtn) return;
        scrollTopBtn.classList.toggle('visible', window.scrollY > 400);
    }

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

});
