// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic SPA Navigation — keeps audio alive, injects page styles on swap
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    const HARD_NAV  = ['/static/', '/api/', 'http://', 'https://'];
    const SPA_STYLE = 'spa-page-style';

    function _injectStyles(newDoc) {
        document.querySelectorAll(`style[${SPA_STYLE}]`).forEach(s => s.remove());
        newDoc.querySelectorAll('style').forEach(s => {
            const clone = document.createElement('style');
            clone.textContent = s.textContent;
            clone.setAttribute(SPA_STYLE, '1');
            document.head.appendChild(clone);
        });
    }

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

            _injectStyles(newDoc);
            curMain.innerHTML = newMain.innerHTML;

            const newTitle = newDoc.querySelector('title');
            if (newTitle) document.title = newTitle.textContent;

            if (pushState) history.pushState({ url }, '', url);

            _updateNav(url);
            _execScripts(curMain);

            // ── KEY FIX: refresh queue AND re-show bar after every navigation ──
            if (window.__evaPlayerInstance) {
                window.__evaPlayerInstance.refreshQueueFromDOM();
                // Re-show bar if a song is loaded (bar HTML is outside .main-content so it survives)
                if (window.__evaPlayerInstance.currentSong) {
                    window.__evaPlayerInstance.showMusicBar();
                    window.__evaPlayerInstance._updateBarUI(window.__evaPlayerInstance.currentSong);
                    window.__evaPlayerInstance._syncPlayIcons(window.__evaPlayerInstance.isPlaying);
                }
            }

            window.scrollTo(0, 0);

        } catch (err) {
            console.warn('[SPA] fetch failed, hard navigating:', err);
            window.location.href = url;
        }
    }

    function _execScripts(container) {
        container.querySelectorAll('script').forEach(oldScript => {
            const s = document.createElement('script');
            [...oldScript.attributes].forEach(a => s.setAttribute(a.name, a.value));
            s.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(s, oldScript);
        });
    }

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

    window.addEventListener('popstate', function (e) {
        const url = e.state?.url || window.location.pathname + window.location.search;
        navigateTo(url, false);
    });

    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.method?.toLowerCase() !== 'get') return;
        const action = form.getAttribute('action') || window.location.pathname;
        if (HARD_NAV.some(p => action.startsWith(p))) return;
        e.preventDefault();
        const params = new URLSearchParams(new FormData(form)).toString();
        navigateTo(action + (params ? '?' + params : ''));
    });

    _updateNav(window.location.pathname);
    console.log('[SPA] Navigation initialized');
})();
                
