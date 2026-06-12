// EvaMusic Bottom Navigation — client-side active state + bfcache-safe
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        const href = item.getAttribute('href');
        let isActive = false;

        if (href === currentPath) {
            isActive = true;
        } else if (href === '/home' && (currentPath === '/' || currentPath === '/home')) {
            isActive = true;
        } else if (href !== '/' && currentPath.startsWith(href)) {
            isActive = true;
        }

        item.classList.toggle('active', isActive);
    });
});
