/**
 * Civil Connection - Worker Slider & Mobile Menu Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Worker Slider Horizontal Scroll
    const workerSlider = document.getElementById('workerSlider');
    const prevBtn = document.querySelector('.nav-btn i.fa-chevron-left')?.parentElement;
    const nextBtn = document.querySelector('.nav-btn i.fa-chevron-right')?.parentElement;

    if (workerSlider && prevBtn && nextBtn) {
        // We override the inline onclick if needed, or just let them work.
        // Adding touch drag support for better mobile experience.
        let isDown = false;
        let startX;
        let scrollLeft;

        workerSlider.addEventListener('mousedown', (e) => {
            isDown = true;
            workerSlider.classList.add('active');
            startX = e.pageX - workerSlider.offsetLeft;
            scrollLeft = workerSlider.scrollLeft;
        });
        
        workerSlider.addEventListener('mouseleave', () => {
            isDown = false;
            workerSlider.classList.remove('active');
        });
        
        workerSlider.addEventListener('mouseup', () => {
            isDown = false;
            workerSlider.classList.remove('active');
        });
        
        workerSlider.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - workerSlider.offsetLeft;
            const walk = (x - startX) * 2; 
            workerSlider.scrollLeft = scrollLeft - walk;
        });
    }

    // 2. Mobile Menu Trigger
    const menuTrigger = document.getElementById('menuTrigger');
    const navMenu = document.querySelector('.nav-menu-desktop');
    
    if (menuTrigger && navMenu) {
        menuTrigger.addEventListener('click', () => {
            navMenu.classList.toggle('show-mobile');
            const icon = menuTrigger.querySelector('i');
            if (navMenu.classList.contains('show-mobile')) {
                icon.classList.replace('fa-bars', 'fa-xmark');
            } else {
                icon.classList.replace('fa-xmark', 'fa-bars');
            }
        });
    }

    // 3. Filter Tab Switching
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // Filter logic can be added here if dynamic
        });
    });

    console.log('Slider and UI scripts initialized.');
});
