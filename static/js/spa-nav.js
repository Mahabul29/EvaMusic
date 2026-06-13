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

    // FIX: Track executed scripts to prevent re-running
    const executedScripts = new Set();

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
            // FIX: Only execute NEW scripts, skip already executed ones
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

    // FIX: Safer script execution with error handling
    function _execScripts(container, newDoc) {
        // Get scripts from the NEW page content, not the current container
        const scripts = newDoc.querySelectorAll('.main-content script');
        scripts.forEach(oldScript => {
            // Skip if this script has already been executed
            const scriptKey = oldScript.textContent?.substring(0, 100) || '';
            if (executedScripts.has(scriptKey)) return;
            executedScripts.add(scriptKey);

            const s = document.createElement('script');
            // Copy attributes
            [...oldScript.attributes].forEach(a => {
                if (a.name !== 'src' || a.value) {
                    s.setAttribute(a.name, a.value);
                }
            });
            
            // Handle external scripts vs inline
            if (oldScript.src) {
                s.src = oldScript.src;
            } else {
                s.textContent = oldScript.textContent;
            }
            
            // Execute safely
            try {
                container.appendChild(s);
                // Remove after execution to keep DOM clean
                if (s.parentNode) s.parentNode.removeChild(s);
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

    // Re-attach song card click handlers after SPA swap
    function _attachSongCards(container) {
        if (!container) container = document;

        container.querySelectorAll('.grid-item[data-song-id]').forEach(item => {
            const clone = item.cloneNode(true);
            item.parentNode.replaceChild(clone, item);
            clone.addEventListener('click', function(e) {
                if (e.target.closest('.queue-item-remove') ||
                    e.target.closest('.queue-item-drag')) return;
                e.preventDefault();
                const songData = {
                    id:     this.dataset.songId,
                    title:  this.dataset.songTitle,
                    artist: this.dataset.songArtist,
                    image:  this.dataset.songImage,
                    url:    this.dataset.songUrl || ''
                };
                if (window.player && typeof window.player.playSong === 'function') {
                    window.player.playSong(songData.id, songData);
                } else if (typeof playSong === 'function') {
                    playSong(songData.id, songData);
                } else {
                    showToast('Player not ready', 'error');
                }
            });
        });

        container.querySelectorAll('.trending-card[data-song-id]').forEach(item => {
            const clone = item.cloneNode(true);
            item.parentNode.replaceChild(clone, item);
            clone.addEventListener('click', function(e) {
                e.preventDefault();
                const songData = {
                    id:     this.dataset.songId,
                    title:  this.dataset.songTitle,
                    artist: this.dataset.songArtist,
                    image:  this.dataset.songImage,
                    url:    this.dataset.songUrl || ''
                };
                if (window.player && typeof window.player.playSong === 'function') {
                    window.player.playSong(songData.id, songData);
                } else if (typeof playSong === 'function') {
                    playSong(songData.id, songData);
                } else {
                    showToast('Player not ready', 'error');
                }
            });
        });

        container.querySelectorAll('.heart-btn-standalone').forEach(btn => {
            const clone = btn.cloneNode(true);
            btn.parentNode.replaceChild(clone, btn);
            clone.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                e.stopImmediatePropagation();
                if (typeof handleLikeClick === 'function') {
                    handleLikeClick(e, this);
                }
                return false;
            });
        });

        if (typeof initHeartStates === 'function') {
            initHeartStates();
        }
    }

    _updateNav(window.location.pathname);
    _attachSongCards(document.querySelector('.main-content'));
    console.log('[SPA] Navigation initialized');
})();
        
