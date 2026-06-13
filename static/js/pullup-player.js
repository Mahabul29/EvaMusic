// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic — Single Audio Engine (pullup-player.js)
// ═══════════════════════════════════════════════════════════════════════════════

console.log('[EvaPlayer] Script loading...');

class EvaPlayer {
    constructor() {
        if (window.__evaPlayerInstance) {
            console.log('[EvaPlayer] Instance already exists, reusing');
            return window.__evaPlayerInstance;
        }

        console.log('[EvaPlayer] Creating new instance');
        this.audio         = new Audio();
        this.audio.preload = 'metadata';
        this.currentSong   = null;
        this.isPlaying     = false;
        this.isShuffle     = false;
        this.repeatMode    = 0; // 0=off 1=all 2=one
        this.queue         = [];
        this.currentIndex  = 0;
        this._listenersAttached = false;
        this._favoritesCache    = null;
        this._seekTouching      = false;

        this.els = {
            musicBar:             document.getElementById('musicBar'),
            musicBarThumb:        document.getElementById('musicBarThumb'),
            musicBarTitle:        document.getElementById('musicBarTitle'),
            musicBarArtist:       document.getElementById('musicBarArtist'),
            musicBarPlayIcon:     document.getElementById('musicBarPlayIcon'),
            musicBarProgress:     document.getElementById('musicBarProgress'),
            musicBarProgressFill: document.getElementById('musicBarProgressFill'),
        };

        window.__evaPlayerInstance = this;

        // ── Bridge to legacy window._eva so any old code still works ──
        window._eva = {
            get audio()      { return window.__evaPlayerInstance.audio; },
            get current()    { return window.__evaPlayerInstance.currentSong; },
            get queue()      { return window.__evaPlayerInstance.queue; },
            get isShuffle()  { return window.__evaPlayerInstance.isShuffle; },
            set isShuffle(v) { window.__evaPlayerInstance.isShuffle = v; },
            get repeatMode() { return window.__evaPlayerInstance.repeatMode; },
            set repeatMode(v){ window.__evaPlayerInstance.repeatMode = v; },
            get isPlaying()  { return window.__evaPlayerInstance.isPlaying; }
        };

        this.init();

        // Try to restore last song (bar only, don't autoplay)
        this._restoreLastSong();

        console.log('[EvaPlayer] Initialized');
    }

    // ── URL / metadata helpers ─────────────────────────────────────────────────
    getAudioUrl(song) {
        if (!song) return '';
        return song.url || song.downloadUrl || song.media_url || song.audio_url ||
               song.download_url || song.stream_url || song.song_url || '';
    }
    getImageUrl(song) {
        if (!song) return '/static/images/default-album.png';
        let img = song.image || song.image_url || song.thumbnail || song.cover || '';
        if (Array.isArray(img)) img = img[img.length - 1] || img[0] || '';
        return img || '/static/images/default-album.png';
    }
    getTitle(song)  { return song ? (song.title  || song.name  || song.song  || 'Unknown') : 'Unknown'; }
    getArtist(song) { return song ? (song.artist || song.primaryArtists || song.singers || 'Unknown') : 'Unknown'; }
    getId(song)     { return song ? (song.id     || song.song_id || '') : ''; }

