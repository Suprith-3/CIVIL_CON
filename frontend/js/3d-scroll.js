gsap.registerPlugin(ScrollTrigger);

const sections = gsap.utils.toArray('section, .animate-section');
const scrollContainer = document.querySelector('.scroll-container');

if (sections.length > 0) {
    // Initial Setup
    sections.forEach((section, i) => {
        if (i !== 0) {
            gsap.set(section, {
                z: -1000,
                opacity: 0,
                visibility: 'hidden',
                rotateX: 45
            });
        } else {
            gsap.set(section, {
                z: 0,
                opacity: 1,
                visibility: 'visible',
                rotateX: 0
            });
        }
    });

    // Create scroll timeline with pinning
    if (sections.length > 0) {
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: ".scroll-container",
                start: "top top",
                end: "+=400%", // 400% of viewport height
                scrub: 1.5,
                pin: ".scene",
                anticipatePin: 1,
            }
        });

        sections.forEach((section, i) => {
            // First section is already visible
            if (i > 0) {
                // Entrance animation
                tl.to(section, {
                    z: 0,
                    opacity: 1,
                    rotateX: 0,
                    visibility: 'visible',
                    ease: "power2.inOut",
                    duration: 1
                }, i * 1.5);
            }

            // Exit animation (fade/fly out)
            if (i < sections.length - 1) {
                tl.to(section, {
                    z: 1500, // Fly towards camera
                    opacity: 0,
                    rotateX: -30,
                    ease: "power2.inOut",
                    duration: 1,
                    onStart: () => { section.classList.add('active'); },
                    onComplete: () => { gsap.set(section, { visibility: 'hidden' }); section.classList.remove('active'); }
                }, (i + 1) * 1.5 - 0.5);
            } else {
                // Last section stays visible or we handle final state
                tl.to(section, {
                    duration: 0.5,
                    onStart: () => { section.classList.add('active'); }
                });
            }
        });
    }

    // Parallax Mouse Effect
    document.addEventListener('mousemove', (e) => {
        const cards = document.querySelectorAll('.f-card-3d, .card');
        const { clientX, clientY } = e;
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;

        cards.forEach(card => {
            const depth = card.getAttribute('data-depth') || 0.05;
            const moveX = (clientX - centerX) * depth;
            const moveY = (clientY - centerY) * depth;

            gsap.to(card, {
                rotateY: moveX / 5,
                rotateX: -moveY / 5,
                x: moveX,
                y: moveY,
                duration: 0.8,
                ease: "power2.out"
            });
        });
    });
}

