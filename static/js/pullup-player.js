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

        window.__evaPlayerInstance = this;

        // ── Bridge to legacy window._eva ──
        window._eva = {
            get audio()       { return window.__evaPlayerInstance.audio; },
            get current()     { return window.__evaPlayerInstance.currentSong; },
            get queue()       { return window.__evaPlayerInstance.queue; },
            get isShuffle()   { return window.__evaPlayerInstance.isShuffle; },
            set isShuffle(v)  { window.__evaPlayerInstance.isShuffle = v; },
            get repeatMode()  { return window.__evaPlayerInstance.repeatMode; },
            set repeatMode(v) { window.__evaPlayerInstance.repeatMode = v; },
            get isPlaying()   { return window.__evaPlayerInstance.isPlaying; }
        };

        this.init();
        this._restoreLastSong();

        console.log('[EvaPlayer] Initialized');
    }

    // ── Always fetch els fresh from DOM (never cache — SPA swaps content) ──
    get els() {
        return {
            musicBar:             document.getElementById('musicBar'),
            musicBarThumb:        document.getElementById('musicBarThumb'),
            musicBarTitle:        document.getElementById('musicBarTitle'),
            musicBarArtist:       document.getElementById('musicBarArtist'),
            musicBarPlayIcon:     document.getElementById('musicBarPlayIcon'),
            musicBarProgress:     document.getElementById('musicBarProgress'),
            musicBarProgressFill: document.getElementById('musicBarProgressFill'),
        };
    }

    // ── URL / metadata helpers ─────────────────────────────────────────────────

    getAudioUrl(song) {
        if (!song) return '';
        const URL_KEYS = ['url', 'downloadUrl', 'download_url', 'media_url',
                          'audio_url', 'stream_url', 'song_url', 'link'];

        const pick = (obj) => {
            if (!obj || typeof obj !== 'object') return '';
            for (const key of URL_KEYS) {
                const val = obj[key];
                if (!val) continue;
                if (Array.isArray(val) && val.length) {
                    const entry = val[val.length - 1];
                    const u = (typeof entry === 'object')
                        ? (entry.url || entry.link || '')
                        : (typeof entry === 'string' ? entry : '');
                    if (u && u.startsWith('http')) return u;
                }
                if (typeof val === 'string' && val.startsWith('http')) return val;
            }
            return '';
        };

        let url = pick(song);
        if (url) return url;

        for (const wrapper of ['data', 'song', 'songs', 'result']) {
            const inner = song[wrapper];
            url = Array.isArray(inner) ? pick(inner[0]) : pick(inner);
            if (url) return url;
        }

        console.warn('[EvaPlayer] No audio URL found in song object:', song);
        return '';
    }

    getImageUrl(song) {
        if (!song) return '/static/images/default-album.png';
        let img = song.image || song.image_url || song.thumbnail || song.cover || '';
        if (Array.isArray(img) && img.length) {
            const entry = img[img.length - 1];
            img = (typeof entry === 'object') ? (entry.url || entry.link || '') : entry;
        }
        return (img && typeof img === 'string') ? img : '/static/images/default-album.png';
    }

    getTitle(song)  { return song ? (song.title  || song.name   || song.song    || 'Unknown') : 'Unknown'; }
    getArtist(song) { return song ? (song.artist || song.primaryArtists || song.singers || 'Unknown') : 'Unknown'; }
    getId(song)     { return song ? (song.id     || song.song_id || '') : ''; }

    // ── Init audio event listeners (once only) ────────────────────────────────
    init() {
        if (this._listenersAttached) return;
        this._listenersAttached = true;

        this.audio.addEventListener('timeupdate', () => this._onTimeUpdate());
        this.audio.addEventListener('ended',      () => this.handleEnded());
        this.audio.addEventListener('play',  () => { this.isPlaying = true;  this._syncPlayIcons(true);  });
        this.audio.addEventListener('pause', () => { this.isPlaying = false; this._syncPlayIcons(false); });
        this.audio.addEventListener('error', (e) => {
            console.error('[EvaPlayer] Audio error:', e, 'src:', this.audio.src);
            if (this.currentSong && this.getId(this.currentSong)) {
                this._refetchAndPlay(this.getId(this.currentSong));
            } else {
                showToast('Playback error — try again', 'error');
            }
        });

        // Bar progress seek — use delegation so it works after SPA swaps
        document.addEventListener('click', (e) => {
            const bar = e.target.closest('#musicBarProgress');
            if (!bar) return;
            e.stopPropagation();
            const rect = bar.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space')                   { e.preventDefault(); this.togglePlay(); }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft'  && e.ctrlKey) this.previous();
        });

        this.refreshQueueFromDOM();
    }

    // ── Refetch URL on audio error ─────────────────────────────────────────────
    async _refetchAndPlay(songId) {
        console.log('[EvaPlayer] Refetching URL for:', songId);
        showToast('Retrying…', 'info');
        try {
            const fresh = await fetch(`/api/song/${songId}`).then(r => r.json());
            const freshUrl = this.getAudioUrl(fresh);
            if (freshUrl && freshUrl !== this.audio.src) {
                this.audio.src = freshUrl;
                this.audio.load();
                await this.audio.play();
                this.currentSong = { ...this.currentSong, ...fresh };
                showToast('▶ ' + this.getTitle(this.currentSong), 'success');
            } else {
                showToast('Song unavailable', 'error');
            }
        } catch (err) {
            console.error('[EvaPlayer] Refetch failed:', err);
            showToast('Playback failed', 'error');
        }
    }

    // ── Sync play icons in bar + overlay ──────────────────────────────────────
    _syncPlayIcons(playing) {
        const barIcon = document.getElementById('musicBarPlayIcon');
        if (barIcon) barIcon.className = `fas ${playing ? 'fa-pause' : 'fa-play'}`;
        const npIcon = document.getElementById('npPlayIcon');
        if (npIcon)  npIcon.className  = `fas ${playing ? 'fa-pause' : 'fa-play'}`;
        if (window._npUpdatePlayBtn) window._npUpdatePlayBtn(playing);
    }

    // ── timeupdate ─────────────────────────────────────────────────────────────
    _onTimeUpdate() {
        if (!this.audio.duration) return;
        const pct = (this.audio.currentTime / this.audio.duration) * 100;

        const fill = document.getElementById('musicBarProgressFill');
        if (fill) fill.style.width = pct + '%';

        if (!this._seekTouching) {
            const npFill  = document.getElementById('npProgressFill');
            const npThumb = document.getElementById('npProgressThumb');
            const npCur   = document.getElementById('npCurrentTime');
            const npTot   = document.getElementById('npTotalTime');
            if (npFill)  npFill.style.width  = pct + '%';
            if (npThumb) npThumb.style.left  = pct + '%';
            if (npCur)   npCur.textContent   = this._fmt(this.audio.currentTime);
            if (npTot)   npTot.textContent   = this._fmt(this.audio.duration);
        }

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
        // Re-show bar if a song is already loaded
        if (this.currentSong) this.showMusicBar();
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

        this.currentSong = songData;
        const idx = this.queue.findIndex(s => this.getId(s) === songId);
        if (idx !== -1) this.currentIndex = idx;
        else { this.queue.push(songData); this.currentIndex = this.queue.length - 1; }

        let audioUrl = this.getAudioUrl(songData);

        // Fetch fresh URL from API if missing
        if (!audioUrl && songId) {
            showToast('Loading song…', 'info');
            try {
                const fresh = await fetch(`/api/song/${songId}`).then(r => r.json());
                if (fresh && !fresh.error) {
                    audioUrl = this.getAudioUrl(fresh);
                    this.currentSong = { ...songData, ...fresh };
                    console.log('[EvaPlayer] Fresh URL fetched:', audioUrl ? 'yes' : 'no');
                }
            } catch (e) {
                console.error('[EvaPlayer] Fetch failed:', e);
            }
        }

        if (!audioUrl) {
            showToast('No audio URL available', 'error');
            this._updateBarUI(this.currentSong);
            this._updateOverlayUI(this.currentSong);
            this.showMusicBar();
            return;
        }

        if (this.audio.src !== audioUrl) {
            this.audio.src = audioUrl;
            this.audio.load();
        }

        // Show bar immediately with metadata before play resolves
        this._updateBarUI(this.currentSong);
        this._updateOverlayUI(this.currentSong);
        this.showMusicBar();

        try {
            await this.audio.play();
            this.isPlaying = true;
            this._saveLastSong(this.currentSong);
            showToast('▶ ' + this.getTitle(this.currentSong), 'success');
        } catch (err) {
            console.warn('[EvaPlayer] Autoplay blocked:', err);
            this.isPlaying = false;
            this._syncPlayIcons(false);
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
        if (this.isPlaying) {
            this.audio.pause();
        } else {
            if (!this.audio.src || this.audio.src === window.location.href) {
                this.playSong(this.getId(this.currentSong), this.currentSong);
                return;
            }
            this.audio.play().catch(err => {
                console.error('[EvaPlayer] Resume failed:', err);
                showToast('Playback failed', 'error');
            });
        }
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
        if (this.repeatMode === 2) {
            this.audio.currentTime = 0; this.audio.play().catch(() => {});
        } else if (this.isShuffle) {
            this.playRandom();
        } else if (this.currentIndex < this.queue.length - 1) {
            this.next();
        } else if (this.repeatMode === 1) {
            this.currentIndex = 0; this.playSong(this.getId(this.queue[0]), this.queue[0]);
        } else {
            this.isPlaying = false; this._syncPlayIcons(false);
        }
    }

    seek(percent) {
        if (!this.audio.duration || isNaN(this.audio.duration)) return;
        this.audio.currentTime = percent * this.audio.duration;
    }

    // ── UI updates ─────────────────────────────────────────────────────────────
    _updateBarUI(song) {
        if (!song) return;
        const thumb  = document.getElementById('musicBarThumb');
        const title  = document.getElementById('musicBarTitle');
        const artist = document.getElementById('musicBarArtist');
        if (thumb)  thumb.src           = this.getImageUrl(song);
        if (title)  title.textContent   = this.getTitle(song);
        if (artist) artist.textContent  = this.getArtist(song);
        this._syncPlayIcons(this.isPlaying);
    }

    _updateOverlayUI(song) {
        if (!song) return;
        const art    = document.getElementById('npAlbumArt');
        const title  = document.getElementById('npSongTitle');
        const artist = document.getElementById('npSongArtist');
        const bg     = document.getElementById('npBg');
        const label  = document.getElementById('npArtistLabel');
        const link   = document.getElementById('npViewArtist');
        if (art)    art.src                  = this.getImageUrl(song);
        if (title)  title.textContent        = this.getTitle(song);
        if (artist) artist.textContent       = this.getArtist(song);
        if (bg)     bg.style.backgroundImage = `url('${this.getImageUrl(song)}')`;
        if (label)  label.textContent        = this.getArtist(song);
        if (link)   link.href                = `/search?q=${encodeURIComponent(this.getArtist(song))}`;
        if (window._npUpdateSongUI) window._npUpdateSongUI(song);
    }

    showMusicBar() {
        const bar = document.getElementById('musicBar');
        if (bar) bar.classList.remove('hidden');
    }

    toggleShuffle() {
        this.isShuffle = !this.isShuffle;
        showToast(this.isShuffle ? 'Shuffle on' : 'Shuffle off', 'info');
    }

    toggleRepeat() {
        this.repeatMode = (this.repeatMode + 1) % 3;
        showToast(['Repeat off', 'Repeat all', 'Repeat one'][this.repeatMode], 'info');
    }

    // ── Favorites ──────────────────────────────────────────────────────────────
    async toggleFavorite(songOverride, btnEl) {
        const song = songOverride || this.currentSong;
        if (!song) return;
        const songId = this.getId(song);
        if (btnEl) { btnEl.style.transform = 'scale(1.3)'; setTimeout(() => btnEl.style.transform = '', 200); }
        try {
            const res  = await fetch('/api/favorite', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
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

// ── Global convenience functions ───────────────────────────────────────────────
function playSong(songId, songData)  { window.player.playSong(songId, songData); }
function barTogglePlay()             { window.player.togglePlay(); }
function togglePlay()                { window.player.togglePlay(); }
function barNext()                   { window.player.next(); }
function nextSong()                  { window.player.next(); }
function barPrev()                   { window.player.previous(); }
function previousSong()              { window.player.previous(); }
function barSeek(e) {
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

// ── showToast (safe fallback if not defined elsewhere) ────────────────────────
if (typeof showToast === 'undefined') {
    window.showToast = function(msg, type = 'info') {
        let t = document.getElementById('__evaToast');
        if (!t) {
            t = document.createElement('div');
            t.id = '__evaToast';
            t.style.cssText = `
                position:fixed;bottom:140px;left:50%;transform:translateX(-50%) translateY(20px);
                padding:10px 20px;border-radius:20px;font-size:13px;font-weight:500;
                color:white;z-index:10000;opacity:0;transition:all 0.3s ease;
                pointer-events:none;white-space:nowrap;`;
            document.body.appendChild(t);
        }
        const colors = { success: '#1DB954', error: '#ef4444', info: '#3b82f6' };
        t.style.background = colors[type] || colors.info;
        t.textContent = msg;
        t.style.opacity = '1';
        t.style.transform = 'translateX(-50%) translateY(0)';
        clearTimeout(t._timer);
        t._timer = setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateX(-50%) translateY(20px)';
        }, 2500);
    };
}

// ── Full-screen player overlay ─────────────────────────────────────────────────
function openPlayerOverlay(song) {
    let overlay = document.getElementById('evaPlayerOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'evaPlayerOverlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;display:none;';
        overlay.innerHTML = `
<div id="npBg" style="
    position:absolute;inset:0;
    background-size:cover;background-position:center;
    display:flex;flex-direction:column;align-items:center;
    justify-content:center;padding:24px;box-sizing:border-box;
    background-color:rgba(0,0,0,0.92);">

  <button onclick="closePlayerOverlay()" style="
    position:absolute;top:20px;right:20px;background:none;
    border:none;color:#fff;font-size:24px;cursor:pointer;">
    <i class="fas fa-chevron-down"></i>
  </button>

  <img id="npAlbumArt" src="/static/images/default-album.png" style="
    width:260px;height:260px;border-radius:16px;object-fit:cover;
    box-shadow:0 8px 32px rgba(0,0,0,0.5);margin-bottom:28px;">

  <div style="text-align:center;margin-bottom:24px;width:100%;max-width:340px">
    <div id="npSongTitle" style="color:#fff;font-size:20px;font-weight:700;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></div>
    <div id="npSongArtist" style="color:rgba(255,255,255,0.7);font-size:14px;margin-top:4px;">
      <a id="npViewArtist" href="#" style="color:inherit;text-decoration:none">
        <span id="npArtistLabel"></span>
      </a>
    </div>
  </div>

  <div style="width:100%;max-width:340px;margin-bottom:8px;position:relative;cursor:pointer"
       onclick="window.player._seekFromOverlay(event,this)">
    <div style="height:4px;background:rgba(255,255,255,0.2);border-radius:4px;position:relative;">
      <div id="npProgressFill" style="height:100%;background:#1db954;border-radius:4px;width:0%"></div>
      <div id="npProgressThumb" style="
        position:absolute;top:50%;transform:translate(-50%,-50%);
        width:12px;height:12px;background:#fff;border-radius:50%;left:0%"></div>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;width:100%;max-width:340px;
    color:rgba(255,255,255,0.6);font-size:12px;margin-bottom:24px">
    <span id="npCurrentTime">0:00</span>
    <span id="npTotalTime">0:00</span>
  </div>

  <div style="display:flex;align-items:center;gap:32px;margin-bottom:28px">
    <button onclick="window.player.previous()" style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer">
      <i class="fas fa-step-backward"></i>
    </button>
    <button onclick="window.player.togglePlay()" style="
      width:56px;height:56px;border-radius:50%;background:#1db954;
      border:none;color:#fff;font-size:22px;cursor:pointer;
      display:flex;align-items:center;justify-content:center">
      <i id="npPlayIcon" class="fas fa-play"></i>
    </button>
    <button onclick="window.player.next()" style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer">
      <i class="fas fa-step-forward"></i>
    </button>
  </div>

  <div style="display:flex;gap:32px;align-items:center">
    <button id="npLikeBtn" onclick="window.player.toggleFavorite(null,this)"
      style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer">
      <i class="far fa-heart"></i>
    </button>
    <button onclick="window.player.shareSong()"
      style="background:none;border:none;color:#fff;font-size:20px;cursor:pointer">
      <i class="fas fa-share-alt"></i>
    </button>
    <button onclick="window.player.toggleShuffle()"
      style="background:none;border:none;color:#fff;font-size:20px;cursor:pointer">
      <i class="fas fa-random"></i>
    </button>
    <button onclick="window.player.toggleRepeat()"
      style="background:none;border:none;color:#fff;font-size:20px;cursor:pointer">
      <i class="fas fa-redo"></i>
    </button>
  </div>
</div>`;
        document.body.appendChild(overlay);
    }

    overlay.style.display = 'block';
    window.player._updateOverlayUI(song);
    window.player._syncPlayIcons(window.player.isPlaying);
    if (window.player.getId(song)) window.player.checkFavoriteState(window.player.getId(song));

    // Blur background
    const bg = document.getElementById('npBg');
    if (bg) bg.style.backdropFilter = 'blur(40px)';
}

function closePlayerOverlay() {
    const overlay = document.getElementById('evaPlayerOverlay');
    if (overlay) overlay.style.display = 'none';
}

EvaPlayer.prototype._seekFromOverlay = function(e, bar) {
    const rect = bar.getBoundingClientRect();
    this.seek((e.clientX - rect.left) / rect.width);
};