    // ── Init event listeners ───────────────────────────────────────────────────
    init() {
        if (this._listenersAttached) return;
        this._listenersAttached = true;

        // Bar progress seek
        this.els.musicBarProgress?.addEventListener('click', (e) => {
            e.stopPropagation();
            const rect = this.els.musicBarProgress.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });

        this.audio.addEventListener('timeupdate', () => this._onTimeUpdate());
        this.audio.addEventListener('ended',      () => this.handleEnded());
        this.audio.addEventListener('play',       () => {
            this.isPlaying = true;
            this._syncPlayIcons(true);
        });
        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this._syncPlayIcons(false);
        });
        this.audio.addEventListener('error', (e) => {
            console.error('[EvaPlayer] Audio error:', e, 'src:', this.audio.src);
            showToast('Failed to load audio', 'error');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space')                  { e.preventDefault(); this.togglePlay(); }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft'  && e.ctrlKey) this.previous();
        });

        this.refreshQueueFromDOM();
    }

    // ── Sync both bar icon + fullscreen player icon ────────────────────────────
    _syncPlayIcons(playing) {
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';
        // Mini bar
        if (this.els.musicBarPlayIcon) this.els.musicBarPlayIcon.className = `fas ${playing ? 'fa-pause' : 'fa-play'}`;
        // Full-screen overlay (if open)
        const npIcon = document.getElementById('npPlayIcon');
        if (npIcon) npIcon.className = `fas ${playing ? 'fa-pause' : 'fa-play'}`;
        // Legacy hook
        if (window._npUpdatePlayBtn) window._npUpdatePlayBtn(playing);
    }

    // ── timeupdate ─────────────────────────────────────────────────────────────
    _onTimeUpdate() {
        if (!this.audio.duration) return;
        const pct = (this.audio.currentTime / this.audio.duration) * 100;

        // Mini bar
        if (this.els.musicBarProgressFill) this.els.musicBarProgressFill.style.width = pct + '%';

        // Full-screen overlay
        if (!this._seekTouching) {
            const fill  = document.getElementById('npProgressFill');
            const thumb = document.getElementById('npProgressThumb');
            const cur   = document.getElementById('npCurrentTime');
            const tot   = document.getElementById('npTotalTime');
            if (fill)  fill.style.width  = pct + '%';
            if (thumb) thumb.style.left  = pct + '%';
            if (cur)   cur.textContent   = this._fmt(this.audio.currentTime);
            if (tot)   tot.textContent   = this._fmt(this.audio.duration);
        }

        // Legacy hook
        if (window._npOnTimeUpdate) window._npOnTimeUpdate(this.audio.currentTime, this.audio.duration);
    }

    _fmt(s) {
        if (!s || isNaN(s)) return '0:00';
        return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
    }

    // ── Refresh queue from DOM song cards ─────────────────────────────────────
    refreshQueueFromDOM() {
        const items = document.querySelectorAll('[data-song-id]');
        if (!items.length) return;
        const newQueue = [];
        items.forEach(item => {
            const id = item.dataset.songId;
            if (id) {
                newQueue.push({
                    id:     id,
                    title:  item.dataset.songTitle  || 'Unknown',
                    artist: item.dataset.songArtist || 'Unknown',
                    image:  item.dataset.songImage  || '/static/images/default-album.png',
                    url:    item.dataset.songUrl    || ''
                });
            }
        });
        if (newQueue.length) {
            const currentId = this.currentSong ? this.getId(this.currentSong) : null;
            this.queue = newQueue;
            if (currentId) {
                const idx = this.queue.findIndex(s => this.getId(s) === currentId);
                if (idx !== -1) this.currentIndex = idx;
            }
        }
    }

    // ── Core: play a song ──────────────────────────────────────────────────────
    async playSong(songId, songData = null) {
        console.log('[EvaPlayer] playSong called:', songId);

        if (!songData) {
            const idx = this.queue.findIndex(s => this.getId(s) === songId);
            if (idx !== -1) songData = this.queue[idx];
        }

        if (!songData || typeof songData !== 'object') {
            showToast('Song data not found', 'error');
            return;
        }

        this.currentSong  = songData;
        const idx = this.queue.findIndex(s => this.getId(s) === songId);
        if (idx !== -1) this.currentIndex = idx;
        else { this.queue.push(songData); this.currentIndex = this.queue.length - 1; }

        let audioUrl = this.getAudioUrl(songData);

        // Fetch fresh URL from API if missing
        if (!audioUrl && songId) {
            showToast('Fetching song…', 'info');
            try {
                const fresh = await fetch(`/api/song/${songId}`).then(r => r.json());
                if (fresh && this.getAudioUrl(fresh)) {
                    audioUrl = this.getAudioUrl(fresh);
                    this.currentSong = { ...songData, ...fresh };
                } else {
                    showToast('Song unavailable', 'error');
                    return;
                }
            } catch (e) {
                showToast('Failed to load song', 'error');
                return;
            }
        }

        if (!audioUrl) { showToast('No audio URL available', 'error'); return; }

        // Only reload src if it actually changed
        if (this.audio.src !== audioUrl) {
            this.audio.src = audioUrl;
            this.audio.load();
        }

        try {
            await this.audio.play();
            this.isPlaying = true;
            this._saveLastSong(this.currentSong);
            this._updateBarUI(this.currentSong);
            this._updateOverlayUI(this.currentSong);
            this.showMusicBar();
            showToast('▶ ' + this.getTitle(this.currentSong), 'success');
        } catch (err) {
            console.warn('[EvaPlayer] Autoplay blocked:', err);
            this.isPlaying = false;
            this._syncPlayIcons(false);
            this._updateBarUI(this.currentSong);
            this._updateOverlayUI(this.currentSong);
            this.showMusicBar();
            showToast('Tap ▶ to play', 'info');
        }
    }

    // ── Toggle play/pause ──────────────────────────────────────────────────────
    togglePlay() {
        if (!this.currentSong) {
            if (this.queue.length > 0) this.playSong(this.getId(this.queue[0]), this.queue[0]);
            else showToast('Select a song first', 'info');
            return;
        }
        if (this.isPlaying) this.audio.pause();
        else this.audio.play().catch(err => { console.error('[EvaPlayer] Resume failed:', err); showToast('Playback failed', 'error'); });
    }

    next() {
        if (!this.queue.length) return;
        if (this.isShuffle) { this.playRandom(); return; }
        if (this.currentIndex < this.queue.length - 1) {
            this.currentIndex++;
            this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]);
        } else if (this.repeatMode === 1) {
            this.currentIndex = 0;
            this.playSong(this.getId(this.queue[0]), this.queue[0]);
        } else {
            showToast('End of queue', 'info');
        }
    }

    previous() {
        if (!this.queue.length) return;
        if (this.audio.currentTime > 3) { this.audio.currentTime = 0; return; }
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]);
        }
    }

    playRandom() {
        if (this.queue.length <= 1) return;
        let newIdx;
        do { newIdx = Math.floor(Math.random() * this.queue.length); }
        while (newIdx === this.currentIndex && this.queue.length > 1);
        this.currentIndex = newIdx;
        this.playSong(this.getId(this.queue[newIdx]), this.queue[newIdx]);
    }

    handleEnded() {
        if (this.repeatMode === 2) { this.audio.currentTime = 0; this.audio.play().catch(() => {}); }
        else if (this.isShuffle)   this.playRandom();
        else if (this.currentIndex < this.queue.length - 1) this.next();
        else if (this.repeatMode === 1) { this.currentIndex = 0; this.playSong(this.getId(this.queue[0]), this.queue[0]); }
        else { this.isPlaying = false; this._syncPlayIcons(false); }
    }

    seek(percent) {
        if (!this.audio.duration || isNaN(this.audio.duration)) return;
        this.audio.currentTime = percent * this.audio.duration;
    }

    // ── UI updates ─────────────────────────────────────────────────────────────
    _updateBarUI(song) {
        if (!song) return;
        if (this.els.musicBarThumb)  this.els.musicBarThumb.src            = this.getImageUrl(song);
        if (this.els.musicBarTitle)  this.els.musicBarTitle.textContent    = this.getTitle(song);
        if (this.els.musicBarArtist) this.els.musicBarArtist.textContent   = this.getArtist(song);
        this._syncPlayIcons(this.isPlaying);
    }

    _updateOverlayUI(song) {
        if (!song) return;
        // Full-screen overlay elements (present when player overlay is open)
        const art    = document.getElementById('npAlbumArt');
        const title  = document.getElementById('npSongTitle');
        const artist = document.getElementById('npSongArtist');
        const bg     = document.getElementById('npBg');
        const label  = document.getElementById('npArtistLabel');
        const link   = document.getElementById('npViewArtist');
        if (art)    art.src              = this.getImageUrl(song);
        if (title)  title.textContent    = this.getTitle(song);
        if (artist) artist.textContent   = this.getArtist(song);
        if (bg)     bg.style.backgroundImage = `url('${this.getImageUrl(song)}')`;
        if (label)  label.textContent    = this.getArtist(song);
        if (link)   link.href            = `/search?q=${encodeURIComponent(this.getArtist(song))}`;
        // Legacy hook
        if (window._npUpdateSongUI) window._npUpdateSongUI(song);
    }

    showMusicBar() {
        if (this.els.musicBar) this.els.musicBar.classList.remove('hidden');
    }

    toggleShuffle() {
        this.isShuffle = !this.isShuffle;
        showToast(this.isShuffle ? 'Shuffle on' : 'Shuffle off', 'info');
    }

    toggleRepeat() {
        this.repeatMode = (this.repeatMode + 1) % 3;
        const modes = ['Repeat off', 'Repeat all', 'Repeat one'];
        showToast(modes[this.repeatMode], 'info');
    }

    // ── Favorites ──────────────────────────────────────────────────────────────
    async toggleFavorite(songOverride, btnEl) {
        const song   = songOverride || this.currentSong;
        if (!song) return;
        const songId = this.getId(song);
        if (btnEl) { btnEl.style.transform = 'scale(1.3)'; setTimeout(() => btnEl.style.transform = '', 200); }
        try {
            const res  = await fetch('/api/favorite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    song_id:   songId,
                    title:     this.getTitle(song),
                    artist:    this.getArtist(song),
                    album:     song.album    || '',
                    duration:  song.duration || '',
                    image_url: this.getImageUrl(song),
                    audio_url: this.getAudioUrl(song),
                    source:    'jiosaavn'
                })
            });
            const data = await res.json();
            if (data.success) {
                this._favoritesCache = null;
                const added = data.action === 'added';
                showToast(added ? '❤️ Added to favorites' : '💔 Removed from favorites', added ? 'success' : 'info');
                if (btnEl) {
                    const icon = btnEl.querySelector('i');
                    if (icon) icon.className = added ? 'fas fa-heart' : 'far fa-heart';
                    btnEl.classList.toggle('liked', added);
                }
                // Sync NP like button if open
                const npBtn = document.getElementById('npLikeBtn');
                if (npBtn) {
                    const npIcon = npBtn.querySelector('i');
                    if (npIcon) npIcon.className = added ? 'fas fa-heart' : 'far fa-heart';
                    npBtn.classList.toggle('liked', added);
                }
            }
        } catch(e) { showToast('Network error', 'error'); }
    }

    async checkFavoriteState(songId) {
        try {
            const res  = await fetch('/api/favorites');
            const favs = await res.json();
            this._favoritesCache = favs;
            const liked = favs.some(f => f.song_id === songId);
            const btn   = document.getElementById('npLikeBtn');
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) icon.className = liked ? 'fas fa-heart' : 'far fa-heart';
                btn.classList.toggle('liked', liked);
            }
            return liked;
        } catch(e) { return false; }
    }

    shareSong() {
        const song = this.currentSong;
        if (!song) return;
        const url = window.location.origin + '/player/' + this.getId(song);
        if (navigator.share) navigator.share({ title: this.getTitle(song), url });
        else navigator.clipboard.writeText(url).then(() => showToast('🔗 Link copied!', 'success'));
    }

    // ── Persistence ────────────────────────────────────────────────────────────
    _saveLastSong(song) {
        try { localStorage.setItem('evamusic_currentSong', JSON.stringify(song)); } catch(e) {}
    }

    _restoreLastSong() {
        try {
            const saved = localStorage.getItem('evamusic_currentSong');
            if (!saved) return;
            const song = JSON.parse(saved);
            // Only restore bar UI — do NOT autoplay
            this.currentSong = song;
            this._updateBarUI(song);
            this.showMusicBar();
        } catch(e) {}
    }

    formatTime(s) {
        if (!s || isNaN(s) || !isFinite(s)) return '0:00';
        return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
    }
}

