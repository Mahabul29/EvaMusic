// UI Utilities
const UI = {
    init() {
        this.setupLazyLoading();
        this.setupInfiniteScroll();
    },
    
    setupLazyLoading() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    observer.unobserve(img);
                }
            });
        });
        images.forEach(img => observer.observe(img));
    },
    
    setupInfiniteScroll() {
        // For future pagination
    },
    
    showLoading() {
        document.body.classList.add('loading');
    },
    
    hideLoading() {
        document.body.classList.remove('loading');
    }
};

document.addEventListener('DOMContentLoaded', () => UI.init());
