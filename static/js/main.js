// Main App Logic
const App = {
    init() {
        this.setupServiceWorker();
        this.setupTheme();
    },
    
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then(reg => console.log('SW registered'))
                .catch(err => console.log('SW error:', err));
        }
    },
    
    setupTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
        }
    },
    
    toggleTheme() {
        document.body.classList.toggle('light-mode');
        const theme = document.body.classList.contains('light-mode') ? 'light' : 'dark';
        localStorage.setItem('theme', theme);
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