// ── Create singleton ───────────────────────────────────────────────────────────
const player = new EvaPlayer();
window.player = player;

// ── Global convenience functions (used in HTML onclick= attributes) ────────────
function playSong(songId, songData)  { window.player.playSong(songId, songData); }
function barTogglePlay()             { window.player.togglePlay(); }
function togglePlay()                { window.player.togglePlay(); }
function barNext()                   { window.player.next(); }
function nextSong()                  { window.player.next(); }
function barPrev()                   { window.player.previous(); }
function previousSong()              { window.player.previous(); }
function barSeek(e)                  {
    if (!e) return;
    e.stopPropagation();
    const bar  = document.getElementById('musicBarProgress');
    if (!bar)  return;
    const rect = bar.getBoundingClientRect();
    window.player.seek((e.clientX - rect.left) / rect.width);
}
function expandPlayer(e) {
    if (e) e.stopPropagation();
    if (!window.player.currentSong) return;
    openPlayerOverlay(window.player.currentSong);
}

// ── Full-screen player OVERLAY (no page navigation) ───────────────────────────
// This replaces the old window.location.href = '/player/...' navigation.
// The overlay is injected into the DOM on first open and reused.

function openPlayerOverlay(song) {
    let overlay = document.getElementById('evaPlayerOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'evaPlayerOverlay';
        overlay.innerHTML = _buildOverlayHTML();
        document.body.appendChild(overlay);
        _initOverlayEvents(overlay);
    }
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    window.player._updateOverlayUI(song);
    window.player._syncPlayIcons(window.player.isPlaying);
    window.player.checkFavoriteState(window.player.getId(song));

    const dur = song.duration;
    const tot = document.getElementById('npTotalTime');
    if (tot && dur) tot.textContent = window.player._fmt(
        typeof dur === 'number' ? dur : parseInt(dur) || 0
    );
}

