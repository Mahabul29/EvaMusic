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
            // Always re-execute page scripts — page-specific functions
            // (playSong, removeFavorite, etc.) must re-register on every swap
            _execScripts(curMain, newDoc);
            _attachSongCards(curMain);

            // Refresh player state
            if (window.__evaPlayerInstance) {
                window.__evaPlayerInstance.refreshQueueFromDOM();
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

    function _execScripts(container, newDoc) {
        // Always re-execute ALL inline scripts from the new page
        // so page-specific functions re-register after every SPA swap
        const scripts = newDoc.querySelectorAll('.main-content script');
        scripts.forEach(oldScript => {
            // Skip external src scripts that are already loaded globally
            if (oldScript.src) return;

            const s = document.createElement('script');
            [...oldScript.attributes].forEach(a => s.setAttribute(a.name, a.value));
            s.textContent = oldScript.textContent;

            try {
                document.head.appendChild(s);
                document.head.removeChild(s);
            } catch (e) {
                console.warn('[SPA] Script execution failed:', e);
            }
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

    // Push initial state so popstate fires correctly on first back press
    history.replaceState(
        { url: window.location.pathname + window.location.search },
        '',
        window.location.pathname + window.location.search
    );

    window.addEventListener('popstate', function (e) {
        const url = (e.state && e.state.url)
            ? e.state.url
            : window.location.pathname + window.location.search;
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

    // Re-attach song card click handlers after SPA swap
    function _attachSongCards(container) {
        if (!container) container = document;

        // Generic: any element with data-song-id that isn't a song-row
        // (song-row clicks are handled by per-page scripts)
        container.querySelectorAll('.grid-item[data-song-id], .trending-card[data-song-id]').forEach(item => {
            const clone = item.cloneNode(true);
            item.parentNode.replaceChild(clone, item);
            clone.addEventListener('click', function(e) {
                if (e.target.closest('.queue-item-remove') ||
                    e.target.closest('.queue-item-drag')) return;
                e.preventDefault();
                const p = window.player || window.__evaPlayerInstance;
                if (!p) { showToast('Player not ready', 'error'); return; }
                p.playSong(this.dataset.songId, {
                    id:     this.dataset.songId,
                    title:  this.dataset.songTitle,
                    artist: this.dataset.songArtist,
                    image:  this.dataset.songImage,
                    url:    this.dataset.songUrl || ''
                });
            });
        });

        container.querySelectorAll('.heart-btn-standalone').forEach(btn => {
            const clone = btn.cloneNode(true);
            btn.parentNode.replaceChild(clone, btn);
            clone.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                e.stopImmediatePropagation();
                if (typeof handleLikeClick === 'function') handleLikeClick(e, this);
                return false;
            });
        });

        if (typeof initHeartStates === 'function') initHeartStates();
    }

    _updateNav(window.location.pathname);
    _attachSongCards(document.querySelector('.main-content'));
    console.log('[SPA] Navigation initialized');
})();
                    
