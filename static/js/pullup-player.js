// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic Player — Bottom Mini Bar + Full Screen Now Playing
// ═══════════════════════════════════════════════════════════════════════════════

console.log('[EvaPlayer] Script loading...');

if (window.__evaPlayerInstance) {
    console.log('[EvaPlayer] Instance already exists, reusing');
    window.__evaPlayerInstance.updateUI();
    window.__evaPlayerInstance.refreshQueueFromDOM();
}

class EvaPlayer {
    constructor() {
        if (window.__evaPlayerInstance) return window.__evaPlayerInstance;

        console.log('[EvaPlayer] Creating new instance');
        this.audio = new Audio();
        this.audio.preload = 'metadata';
        this.currentSong = null;
        this.isPlaying = false;
        this.isShuffle = false;
        this.repeatMode = 0;
        this.queue = [];
        this.currentIndex = 0;
        this._listenersAttached = false;

        // Mini bar DOM refs
        this.els = {
            musicBar:        document.getElementById('musicBar'),
            musicBarThumb:   document.getElementById('musicBarThumb'),
            musicBarTitle:   document.getElementById('musicBarTitle'),
            musicBarArtist:  document.getElementById('musicBarArtist'),
            musicBarPlayIcon: document.getElementById('musicBarPlayIcon'),
            musicBarProgress: document.getElementById('musicBarProgress'),
            musicBarProgressFill: document.getElementById('musicBarProgressFill'),
        };

        window.__evaPlayerInstance = this;
        this.init();
        console.log('[EvaPlayer] Initialized');
    }

    getAudioUrl(song) {
        if (!song) return '';
        // Try all possible URL fields from JioSaavn API
        return song.url || song.downloadUrl || song.media_url || song.audio_url || 
               song.download_url || song.stream_url || song.song_url || '';
    }
    getImageUrl(song) {
        if (!song) return '/static/images/default-album.png';
        let img = song.image || song.image_url || song.thumbnail || song.cover || '';
        if (Array.isArray(img)) img = img[img.length - 1] || img[0] || '';
        return img || '/static/images/default-album.png';
    }
    getTitle(song)  { return song ? (song.title || song.name || song.song || 'Unknown') : 'Unknown'; }
    getArtist(song) { return song ? (song.artist || song.primaryArtists || song.singers || 'Unknown') : 'Unknown'; }
    getId(song)     { return song ? (song.id || song.song_id || '') : ''; }