function closePlayerOverlay() {
    const overlay = document.getElementById('evaPlayerOverlay');
    if (!overlay) return;
    overlay.classList.remove('open');
    setTimeout(() => { overlay.style.display = 'none'; }, 350);
}

function _buildOverlayHTML() {
    return `
    <style>
    #evaPlayerOverlay {
        display: none;
        position: fixed; inset: 0; z-index: 9999;
        flex-direction: column;
        background: #121212;
        transform: translateY(100%);
        transition: transform 0.35s cubic-bezier(.4,0,.2,1);
        overflow-y: auto;
    }
    #evaPlayerOverlay.open { transform: translateY(0); }

    .np-bg {
        position: fixed; inset: 0;
        background-size: cover; background-position: center;
        filter: blur(60px) brightness(0.35); transform: scale(1.3);
        z-index: -1; transition: background-image 0.4s;
    }
    .np-container {
        position: relative; min-height: 100dvh;
        display: flex; flex-direction: column;
        padding: max(12px, env(safe-area-inset-top)) 24px max(16px, env(safe-area-inset-bottom));
        color: #fff; box-sizing: border-box;
    }
    .np-topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
    .np-topbar button { background:none; border:none; color:#fff; font-size:20px; width:44px; height:44px; display:flex; align-items:center; justify-content:center; cursor:pointer; }
    .np-topbar-title { font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#b3b3b3; }
    .np-art-wrapper { flex:1; display:flex; align-items:center; justify-content:center; min-height:0; padding:8px 0; }
    .np-album-art { width:min(70vw,280px); height:min(70vw,280px); max-height:32vh; border-radius:14px; object-fit:cover; box-shadow:0 24px 60px rgba(0,0,0,.55); }
    .np-info { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:14px; }
    .np-info-text { min-width:0; flex:1; }
    .np-info-text h2 { font-size:22px; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .np-info-text p  { font-size:15px; color:#b3b3b3; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .np-view-artist { display:inline-flex; align-items:center; gap:6px; margin-top:8px; font-size:12px; color:#b3b3b3; text-decoration:none; }
    .np-like-btn { flex-shrink:0; background:none; border:none; color:#b3b3b3; font-size:24px; width:44px; height:44px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:transform .2s; }
    .np-like-btn.liked { color:#ff4757; }
    .np-like-btn:active { transform:scale(1.25); }
    .np-progress-section { margin-bottom:12px; }
    .np-progress-bar { position:relative; height:4px; background:rgba(255,255,255,.2); border-radius:2px; cursor:pointer; touch-action:none; }
    .np-progress-fill { position:absolute; top:0; left:0; height:100%; width:0%; background:#1DB954; border-radius:2px; pointer-events:none; }
    .np-progress-thumb { position:absolute; top:50%; left:0%; width:12px; height:12px; background:#fff; border-radius:50%; transform:translate(-50%,-50%); box-shadow:0 1px 4px rgba(0,0,0,.4); pointer-events:none; }
    .np-time-row { display:flex; justify-content:space-between; font-size:12px; color:#b3b3b3; margin-top:8px; }
    .np-controls { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
    .np-control-btn { background:none; border:none; color:#fff; font-size:20px; width:48px; height:48px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:color .2s; }
    .np-control-btn.active { color:#1DB954; }
    .np-play-btn { width:68px; height:68px; border-radius:50%; background:#fff; color:#000; font-size:24px; display:flex; align-items:center; justify-content:center; border:none; cursor:pointer; transition:transform .2s; }
    .np-play-btn:active { transform:scale(.94); }
    .np-secondary { display:flex; justify-content:space-around; padding-top:10px; border-top:1px solid rgba(255,255,255,.08); }
    .np-secondary button { background:none; border:none; color:#b3b3b3; font-size:11px; font-weight:500; display:flex; flex-direction:column; align-items:center; gap:6px; cursor:pointer; padding:6px 4px; }
    .np-secondary button i { font-size:17px; }
    .np-secondary button:active { color:#1DB954; }
    </style>

    <div class="np-bg" id="npBg"></div>
    <div class="np-container">
        <div class="np-topbar">
            <button onclick="closePlayerOverlay()" aria-label="Close"><i class="fas fa-chevron-down"></i></button>
            <div class="np-topbar-title">Now Playing</div>
            <button onclick="showToast('More options coming soon!','info')" aria-label="More"><i class="fas fa-ellipsis-v"></i></button>
        </div>
        <div class="np-art-wrapper">
            <img id="npAlbumArt" class="np-album-art" src="/static/images/default-album.png" alt="">
        </div>
        <div class="np-info">
            <div class="np-info-text">
                <h2 id="npSongTitle">—</h2>
                <p  id="npSongArtist">—</p>
                <a  id="npViewArtist" class="np-view-artist" href="#"><i class="fas fa-user"></i> <span id="npArtistLabel">Artist</span></a>
            </div>
            <button class="np-like-btn" id="npLikeBtn" onclick="window.player.toggleFavorite(null, this)" aria-label="Favorite">
                <i class="far fa-heart"></i>
            </button>
        </div>
        <div class="np-progress-section">
            <div class="np-progress-bar" id="npProgressBar"
                 onclick="_npBarClick(event)"
                 ontouchstart="_npTouchStart(event)"
                 ontouchmove="_npTouchMove(event)"
                 ontouchend="_npTouchEnd(event)">
                <div class="np-progress-fill"  id="npProgressFill"></div>
                <div class="np-progress-thumb" id="npProgressThumb"></div>
            </div>
            <div class="np-time-row">
                <span id="npCurrentTime">0:00</span>
                <span id="npTotalTime">0:00</span>
            </div>
        </div>
        <div class="np-controls">
            <button class="np-control-btn" id="npShuffleBtn" onclick="_npToggleShuffle()" aria-label="Shuffle"><i class="fas fa-random"></i></button>
            <button class="np-control-btn" onclick="window.player.previous()" aria-label="Previous"><i class="fas fa-step-backward" style="font-size:24px"></i></button>
            <button class="np-play-btn"    onclick="window.player.togglePlay()" aria-label="Play/Pause"><i class="fas fa-play" id="npPlayIcon"></i></button>
            <button class="np-control-btn" onclick="window.player.next()" aria-label="Next"><i class="fas fa-step-forward" style="font-size:24px"></i></button>
            <button class="np-control-btn" id="npRepeatBtn" onclick="_npToggleRepeat()" aria-label="Repeat"><i class="fas fa-redo"></i></button>
        </div>
        <div class="np-secondary">
            <button onclick="showToast('Lyrics coming soon!','info')"><i class="fas fa-align-left"></i> Lyrics</button>
            <button onclick="showToast('Queue coming soon!','info')"><i class="fas fa-list-ul"></i> Queue</button>
            <button onclick="_npDownload()"><i class="fas fa-download"></i> Save</button>
            <button onclick="window.player.shareSong()"><i class="fas fa-share-alt"></i> Share</button>
            <button onclick="showToast('Sleep timer coming soon!','info')"><i class="fas fa-moon"></i> Sleep</button>
        </div>
    </div>`;
}

