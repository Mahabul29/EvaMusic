// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic Simple Player — Spotify/YouTube Music style bottom bar
// No full-screen overlay, no pull-up gesture. Just a clean bottom music bar.
// ═══════════════════════════════════════════════════════════════════════════════

if (window.__evaPlayerInstance) {
    console.log('[EvaPlayer] Instance already exists, reusing');
    window.__evaPlayerInstance.updateUI();
    window.__evaPlayerInstance.refreshQueueFromDOM();
}

class EvaPlayer {
    constructor() {
        if (window.__evaPlayerInstance) return window.__evaPlayerInstance;

        this.audio = new Audio();
        this.audio.preload = 'metadata';
        this.currentSong = null;
        this.isPlaying = false;
        this.isShuffle = false;
        this.repeatMode = 0;
        this.queue = [];
        this.currentIndex = 0;
        this._listenersAttached = false;

        // DOM refs for bottom music bar
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
    }

    getAudioUrl(song) {
        if (!song) return '';
        return song.url || song.downloadUrl || song.media_url || song.audio_url || '';
    }
    getImageUrl(song) {
        if (!song) return '/static/images/default-album.png';
        let img = song.image || song.image_url || song.thumbnail || '';
        if (Array.isArray(img)) img = img[img.length - 1] || img[0] || '';
        return img || '/static/images/default-album.png';
    }
    getTitle(song)  { return song ? (song.title || song.name || 'Unknown') : 'Unknown'; }
    getArtist(song) { return song ? (song.artist || song.primaryArtists || 'Unknown') : 'Unknown'; }
    getId(song)     { return song ? (song.id || song.song_id || '') : ''; }

    init() {
        if (this._listenersAttached) return;
        this._listenersAttached = true;

        // Progress bar click to seek
        this.els.musicBarProgress?.addEventListener('click', (e) => {
            const rect = this.els.musicBarProgress.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });

        // Audio events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('error', () => {
            showToast('Failed to load audio', 'error');
            setTimeout(() => this.next(), 1500);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space') { e.preventDefault(); this.togglePlay(); }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft' && e.ctrlKey) this.previous();
        });

        this.refreshQueueFromDOM();
    }

    refreshQueueFromDOM() {
        const cards = document.querySelectorAll('[data-id], .trending-card[onclick*="playSong"]');
        if (!cards.length) return;
        const newQueue = [];
        cards.forEach(card => {
            const id = card.dataset?.id;
            const url = card.dataset?.url;
            const title = card.dataset?.title || card.querySelector('.trending-title, .song-title, h3, h4')?.textContent?.trim() || 'Unknown';
            const artist = card.dataset?.artist || card.querySelector('.trending-artist, .song-artist, p')?.textContent?.trim() || 'Unknown';
            const img = card.dataset?.image || card.querySelector('img')?.src || '/static/images/default-album.png';
            if (id) newQueue.push({ id, title, artist, image: img, url: url || '' });
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

    setQueue(songs, startIndex = 0) {
        this.queue = songs || [];
        this.currentIndex = Math.max(0, Math.min(startIndex, this.queue.length - 1));
    }

    async playSong(songId, songData = null) {
        console.log('[EvaPlayer] playSong:', songId);

        if (songData && typeof songData === 'object') {
            if (!this.getAudioUrl(songData)) {
                showToast('Fetching song...', 'info');
                try {
                    const fresh = await API.getSong(songId);
                    if (fresh && this.getAudioUrl(fresh)) songData = { ...songData, ...fresh };
                    else { showToast('Song unavailable', 'error'); return; }
                } catch (e) { showToast('Failed to load song', 'error'); return; }
            }
            this.currentSong = songData;
            const idx = this.queue.findIndex(s => this.getId(s) === songId);
            if (idx !== -1) { this.queue[idx] = { ...this.queue[idx], ...songData }; this.currentIndex = idx; }
            else { this.queue.push(songData); this.currentIndex = this.queue.length - 1; }
        } else {
            const idx = this.queue.findIndex(s => this.getId(s) === songId);
            if (idx !== -1) { this.currentIndex = idx; this.currentSong = this.queue[idx]; }
            else {
                showToast('Loading...', 'info');
                try {
                    const song = await API.getSong(songId);
                    if (song) { this.currentSong = song; this.queue.push(song); this.currentIndex = this.queue.length - 1; }
                    else { showToast('Song not found', 'error'); return; }
                } catch (e) { showToast('Failed to load song', 'error'); return; }
            }
        }

        const audioUrl = this.getAudioUrl(this.currentSong);
        if (!audioUrl) { showToast('No audio URL available', 'error'); return; }

        if (this.audio.src !== audioUrl) { this.audio.src = audioUrl; this.audio.load(); }

        try {
            await this.audio.play();
            this.isPlaying = true;
            this.updateUI();
            this.showMusicBar();
            this.addToRecentlyPlayed(this.currentSong);
            showToast('Now Playing: ' + this.getTitle(this.currentSong), 'success');
        } catch (err) {
            this.isPlaying = false;
            this.updateUI();
            showToast('Tap to play', 'info');
        }
    }

    togglePlay() {
        if (!this.currentSong) {
            if (this.queue.length > 0) this.playSong(this.getId(this.queue[0]), this.queue[0]);
            else showToast('Select a song first', 'info');
            return;
        }
        if (this.isPlaying) {
            this.audio.pause();
            this.isPlaying = false;
        } else {
            this.audio.play().then(() => { this.isPlaying = true; this.updateUI(); })
                .catch(() => showToast('Playback failed', 'error'));
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
        // Duration available, progress bar ready
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
}

// ═══════════════════════════════════════════════════════════════════════════════
// Global Instance & Helpers
// ═══════════════════════════════════════════════════════════════════════════════

const player = new EvaPlayer();

function playSong(songId, songData)      { player.playSong(songId, songData); }
function togglePlay()                     { player.togglePlay(); }
function nextSong()                       { player.next(); }
function previousSong()                   { player.previous(); }
function toggleShuffle()                  { player.toggleShuffle(); }
function toggleRepeat()                   { player.toggleRepeat(); }
function toggleFavorite()                 { player.toggleFavorite(); }
function shareSong()                      { player.shareSong(); }

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
    if (window.__evaPlayerInstance) window.__evaPlayerInstance.refreshQueueFromDOM();
});
