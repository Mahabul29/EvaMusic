// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic SPA Navigation — keeps audio alive, injects page styles on swap
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    const HARD_NAV   = ['/static/', '/api/', 'http://', 'https://'];
    const SPA_STYLE  = 'spa-page-style'; // attribute marker on injected <style> tags

    // ── Inject <style> tags from the fetched page's <head> ──────────────────
    function _injectStyles(newDoc) {
        // Remove previously SPA-injected styles
        document.querySelectorAll(`style[${SPA_STYLE}]`).forEach(s => s.remove());

        // Grab every <style> from the new page's <head> and <body>
        newDoc.querySelectorAll('style').forEach(s => {
            const clone = document.createElement('style');
            clone.textContent = s.textContent;
            clone.setAttribute(SPA_STYLE, '1');
            document.head.appendChild(clone);
        });
    }

    // ── Swap page content ────────────────────────────────────────────────────
    async function navigateTo(url, pushState = true) {
        if (!url || url === '#') return;
        if (url === window.location.pathname + window.location.search) return;

        try {
            const res  = await fetch(url, { headers: { 'X-SPA': '1' } });
            const html = await res.text();

            const parser  = new DOMParser();
            const newDoc  = parser.parseFromString(html, 'text/html');
            const newMain = newDoc.querySelector('.main-content');
            const curMain = document.querySelector('.main-content');

            if (!newMain || !curMain) { window.location.href = url; return; }

            // 1. Inject styles BEFORE swapping content
            _injectStyles(newDoc);

            // 2. Swap content
            curMain.innerHTML = newMain.innerHTML;

            // 3. Update <title>
            const newTitle = newDoc.querySelector('title');
            if (newTitle) document.title = newTitle.textContent;

            // 4. Push history
            if (pushState) history.pushState({ url }, '', url);

            // 5. Update bottom nav
            _updateNav(url);

            // 6. Re-execute inline <script> tags in swapped content
            _execScripts(curMain);

            // 7. Refresh player queue
            if (window.__evaPlayerInstance) {
                window.__evaPlayerInstance.refreshQueueFromDOM();
            }

            // 8. Scroll to top
            window.scrollTo(0, 0);

        } catch (err) {
            console.warn('[SPA] fetch failed, hard navigating:', err);
            window.location.href = url;
        }
    }

    // Re-execute <script> tags injected via innerHTML
    function _execScripts(container) {
        container.querySelectorAll('script').forEach(oldScript => {
            const s = document.createElement('script');
            [...oldScript.attributes].forEach(a => s.setAttribute(a.name, a.value));
            s.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(s, oldScript);
        });
    }

    // Update bottom nav active state
    function _updateNav(url) {
        const path = url.split('?')[0];
        document.querySelectorAll('.nav-item').forEach(item => {
            const href = item.getAttribute('href');
            const active =
                href === path ||
                (href === '/home' && (path === '/' || path === '/home')) ||
                (href !== '/' && href !== '/home' && path.startsWith(href));
            item.classList.toggle('active', active);
        });
    }

    // ── Intercept link clicks ────────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        const a = e.target.closest('a[href]');
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href) return;
        if (HARD_NAV.some(p => href.startsWith(p))) return;
        if (a.target === '_blank') return;
        if (href.startsWith('mailto:') || href.startsWith('tel:')) return;
        if (a.hasAttribute('data-hard-nav')) return;
        e.preventDefault();
        navigateTo(href);
    }, true);

    // ── Handle browser back/forward ──────────────────────────────────────────
    window.addEventListener('popstate', function (e) {
        const url = e.state?.url || window.location.pathname + window.location.search;
        navigateTo(url, false);
    });

    // ── Intercept form submits (search) ──────────────────────────────────────
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.method?.toLowerCase() !== 'get') return;
        const action = form.getAttribute('action') || window.location.pathname;
        if (HARD_NAV.some(p => action.startsWith(p))) return;
        e.preventDefault();
        const params = new URLSearchParams(new FormData(form)).toString();
        navigateTo(action + (params ? '?' + params : ''));
    });

    // Init nav on first load
    _updateNav(window.location.pathname);

    console.log('[SPA] Navigation initialized');
})();
                                              
