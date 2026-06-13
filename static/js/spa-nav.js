// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic SPA Navigation — keeps audio alive across all page changes
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    // Pages that must do a real navigation (external, auth, etc.)
    const HARD_NAV = ['/static/', '/api/', 'http://', 'https://'];

    // ── Swap page content ────────────────────────────────────────────────────
    async function navigateTo(url, pushState = true) {
        if (!url || url === '#') return;

        // Don't re-navigate to same page
        if (url === window.location.pathname + window.location.search) return;

        try {
            const res  = await fetch(url, { headers: { 'X-SPA': '1' } });
            const html = await res.text();

            const parser  = new DOMParser();
            const newDoc  = parser.parseFromString(html, 'text/html');
            const newMain = newDoc.querySelector('.main-content');
            const curMain = document.querySelector('.main-content');

            if (!newMain || !curMain) {
                // Fallback: hard navigate
                window.location.href = url;
                return;
            }

            // Swap content
            curMain.innerHTML = newMain.innerHTML;

            // Update <title>
            const newTitle = newDoc.querySelector('title');
            if (newTitle) document.title = newTitle.textContent;

            // Push history
            if (pushState) history.pushState({ url }, '', url);

            // Update bottom nav active state
            _updateNav(url);

            // Re-run any inline <script> tags in the new content
            _execScripts(curMain);

            // Refresh song queue from new DOM
            if (window.__evaPlayerInstance) {
                window.__evaPlayerInstance.refreshQueueFromDOM();
            }

            // Scroll to top
            window.scrollTo(0, 0);

        } catch (err) {
            console.warn('[SPA] fetch failed, hard navigating:', err);
            window.location.href = url;
        }
    }

    // Re-execute <script> tags injected via innerHTML (browsers don't run them)
    function _execScripts(container) {
        container.querySelectorAll('script').forEach(oldScript => {
            const s = document.createElement('script');
            [...oldScript.attributes].forEach(a => s.setAttribute(a.name, a.value));
            s.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(s, oldScript);
        });
    }

    // Update bottom nav highlight
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

    // ── Intercept clicks ─────────────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        const a = e.target.closest('a[href]');
        if (!a) return;

        const href = a.getAttribute('href');
        if (!href) return;

        // Skip external / asset / special links
        if (HARD_NAV.some(p => href.startsWith(p))) return;
        if (a.target === '_blank') return;
        if (href.startsWith('mailto:') || href.startsWith('tel:')) return;
        if (a.hasAttribute('data-hard-nav')) return;

        // Skip category search links on search page — they update results inline
        // (let them go through SPA navigation normally)

        e.preventDefault();
        navigateTo(href);
    }, true); // capture phase so it fires before onclick

    // ── Handle browser back/forward ──────────────────────────────────────────
    window.addEventListener('popstate', function (e) {
        const url = e.state?.url || window.location.pathname + window.location.search;
        navigateTo(url, false);
    });

    // ── Handle search form submit ────────────────────────────────────────────
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.method?.toLowerCase() !== 'get') return;
        const action = form.getAttribute('action') || window.location.pathname;
        if (HARD_NAV.some(p => action.startsWith(p))) return;

        e.preventDefault();
        const params = new URLSearchParams(new FormData(form)).toString();
        const url    = action + (params ? '?' + params : '');
        navigateTo(url);
    });

    // Init nav state on first load
    _updateNav(window.location.pathname);

    console.log('[SPA] Navigation initialized');
})();
              
