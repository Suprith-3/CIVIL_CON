// Component Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Dropdown initialization
    const dropdowns = document.querySelectorAll('.user-profile-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            // In a real app, this would show a menu
            console.log('Profile clicked');
        });
    });

    // Search Suggestions Placeholder logic
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', Utils.debounce((e) => {
            const query = e.target.value;
            if (query.length > 2) {
                console.log('Searching for:', query);
                // Here we would call API.get('/search?q=' + query)
            }
        }, 300));
    }
    // Worker Slider Logic
    const slider = document.getElementById('workerSlider');
    const prevBtn = document.getElementById('slidePrev');
    const nextBtn = document.getElementById('slideNext');

    if (slider && prevBtn && nextBtn) {
        const scrollAmount = 300;

        nextBtn.addEventListener('click', () => {
            slider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        prevBtn.addEventListener('click', () => {
            slider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        slider.addEventListener('scroll', () => {
            // Show/hide buttons based on scroll position
            prevBtn.style.display = slider.scrollLeft > 20 ? 'flex' : 'none';
            
            const maxScroll = slider.scrollWidth - slider.clientWidth;
            nextBtn.style.display = slider.scrollLeft >= maxScroll - 20 ? 'none' : 'flex';
        });
    }

    // Engineering Slider Logic
    const engSlider = document.getElementById('engSlider');
    const engPrevBtn = document.getElementById('engSlidePrev');
    const engNextBtn = document.getElementById('engSlideNext');

    if (engSlider && engPrevBtn && engNextBtn) {
        const scrollAmount = 300;

        engNextBtn.addEventListener('click', () => {
            engSlider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        engPrevBtn.addEventListener('click', () => {
            engSlider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        engSlider.addEventListener('scroll', () => {
            engPrevBtn.style.display = engSlider.scrollLeft > 20 ? 'flex' : 'none';
            const maxScroll = engSlider.scrollWidth - engSlider.clientWidth;
            engNextBtn.style.display = engSlider.scrollLeft >= maxScroll - 20 ? 'none' : 'flex';
        });
    }

    // Hero Dynamic Text Flicker (Alternating FUTURE / DREAM)
    const dynamicText = document.getElementById('dynamic-hero-text');
    if (dynamicText) {
        dynamicText.style.transition = 'opacity 0.3s ease';
        const words = ['FUTURE', 'DREAM'];
        let index = 0;
        setInterval(() => {
            dynamicText.style.opacity = '0';
            setTimeout(() => {
                index = (index + 1) % words.length;
                dynamicText.textContent = words[index];
                dynamicText.style.opacity = '1';
            }, 300);
        }, 3000);
    }

    console.log('Components initialized');
});
