// ═══════════════════════════════════════════════════════════════════
// EvaMusic — In-App Notification Panel (notification-panel.js)
// ═══════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    // ── Styles ────────────────────────────────────────────────────
    const STYLES = `
    /* Bell button in music bar */
    #evaNotifBell {
        background: none;
        border: none;
        color: rgba(255,255,255,0.55);
        font-size: 17px;
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        flex-shrink: 0;
        position: relative;
        -webkit-tap-highlight-color: transparent;
        transition: color 0.2s;
    }
    #evaNotifBell:active { color: #1DB954; }
    #evaNotifBell .notif-dot {
        position: absolute;
        top: 4px; right: 4px;
        width: 7px; height: 7px;
        background: #1DB954;
        border-radius: 50%;
        border: 1.5px solid #181818;
        display: none;
    }
    #evaNotifBell .notif-dot.show { display: block; }

    /* Backdrop */
    #evaNotifBackdrop {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0);
        z-index: 1100;
        display: none;
        transition: background 0.3s ease;
    }
    #evaNotifBackdrop.open {
        background: rgba(0,0,0,0.55);
    }

    /* Panel */
    #evaNotifPanel {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 1101;
        background: #111;
        border-bottom-left-radius: 20px;
        border-bottom-right-radius: 20px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.7);
        transform: translateY(-110%);
        transition: transform 0.35s cubic-bezier(0.32,0.72,0,1);
        overflow: hidden;
        max-height: 85vh;
        overflow-y: auto;
        padding-top: env(safe-area-inset-top, 0px);
        -webkit-overflow-scrolling: touch;
    }
    #evaNotifPanel.open {
        transform: translateY(0);
    }

    /* Panel header */
    .enp-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 18px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .enp-header-title {
        font-size: 14px;
        font-weight: 700;
        color: #fff;
        letter-spacing: 0.2px;
    }
    .enp-header-actions {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .enp-clear-btn {
        background: none;
        border: none;
        color: rgba(255,255,255,0.35);
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 10px;
        -webkit-tap-highlight-color: transparent;
        transition: color 0.2s, background 0.2s;
    }
    .enp-clear-btn:active {
        color: #fff;
        background: rgba(255,255,255,0.08);
    }
    .enp-close-btn {
        background: rgba(255,255,255,0.08);
        border: none;
        color: rgba(255,255,255,0.6);
        font-size: 13px;
        width: 28px; height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        transition: background 0.2s, color 0.2s;
    }
    .enp-close-btn:active {
        background: rgba(255,255,255,0.18);
        color: #fff;
    }

    /* Now Playing card */
    .enp-now-playing {
        margin: 12px 14px;
        background: linear-gradient(135deg, #1a2a1a 0%, #181f18 100%);
        border: 1px solid rgba(29,185,84,0.2);
        border-radius: 14px;
        padding: 14px;
        position: relative;
        overflow: hidden;
    }
    .enp-now-playing::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse at top left, rgba(29,185,84,0.12) 0%, transparent 65%);
        pointer-events: none;
    }
    .enp-np-label {
        font-size: 10px;
        font-weight: 700;
        color: #1DB954;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .enp-np-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .enp-np-thumb {
        width: 48px; height: 48px;
        border-radius: 8px;
        object-fit: cover;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .enp-np-info { flex: 1; min-width: 0; }
    .enp-np-title {
        font-size: 14px;
        font-weight: 700;
        color: #fff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 3px;
    }
    .enp-np-artist {
        font-size: 12px;
        color: rgba(255,255,255,0.45);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .enp-np-play {
        width: 38px; height: 38px;
        border-radius: 50%;
        background: #1DB954;
        border: none;
        color: #000;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        flex-shrink: 0;
        -webkit-tap-highlight-color: transparent;
        box-shadow: 0 2px 10px rgba(29,185,84,0.4);
        transition: transform 0.1s, background 0.2s;
    }
    .enp-np-play:active { transform: scale(0.9); }

    /* Progress bar */
    .enp-progress-wrap {
        margin-bottom: 10px;
    }
    .enp-progress-bar {
        width: 100%;
        height: 3px;
        background: rgba(255,255,255,0.12);
        border-radius: 3px;
        cursor: pointer;
        margin-bottom: 5px;
        position: relative;
    }
    .enp-progress-fill {
        height: 100%;
        background: #1DB954;
        border-radius: 3px;
        width: 0%;
        transition: width 0.1s linear;
        pointer-events: none;
    }
    .enp-progress-times {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        color: rgba(255,255,255,0.3);
    }

    /* Controls row */
    .enp-controls {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .enp-ctrl {
        background: none;
        border: none;
        color: rgba(255,255,255,0.5);
        font-size: 16px;
        width: 36px; height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border-radius: 50%;
        -webkit-tap-highlight-color: transparent;
        transition: color 0.15s, background 0.15s;
    }
    .enp-ctrl:active {
        color: #fff;
        background: rgba(255,255,255,0.1);
    }
    .enp-ctrl.active { color: #1DB954; }

    /* Empty now playing state */
    .enp-np-empty {
        text-align: center;
        padding: 20px 14px;
        color: rgba(255,255,255,0.25);
        font-size: 13px;
    }
    .enp-np-empty i {
        display: block;
        font-size: 28px;
        margin-bottom: 8px;
        color: rgba(255,255,255,0.12);
    }

    /* Notifications list */
    .enp-section-label {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255,255,255,0.3);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 4px 18px 8px;
    }
    .enp-list {
        padding: 0 14px 8px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .enp-item {
        display: flex;
        align-items: flex-start;
        gap: 11px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 11px 13px;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        transition: background 0.15s;
        position: relative;
        overflow: hidden;
    }
    .enp-item:active { background: rgba(255,255,255,0.08); }
    .enp-item.unread::after {
        content: '';
        position: absolute;
        top: 12px; right: 12px;
        width: 6px; height: 6px;
        background: #1DB954;
        border-radius: 50%;
    }
    .enp-item-icon {
        width: 32px; height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .enp-icon-green  { background: rgba(29,185,84,0.15);  color: #1DB954; }
    .enp-icon-blue   { background: rgba(59,130,246,0.15); color: #60a5fa; }
    .enp-icon-purple { background: rgba(168,85,247,0.15); color: #c084fc; }
    .enp-icon-orange { background: rgba(251,146,60,0.15); color: #fb923c; }
    .enp-icon-red    { background: rgba(239,68,68,0.15);  color: #f87171; }

    .enp-item-body { flex: 1; min-width: 0; }
    .enp-item-title {
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        margin-bottom: 2px;
        padding-right: 14px;
    }
    .enp-item-text {
        font-size: 12px;
        color: rgba(255,255,255,0.4);
        line-height: 1.4;
    }
    .enp-item-time {
        font-size: 10px;
        color: rgba(255,255,255,0.22);
        margin-top: 4px;
    }

    /* Empty notifications */
    .enp-empty {
        text-align: center;
        padding: 24px 18px 28px;
        color: rgba(255,255,255,0.22);
        font-size: 13px;
    }
    .enp-empty i {
        display: block;
        font-size: 32px;
        margin-bottom: 10px;
        color: rgba(255,255,255,0.1);
    }

    /* Bottom padding */
    .enp-bottom-pad { height: 16px; }

    /* Swipe handle */
    .enp-handle {
        width: 36px; height: 4px;
        background: rgba(255,255,255,0.15);
        border-radius: 2px;
        margin: 10px auto 0;
    }
    `;

    // ── State ─────────────────────────────────────────────────────
    let _notifications = [];
    let _unreadCount   = 0;
    let _isOpen        = false;

    // ── Default notifications on first load ───────────────────────
    function _defaultNotifs() {
        return [
            {
                id:    'n_welcome',
                icon:  'fa-music',
                color: 'green',
                title: 'Welcome to EvaMusic',
                text:  'Your personal music player is ready. Tap any song to start.',
                time:  'Just now',
                unread: true,
                action: () => {}
            },
            {
                id:    'n_trending',
                icon:  'fa-fire',
                color: 'orange',
                title: 'Trending today',
                text:  'New hits added to your trending feed.',
                time:  '2m ago',
                unread: true,
                action: () => { window.location.href = '/trending'; }
            }
        ];
    }

    // ── Create DOM ────────────────────────────────────────────────
    function _inject() {
        // Styles
        const styleEl = document.createElement('style');
        styleEl.textContent = STYLES;
        document.head.appendChild(styleEl);

        // Backdrop
        const backdrop = document.createElement('div');
        backdrop.id = 'evaNotifBackdrop';
        backdrop.addEventListener('click', close);
        document.body.appendChild(backdrop);

        // Panel
        const panel = document.createElement('div');
        panel.id = 'evaNotifPanel';
        document.body.appendChild(panel);

        // Bell button — inject into music bar
        _injectBell();

        // Load saved notifications
        _loadNotifs();
        _render();

        // Watch for music bar DOM appearing (SPA swaps)
        const mo = new MutationObserver(() => _injectBell());
        mo.observe(document.body, { childList: true, subtree: true });
    }

    function _injectBell() {
        if (document.getElementById('evaNotifBell')) return;
        const btns = document.querySelector('.music-bar-btns');
        if (!btns) return;

        const bell = document.createElement('button');
        bell.id = 'evaNotifBell';
        bell.title = 'Notifications';
        bell.innerHTML = '<i class="fas fa-bell"></i><span class="notif-dot"></span>';
        bell.addEventListener('click', (e) => { e.stopPropagation(); toggle(); });

        btns.insertBefore(bell, btns.firstChild);
        _syncDot();
    }

    // ── Render panel content ──────────────────────────────────────
    function _render() {
        const panel = document.getElementById('evaNotifPanel');
        if (!panel) return;

        const p = window.player;
        const song = p ? p.currentSong : null;

        panel.innerHTML = `
            <div class="enp-handle"></div>
            <div class="enp-header">
                <div class="enp-header-title">Notifications</div>
                <div class="enp-header-actions">
                    ${_notifications.length ? '<button class="enp-clear-btn" id="enpClearBtn">Clear all</button>' : ''}
                    <button class="enp-close-btn" id="enpCloseBtn"><i class="fas fa-times"></i></button>
                </div>
            </div>

            ${_renderNowPlaying(song)}

            ${_renderList()}

            <div class="enp-bottom-pad"></div>
        `;

        // Events
        const closeBtn = document.getElementById('enpCloseBtn');
        if (closeBtn) closeBtn.addEventListener('click', close);

        const clearBtn = document.getElementById('enpClearBtn');
        if (clearBtn) clearBtn.addEventListener('click', _clearAll);

        _bindNowPlayingControls();
        _bindProgressSeek();
        _bindNotifItems();
    }

    function _renderNowPlaying(song) {
        if (!song) {
            return `
            <div class="enp-now-playing">
                <div class="enp-np-label">Now Playing</div>
                <div class="enp-np-empty">
                    <i class="fas fa-headphones"></i>
                    Select a song to start playing
                </div>
            </div>`;
        }

        const p       = window.player;
        const title   = p ? p.getTitle(song)   : (song.title  || 'Unknown');
        const artist  = p ? p.getArtist(song)  : (song.artist || 'Unknown');
        const imgUrl  = p ? p.getImageUrl(song) : (song.image  || '/static/images/default-album.png');
        const playing = p ? p.isPlaying : false;
        const isShuffle = p ? p.isShuffle   : false;
        const repeat    = p ? p.repeatMode  : 0;

        const repeatIcons = ['fa-redo', 'fa-redo', 'fa-redo-alt'];
        const repeatIcon  = repeatIcons[repeat] || 'fa-redo';

        return `
        <div class="enp-now-playing">
            <div class="enp-np-label">▶ Now Playing</div>
            <div class="enp-np-row">
                <img class="enp-np-thumb" id="enpThumb" src="${imgUrl}"
                     onerror="this.src='/static/images/default-album.png'" alt="">
                <div class="enp-np-info">
                    <div class="enp-np-title" id="enpTitle">${title}</div>
                    <div class="enp-np-artist" id="enpArtist">${artist}</div>
                </div>
                <button class="enp-np-play" id="enpPlayBtn">
                    <i class="fas ${playing ? 'fa-pause' : 'fa-play'}" id="enpPlayIcon"></i>
                </button>
            </div>
            <div class="enp-progress-wrap">
                <div class="enp-progress-bar" id="enpProgressBar">
                    <div class="enp-progress-fill" id="enpProgressFill"></div>
                </div>
                <div class="enp-progress-times">
                    <span id="enpCurrentTime">0:00</span>
                    <span id="enpTotalTime">0:00</span>
                </div>
            </div>
            <div class="enp-controls">
                <button class="enp-ctrl ${isShuffle ? 'active' : ''}" id="enpShuffle" title="Shuffle">
                    <i class="fas fa-random"></i>
                </button>
                <button class="enp-ctrl" id="enpPrev" title="Previous">
                    <i class="fas fa-step-backward"></i>
                </button>
                <button class="enp-ctrl" id="enpNext" title="Next">
                    <i class="fas fa-step-forward"></i>
                </button>
                <button class="enp-ctrl ${repeat ? 'active' : ''}" id="enpRepeat" title="Repeat">
                    <i class="fas ${repeatIcon}"></i>
                </button>
            </div>
        </div>`;
    }

    function _renderList() {
        if (!_notifications.length) {
            return `
            <div class="enp-empty">
                <i class="fas fa-bell-slash"></i>
                No notifications yet
            </div>`;
        }
        const items = _notifications.map(n => `
            <div class="enp-item ${n.unread ? 'unread' : ''}" data-notif-id="${n.id}">
                <div class="enp-item-icon enp-icon-${n.color || 'green'}">
                    <i class="fas ${n.icon || 'fa-bell'}"></i>
                </div>
                <div class="enp-item-body">
                    <div class="enp-item-title">${n.title}</div>
                    <div class="enp-item-text">${n.text}</div>
                    <div class="enp-item-time">${n.time || ''}</div>
                </div>
            </div>
        `).join('');

        return `
            <div class="enp-section-label">Recent</div>
            <div class="enp-list">${items}</div>
        `;
    }

    // ── Bind controls ─────────────────────────────────────────────
    function _bindNowPlayingControls() {
        const p = window.player;
        if (!p) return;

        const playBtn  = document.getElementById('enpPlayBtn');
        const prevBtn  = document.getElementById('enpPrev');
        const nextBtn  = document.getElementById('enpNext');
        const shuffle  = document.getElementById('enpShuffle');
        const repeat   = document.getElementById('enpRepeat');

        if (playBtn) playBtn.addEventListener('click', () => {
            p.togglePlay();
            setTimeout(_syncPlayState, 100);
        });
        if (prevBtn) prevBtn.addEventListener('click', () => p.previous());
        if (nextBtn) nextBtn.addEventListener('click', () => p.next());
        if (shuffle) shuffle.addEventListener('click', () => {
            p.toggleShuffle();
            shuffle.classList.toggle('active', p.isShuffle);
        });
        if (repeat) repeat.addEventListener('click', () => {
            p.toggleRepeat();
            repeat.classList.toggle('active', p.repeatMode > 0);
        });

        // Sync from audio events
        p.audio.addEventListener('play',  _syncPlayState);
        p.audio.addEventListener('pause', _syncPlayState);
        p.audio.addEventListener('timeupdate', _syncProgress);
    }

    function _syncPlayState() {
        const p    = window.player;
        const icon = document.getElementById('enpPlayIcon');
        if (icon && p) icon.className = `fas ${p.isPlaying ? 'fa-pause' : 'fa-play'}`;
    }

    function _syncProgress() {
        const p = window.player;
        if (!p || !p.audio.duration) return;
        const pct  = (p.audio.currentTime / p.audio.duration) * 100;
        const fill = document.getElementById('enpProgressFill');
        const cur  = document.getElementById('enpCurrentTime');
        const tot  = document.getElementById('enpTotalTime');
        if (fill) fill.style.width = pct + '%';
        if (cur)  cur.textContent  = _fmt(p.audio.currentTime);
        if (tot)  tot.textContent  = _fmt(p.audio.duration);
    }

    function _bindProgressSeek() {
        const bar = document.getElementById('enpProgressBar');
        if (!bar || !window.player) return;
        bar.addEventListener('click', (e) => {
            const rect = bar.getBoundingClientRect();
            window.player.seek((e.clientX - rect.left) / rect.width);
        });
    }

    function _bindNotifItems() {
        document.querySelectorAll('.enp-item[data-notif-id]').forEach(el => {
            el.addEventListener('click', () => {
                const id = el.dataset.notifId;
                const n  = _notifications.find(x => x.id === id);
                if (n) {
                    n.unread = false;
                    _syncUnread();
                    if (typeof n.action === 'function') { n.action(); close(); }
                    _render();
                }
            });
        });
    }

    function _fmt(s) {
        if (!s || isNaN(s)) return '0:00';
        return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    }

    // ── Open / Close / Toggle ─────────────────────────────────────
    function open() {
        _isOpen = true;
        _render();
        const panel    = document.getElementById('evaNotifPanel');
        const backdrop = document.getElementById('evaNotifBackdrop');
        if (backdrop) { backdrop.style.display = 'block'; requestAnimationFrame(() => backdrop.classList.add('open')); }
        if (panel)    requestAnimationFrame(() => panel.classList.add('open'));
        // Mark all as read after 1s
        setTimeout(() => { _notifications.forEach(n => n.unread = false); _syncUnread(); }, 1000);
    }

    function close() {
        _isOpen = false;
        const panel    = document.getElementById('evaNotifPanel');
        const backdrop = document.getElementById('evaNotifBackdrop');
        if (panel)    panel.classList.remove('open');
        if (backdrop) {
            backdrop.classList.remove('open');
            setTimeout(() => { backdrop.style.display = 'none'; }, 300);
        }
    }

    function toggle() { _isOpen ? close() : open(); }

    // ── Notifications management ──────────────────────────────────
    function _clearAll() {
        _notifications = [];
        _unreadCount   = 0;
        _saveNotifs();
        _syncDot();
        _render();
    }

    function _syncUnread() {
        _unreadCount = _notifications.filter(n => n.unread).length;
        _saveNotifs();
        _syncDot();
    }

    function _syncDot() {
        const dot = document.querySelector('#evaNotifBell .notif-dot');
        if (dot) dot.classList.toggle('show', _unreadCount > 0);
    }

    function _saveNotifs() {
        try { localStorage.setItem('evamusic_notifs', JSON.stringify(_notifications)); } catch(e) {}
    }

    function _loadNotifs() {
        try {
            const saved = localStorage.getItem('evamusic_notifs');
            _notifications = saved ? JSON.parse(saved) : _defaultNotifs();
        } catch(e) {
            _notifications = _defaultNotifs();
        }
        _unreadCount = _notifications.filter(n => n.unread).length;
    }

    // ── Public API: push a notification ──────────────────────────
    // Usage: window.EvaNotif.push({ title, text, icon, color, action })
    function push(opts) {
        const n = {
            id:     'n_' + Date.now(),
            icon:   opts.icon   || 'fa-bell',
            color:  opts.color  || 'green',
            title:  opts.title  || 'EvaMusic',
            text:   opts.text   || '',
            time:   'Just now',
            unread: true,
            action: opts.action || null
        };
        _notifications.unshift(n);
        if (_notifications.length > 30) _notifications.pop();
        _syncUnread();
        _saveNotifs();
        if (_isOpen) _render();
    }

    // ── Hook into player events to auto-push notifications ───────
    function _hookPlayer() {
        const p = window.player;
        if (!p) return;

        // Song change → update now playing card live
        const _origUpdateBar = p._updateBarUI.bind(p);
        p._updateBarUI = function(song) {
            _origUpdateBar(song);
            if (_isOpen) {
                // Re-render just the now-playing section
                const np = document.querySelector('.enp-now-playing');
                if (np) {
                    np.outerHTML = _renderNowPlaying(song);
                    _bindNowPlayingControls();
                    _bindProgressSeek();
                }
            }
        };

        // Favorite added → push notification
        const _origFav = p.toggleFavorite.bind(p);
        p.toggleFavorite = async function(songOverride, btnEl) {
            await _origFav(songOverride, btnEl);
            const song = songOverride || p.currentSong;
            if (song) {
                push({
                    icon:  'fa-heart',
                    color: 'red',
                    title: 'Added to Favorites',
                    text:  (p.getTitle ? p.getTitle(song) : song.title || 'Song') + ' saved to your favorites.'
                });
            }
        };
    }

    // ── Swipe-down-to-close on panel ─────────────────────────────
    function _initSwipe() {
        const panel = document.getElementById('evaNotifPanel');
        if (!panel) return;
        let startY = 0, dragging = false;
        panel.addEventListener('touchstart', (e) => {
            if (panel.scrollTop > 0) return;
            startY   = e.touches[0].clientY;
            dragging = true;
        }, { passive: true });
        panel.addEventListener('touchmove', (e) => {
            if (!dragging) return;
            const dy = e.touches[0].clientY - startY;
            if (dy > 0) panel.style.transform = `translateY(${dy}px)`;
        }, { passive: true });
        panel.addEventListener('touchend', (e) => {
            if (!dragging) return;
            dragging = false;
            const dy = e.changedTouches[0].clientY - startY;
            panel.style.transform = '';
            if (dy > 80) close();
        });
    }

    // ── Init ──────────────────────────────────────────────────────
    function _init() {
        _inject();
        _initSwipe();

        // Hook player after it's ready
        if (window.player) {
            _hookPlayer();
        } else {
            const iv = setInterval(() => {
                if (window.player) { _hookPlayer(); clearInterval(iv); }
            }, 150);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

    // ── Export ────────────────────────────────────────────────────
    window.EvaNotif = { push, open, close, toggle };

})();