function _initOverlayEvents(overlay) {
    // Swipe down to close
    let startY = 0;
    overlay.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
    overlay.addEventListener('touchend',   e => {
        if (e.changedTouches[0].clientY - startY > 80) closePlayerOverlay();
    }, { passive: true });
}

// Overlay seek helpers
function _npBarClick(e) {
    const bar  = document.getElementById('npProgressBar');
    const rect = bar.getBoundingClientRect();
    window.player.seek((e.clientX - rect.left) / rect.width);
}
function _npTouchStart(e) { window.player._seekTouching = true; _npTouchMove(e); }
function _npTouchMove(e) {
    if (!window.player._seekTouching) return;
    e.preventDefault();
    const bar   = document.getElementById('npProgressBar');
    const rect  = bar.getBoundingClientRect();
    const pct   = Math.max(0, Math.min(1, (e.touches[0].clientX - rect.left) / rect.width));
    const fill  = document.getElementById('npProgressFill');
    const thumb = document.getElementById('npProgressThumb');
    const cur   = document.getElementById('npCurrentTime');
    if (fill)  fill.style.width = (pct * 100) + '%';
    if (thumb) thumb.style.left = (pct * 100) + '%';
    if (cur && window.player.audio.duration) cur.textContent = window.player._fmt(pct * window.player.audio.duration);
}
function _npTouchEnd(e) {
    const bar   = document.getElementById('npProgressBar');
    const rect  = bar.getBoundingClientRect();
    const pct   = Math.max(0, Math.min(1, (e.changedTouches[0].clientX - rect.left) / rect.width));
    window.player.seek(pct);
    window.player._seekTouching = false;
}
function _npToggleShuffle() {
    window.player.toggleShuffle();
    document.getElementById('npShuffleBtn')?.classList.toggle('active', window.player.isShuffle);
}
function _npToggleRepeat() {
    window.player.toggleRepeat();
    const btn  = document.getElementById('npRepeatBtn');
    const icon = btn?.querySelector('i');
    if (btn)  btn.classList.toggle('active', window.player.repeatMode > 0);
    if (icon) icon.className = window.player.repeatMode === 2 ? 'fas fa-redo-alt' : 'fas fa-redo';
}
function _npDownload() {
    const song = window.player.currentSong;
    if (!song) return;
    const url = window.player.getAudioUrl(song);
    if (!url) { showToast('Download not available', 'error'); return; }
    const a = document.createElement('a');
    a.href = url; a.download = (window.player.getTitle(song) || 'song') + '.mp3'; a.target = '_blank';
    document.body.appendChild(a); a.click(); a.remove();
    showToast('Download started', 'success');
}

// ── showToast (single definition) ─────────────────────────────────────────────
function showToast(message, type = 'info') {
    document.querySelectorAll('.eva-toast').forEach(t => t.remove());
    const t = document.createElement('div');
    t.className = `toast toast-${type} eva-toast`;
    t.textContent = message;
    document.body.appendChild(t);
    requestAnimationFrame(() => {
        t.style.opacity   = '1';
        t.style.transform = 'translateX(-50%) translateY(0)';
    });
    setTimeout(() => {
        t.style.opacity   = '0';
        t.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => t.remove(), 300);
    }, 2200);
}

// ── DOM ready: refresh queue ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    window.__evaPlayerInstance?.refreshQueueFromDOM();
});

console.log('[EvaPlayer] Script loaded successfully');