    init() {
        if (this._listenersAttached) return;
        this._listenersAttached = true;

        // Mini bar progress click
        this.els.musicBarProgress?.addEventListener('click', (e) => {
            e.stopPropagation();
            const rect = this.els.musicBarProgress.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });

        // Audio events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('canplay', () => {
            console.log('[EvaPlayer] Audio can play');
            if (this._pendingPlay) {
                this._pendingPlay = false;
                this.audio.play().catch(err => console.error('[EvaPlayer] Auto-play failed:', err));
            }
        });
        this.audio.addEventListener('error', (e) => {
            console.error('[EvaPlayer] Audio error:', e, 'src:', this.audio.src);
            showToast('Failed to load audio', 'error');
            setTimeout(() => this.next(), 1500);
        });

        // Keyboard
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space') { e.preventDefault(); this.togglePlay(); }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft' && e.ctrlKey) this.previous();
        });

        this.refreshQueueFromDOM();
    }

    refreshQueueFromDOM() {
        const items = document.querySelectorAll('.grid-item[data-song-id]');
        console.log('[EvaPlayer] Found', items.length, 'songs in DOM');
        if (!items.length) return;
        const newQueue = [];
        items.forEach(item => {
            const id = item.dataset.songId;
            if (id) {
                newQueue.push({
                    id: id,
                    title: item.dataset.songTitle || 'Unknown',
                    artist: item.dataset.songArtist || 'Unknown',
                    image: item.dataset.songImage || '/static/images/default-album.png',
                    url: item.dataset.songUrl || ''
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
            console.log('[EvaPlayer] Queue updated:', this.queue.length, 'songs');
        }
    }

    async playSong(songId, songData = null) {
        console.log('[EvaPlayer] playSong called:', songId, songData);

        if (!songData) {
            // Try to find in queue
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
        console.log('[EvaPlayer] Audio URL from data:', audioUrl);

        // If no URL in data, try to fetch from API
        if (!audioUrl && songId) {
            showToast('Fetching song...', 'info');
            try {
                const fresh = await API.getSong(songId);
                console.log('[EvaPlayer] API response:', fresh);
                if (fresh && this.getAudioUrl(fresh)) {
                    audioUrl = this.getAudioUrl(fresh);
                    this.currentSong = { ...songData, ...fresh };
                    console.log('[EvaPlayer] Got URL from API:', audioUrl);
                } else {
                    showToast('Song unavailable - no audio URL', 'error');
                    return;
                }
            } catch (e) {
                console.error('[EvaPlayer] API fetch failed:', e);
                showToast('Failed to load song', 'error');
                return;
            }
        }

        if (!audioUrl) {
            showToast('No audio URL available', 'error');
            return;
        }

        // Set source and play
        if (this.audio.src !== audioUrl) {
            this.audio.src = audioUrl;
            this.audio.load();
            this._pendingPlay = true;
            console.log('[EvaPlayer] Loading audio:', audioUrl.substring(0, 80) + '...');
        }

        try {
            await this.audio.play();
            this.isPlaying = true;
            this._pendingPlay = false;
            this.updateUI();
            this.showMusicBar();
            this.addToRecentlyPlayed(this.currentSong);
            showToast('▶ ' + this.getTitle(this.currentSong), 'success');
            console.log('[EvaPlayer] Playing:', this.getTitle(this.currentSong));
        } catch (err) {
            console.error('[EvaPlayer] Play error:', err);
            this.isPlaying = false;
            this._pendingPlay = false;
            this.updateUI();
            showToast('Tap to play', 'info');
        }
    }

    togglePlay() {
        console.log('[EvaPlayer] togglePlay, currentSong:', this.currentSong ? 'yes' : 'no');
        if (!this.currentSong) {
            if (this.queue.length > 0) {
                this.playSong(this.getId(this.queue[0]), this.queue[0]);
            } else {
                showToast('Select a song first', 'info');
            }
            return;
        }
        if (this.isPlaying) {
            this.audio.pause();
            this.isPlaying = false;
            console.log('[EvaPlayer] Paused');
        } else {
            this.audio.play().then(() => {
                this.isPlaying = true;
                this.updateUI();
                console.log('[EvaPlayer] Resumed');
            }).catch(err => {
                console.error('[EvaPlayer] Resume failed:', err);
                showToast('Playback failed', 'error');
            });
            return;
        }
        this.updateUI();
    }

    next() {
        if (!this.queue.length) return;
        if (this.isShuffle) this.playRandom();
        else if (this.currentIndex < this.queue.length - 1) {
            this.currentIndex++;
            this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]);
        } else if (this.repeatMode === 1) {
            this.currentIndex = 0;
            this.playSong(this.getId(this.queue[0]), this.queue[0]);
        }
    }

    previous() {
        if (!this.queue.length) return;
        if (this.audio.currentTime > 3) { this.audio.currentTime = 0; this.updateProgress(); }
        else if (this.currentIndex > 0) {
            this.currentIndex--;
            this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]);
        }
    }

    playRandom() {
        if (this.queue.length <= 1) return;
        let newIndex;
        do { newIndex = Math.floor(Math.random() * this.queue.length); }
        while (newIndex === this.currentIndex && this.queue.length > 1);
        this.currentIndex = newIndex;
        this.playSong(this.getId(this.queue[newIndex]), this.queue[newIndex]);
    }

    handleEnded() {
        if (this.repeatMode === 2) { this.audio.currentTime = 0; this.audio.play().catch(() => {}); }
        else if (this.isShuffle) this.playRandom();
        else if (this.currentIndex < this.queue.length - 1) this.next();
        else if (this.repeatMode === 1) { this.currentIndex = 0; this.playSong(this.getId(this.queue[0]), this.queue[0]); }
        else { this.isPlaying = false; this.updateUI(); }
    }

    seek(percent) {
        if (!this.audio.duration || isNaN(this.audio.duration)) return;
        this.audio.currentTime = percent * this.audio.duration;
        this.updateProgress();
    }

    updateProgress() {
        if (!this.audio.duration) return;
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        if (this.els.musicBarProgressFill) this.els.musicBarProgressFill.style.width = percent + '%';
    }

    updateDuration() {
        // Duration updated
    }

    updateUI() {
        if (!this.currentSong) return;
        const title = this.getTitle(this.currentSong);
        const artist = this.getArtist(this.currentSong);
        const image = this.getImageUrl(this.currentSong);
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';

        if (this.els.musicBarThumb) this.els.musicBarThumb.src = image;
        if (this.els.musicBarTitle) this.els.musicBarTitle.textContent = title;
        if (this.els.musicBarArtist) this.els.musicBarArtist.textContent = artist;
        if (this.els.musicBarPlayIcon) this.els.musicBarPlayIcon.className = `fas ${icon}`;
    }

    showMusicBar() {
        this.els.musicBar?.classList.remove('hidden');
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

    toggleFavorite() {
        if (!this.currentSong) return;
        const id = this.getId(this.currentSong);
        try {
            let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
            const idx = favorites.indexOf(id);
            if (idx === -1) { favorites.push(id); showToast('Added to favorites', 'success'); }
            else { favorites.splice(idx, 1); showToast('Removed from favorites', 'info'); }
            localStorage.setItem('favorites', JSON.stringify(favorites));
        } catch (e) {}
    }

    shareSong() {
        if (!this.currentSong) return;
        const url = window.location.origin + '/player/' + this.getId(this.currentSong);
        const title = this.getTitle(this.currentSong);
        if (navigator.share) navigator.share({ title: title, url: url });
        else navigator.clipboard.writeText(url).then(() => showToast('Link copied!', 'success'));
    }

    addToRecentlyPlayed(song) {
        try {
            let recent = JSON.parse(localStorage.getItem('recentlyPlayed') || '[]');
            recent = recent.filter(s => this.getId(s) !== this.getId(song));
            recent.unshift(song);
            recent = recent.slice(0, 50);
            localStorage.setItem('recentlyPlayed', JSON.stringify(recent));
        } catch (e) {}
    }

    formatTime(seconds) {
        if (!seconds || isNaN(seconds) || !isFinite(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Global Instance & Helpers
// ═══════════════════════════════════════════════════════════════════════════════

console.log('[EvaPlayer] Creating global player instance...');
const player = new EvaPlayer();

function playSong(songId, songData) {
    console.log('[Global] playSong called:', songId);
    if (!window.player) {
        console.error('[Global] Player not initialized!');
        window.player = new EvaPlayer();
    }
    window.player.playSong(songId, songData);
}
function togglePlay() { window.player?.togglePlay(); }
function nextSong() { window.player?.next(); }
function previousSong() { window.player?.previous(); }
function toggleShuffle() { window.player?.toggleShuffle(); }
function toggleRepeat() { window.player?.toggleRepeat(); }
function toggleFavorite() { window.player?.toggleFavorite(); }
function shareSong() { window.player?.shareSong(); }
function expandPlayer(event) {
    if (event) event.stopPropagation();
    if (window.player && window.player.currentSong) {
        window.location.href = '/player/' + window.player.getId(window.player.currentSong);
    }
}
function seekBar(event) {
    if (event) event.stopPropagation();
    const bar = document.getElementById('musicBarProgress');
    if (!bar || !window.player || !window.player.audio.duration) return;
    const rect = bar.getBoundingClientRect();
    const percent = (event.clientX - rect.left) / rect.width;
    window.player.seek(percent);
}

function showToast(message, type = 'info') {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[EvaPlayer] DOM ready, refreshing queue...');
    if (window.__evaPlayerInstance) {
        window.__evaPlayerInstance.refreshQueueFromDOM();
    }
});

console.log('[EvaPlayer] Script loaded successfully');
