// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic Unified Player — PullUpPlayer + MusicPlayer merged
// Single audio instance, bfcache-safe, no double initialization
// ═══════════════════════════════════════════════════════════════════════════════

// ── Prevent double initialization on back-navigation ──────────────────────────
if (window.__evaPlayerInstance) {
    console.log('[EvaPlayer] Instance already exists, reusing');
    window.__evaPlayerInstance.updateUI();
    window.__evaPlayerInstance.refreshQueueFromDOM();
}

class EvaPlayer {
    constructor() {
        // Singleton pattern — return existing instance if already created
        if (window.__evaPlayerInstance) {
            return window.__evaPlayerInstance;
        }

        this.audio = new Audio();
        this.audio.preload = 'metadata';
        this.currentSong = null;
        this.isPlaying = false;
        this.isShuffle = false;
        this.repeatMode = 0; // 0=off, 1=all, 2=one
        this.queue = [];
        this.currentIndex = 0;
        this._listenersAttached = false;

        // DOM refs
        this.els = {
            miniPlayer:      document.getElementById('miniPlayer'),
            fullPlayer:      document.getElementById('fullPlayer'),
            miniThumb:       document.getElementById('miniThumb'),
            miniTitle:       document.getElementById('miniTitle'),
            miniArtist:      document.getElementById('miniArtist'),
            fullThumb:       document.getElementById('fullThumb'),
            fullTitle:       document.getElementById('fullTitle'),
            fullArtist:      document.getElementById('fullArtist'),
            fullArtwork:     document.getElementById('fullArtwork'),
            progressBar:     document.getElementById('progressBar'),
            progressContainer: document.getElementById('progressContainer'),
            currentTime:     document.getElementById('currentTime'),
            totalTime:       document.getElementById('totalTime'),
        };

        window.__evaPlayerInstance = this;
        this.init();
    }

    // ── URL / Data Helpers ──────────────────────────────────────────────────────
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

    // ── Initialization ──────────────────────────────────────────────────────────
    init() {
        if (this._listenersAttached) return;
        this._listenersAttached = true;

        // Mini-player tap to expand
        this.els.miniPlayer?.addEventListener('click', (e) => {
            if (!e.target.closest('.mini-player-btn')) this.expandPlayer();
        });

        // Swipe up on mini-player to expand
        let startY = 0;
        this.els.miniPlayer?.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
        }, { passive: true });
        this.els.miniPlayer?.addEventListener('touchmove', (e) => {
            if (startY - e.touches[0].clientY > 50) this.expandPlayer();
        }, { passive: true });

        // Swipe down on full-player to collapse
        let fullStartY = 0;
        this.els.fullPlayer?.addEventListener('touchstart', (e) => {
            fullStartY = e.touches[0].clientY;
        }, { passive: true });
        this.els.fullPlayer?.addEventListener('touchmove', (e) => {
            if (e.touches[0].clientY - fullStartY > 100) this.collapsePlayer();
        }, { passive: true });

        // Progress bar click to seek
        this.els.progressContainer?.addEventListener('click', (e) => {
            const rect = this.els.progressContainer.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });

        // Audio events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('error', (e) => {
            console.error('[EvaPlayer] Audio error:', e);
            showToast('Failed to load audio', 'error');
            // Auto-skip to next on error
            setTimeout(() => this.next(), 1500);
        });
        this.audio.addEventListener('canplay', () => {
            if (this._pendingPlay) {
                this._pendingPlay = false;
                this.audio.play().catch(() => {});
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space') { e.preventDefault(); this.togglePlay(); }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft' && e.ctrlKey) this.previous();
        });

        // Build queue from song cards on the page
        this.refreshQueueFromDOM();
    }

    // ── Queue Management ────────────────────────────────────────────────────────
    refreshQueueFromDOM() {
        const cards = document.querySelectorAll('[data-id], .trending-card[onclick*="playSong"]');
        if (!cards.length) return;

        const newQueue = [];
        cards.forEach(card => {
            // Try data attributes first
            const id = card.dataset?.id;
            const url = card.dataset?.url;
            const title = card.dataset?.title || card.querySelector('.trending-title, .song-title, h3, h4')?.textContent?.trim() || 'Unknown';
            const artist = card.dataset?.artist || card.querySelector('.trending-artist, .song-artist, p')?.textContent?.trim() || 'Unknown';
            const img = card.dataset?.image || card.querySelector('img')?.src || '/static/images/default-album.png';

            if (id) {
                newQueue.push({ id, title, artist, image: img, url: url || '' });
            }
        });

        if (newQueue.length) {
            // Preserve current song if it's in the new queue
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

    // ── Playback ────────────────────────────────────────────────────────────────
    async playSong(songId, songData = null) {
        console.log('[EvaPlayer] playSong:', songId);

        // If full song data passed, use it
        if (songData && typeof songData === 'object') {
            // Ensure URL exists
            if (!this.getAudioUrl(songData)) {
                showToast('Fetching song...', 'info');
                try {
                    const fresh = await API.getSong(songId);
                    if (fresh && this.getAudioUrl(fresh)) {
                        songData = { ...songData, ...fresh };
                    } else {
                        showToast('Song unavailable', 'error');
                        return;
                    }
                } catch (e) {
                    showToast('Failed to load song', 'error');
                    return;
                }
            }

            this.currentSong = songData;
            const idx = this.queue.findIndex(s => this.getId(s) === songId);
            if (idx !== -1) {
                this.queue[idx] = { ...this.queue[idx], ...songData };
                this.currentIndex = idx;
            } else {
                this.queue.push(songData);
                this.currentIndex = this.queue.length - 1;
            }
        } else {
            // Find in queue
            const idx = this.queue.findIndex(s => this.getId(s) === songId);
            if (idx !== -1) {
                this.currentIndex = idx;
                this.currentSong = this.queue[idx];
            } else {
                showToast('Loading...', 'info');
                try {
                    const song = await API.getSong(songId);
                    if (song) {
                        this.currentSong = song;
                        this.queue.push(song);
                        this.currentIndex = this.queue.length - 1;
                    } else {
                        showToast('Song not found', 'error');
                        return;
                    }
                } catch (e) {
                    showToast('Failed to load song', 'error');
                    return;
                }
            }
        }

        const audioUrl = this.getAudioUrl(this.currentSong);
        if (!audioUrl) {
            showToast('No audio URL available', 'error');
            return;
        }

        // Set source and play
        if (this.audio.src !== audioUrl) {
            this.audio.src = audioUrl;
            this.audio.load();
        }

        this._pendingPlay = true;
        try {
            await this.audio.play();
            this.isPlaying = true;
            this._pendingPlay = false;
            this.updateUI();
            this.showMiniPlayer();
            this.addToRecentlyPlayed(this.currentSong);
            showToast('Now Playing: ' + this.getTitle(this.currentSong), 'success');
        } catch (err) {
            console.error('[EvaPlayer] Play error:', err);
            this.isPlaying = false;
            this._pendingPlay = false;
            this.updateUI();
            showToast('Tap to play', 'info');
        }
    }

    togglePlay() {
        if (!this.currentSong) {
            // Try to play first song in queue
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
        } else {
            this.audio.play().then(() => { this.isPlaying = true; this.updateUI(); })
                .catch(() => showToast('Playback failed', 'error'));
            return; // updateUI called in then()
        }
        this.updateUI();
    }

    // ── Navigation ────────────────────────────────────────────────────────────────
    next() {
        if (!this.queue.length) return;
        if (this.isShuffle) {
            this.playRandom();
        } else if (this.currentIndex < this.queue.length - 1) {
            this.currentIndex++;
            this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]);
        } else if (this.repeatMode === 1) {
            this.currentIndex = 0;
            this.playSong(this.getId(this.queue[0]), this.queue[0]);
        }
    }

    previous() {
        if (!this.queue.length) return;
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            this.updateProgress();
        } else if (this.currentIndex > 0) {
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
        if (this.repeatMode === 2) {
            this.audio.currentTime = 0;
            this.audio.play().catch(() => {});
        } else if (this.isShuffle) {
            this.playRandom();
        } else if (this.currentIndex < this.queue.length - 1) {
            this.next();
        } else if (this.repeatMode === 1) {
            this.currentIndex = 0;
            this.playSong(this.getId(this.queue[0]), this.queue[0]);
        } else {
            this.isPlaying = false;
            this.updateUI();
        }
    }

    // ── Seek / Progress ───────────────────────────────────────────────────────────
    seek(percent) {
        if (!this.audio.duration || isNaN(this.audio.duration)) return;
        this.audio.currentTime = percent * this.audio.duration;
        this.updateProgress();
    }

    updateProgress() {
        if (!this.audio.duration) return;
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        if (this.els.progressBar) this.els.progressBar.style.width = percent + '%';
        if (this.els.currentTime) this.els.currentTime.textContent = this.formatTime(this.audio.currentTime);
    }

    updateDuration() {
        if (this.els.totalTime) {
            this.els.totalTime.textContent = this.formatTime(this.audio.duration);
        }
    }

    formatTime(seconds) {
        if (!seconds || isNaN(seconds) || !isFinite(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // ── UI Updates ────────────────────────────────────────────────────────────────
    updateUI() {
        if (!this.currentSong) return;
        const title = this.getTitle(this.currentSong);
        const artist = this.getArtist(this.currentSong);
        const image = this.getImageUrl(this.currentSong);
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';

        if (this.els.miniThumb) this.els.miniThumb.src = image;
        if (this.els.miniTitle) this.els.miniTitle.textContent = title;
        if (this.els.miniArtist) this.els.miniArtist.textContent = artist;

        if (this.els.fullThumb) this.els.fullThumb.src = image;
        if (this.els.fullTitle) this.els.fullTitle.textContent = title;
        if (this.els.fullArtist) this.els.fullArtist.textContent = artist;

        document.querySelectorAll('.play-icon').forEach(el => {
            el.className = `fas ${icon} play-icon`;
        });

        if (this.els.fullArtwork) {
            this.els.fullArtwork.classList.toggle('playing', this.isPlaying);
        }
    }

    showMiniPlayer() {
        this.els.miniPlayer?.classList.add('active');
    }

    expandPlayer() {
        if (!this.currentSong) return;
        this.els.fullPlayer?.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    collapsePlayer() {
        this.els.fullPlayer?.classList.remove('active');
        document.body.style.overflow = '';
    }

    // ── Toggles ───────────────────────────────────────────────────────────────────
    toggleShuffle() {
        this.isShuffle = !this.isShuffle;
        document.querySelector('.shuffle-btn')?.classList.toggle('active', this.isShuffle);
        showToast(this.isShuffle ? 'Shuffle on' : 'Shuffle off', 'info');
    }

    toggleRepeat() {
        this.repeatMode = (this.repeatMode + 1) % 3;
        const modes = ['Repeat off', 'Repeat all', 'Repeat one'];
        const icons = ['fa-repeat', 'fa-repeat', 'fa-repeat-1'];
        showToast(modes[this.repeatMode], 'info');
        document.querySelector('.repeat-btn')?.classList.toggle('active', this.repeatMode > 0);
    }

    toggleFavorite() {
        if (!this.currentSong) return;
        const id = this.getId(this.currentSong);
        try {
            let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
            const idx = favorites.indexOf(id);
            if (idx === -1) {
                favorites.push(id);
                showToast('Added to favorites', 'success');
            } else {
                favorites.splice(idx, 1);
                showToast('Removed from favorites', 'info');
            }
            localStorage.setItem('favorites', JSON.stringify(favorites));
        } catch (e) {}
    }

    shareSong() {
        if (!this.currentSong) return;
        const url = window.location.origin + '/player/' + this.getId(this.currentSong);
        const title = this.getTitle(this.currentSong);
        if (navigator.share) {
            navigator.share({ title: title, url: url });
        } else {
            navigator.clipboard.writeText(url).then(() => showToast('Link copied!', 'success'));
        }
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

// Create singleton instance
const player = new EvaPlayer();

// Global functions called from HTML onclick handlers
function playSong(songId, songData)      { player.playSong(songId, songData); }
function togglePlay()                     { player.togglePlay(); }
function nextSong()                       { player.next(); }
function previousSong()                   { player.previous(); }
function toggleShuffle()                  { player.toggleShuffle(); }
function toggleRepeat()                   { player.toggleRepeat(); }
function toggleFavorite()                 { player.toggleFavorite(); }
function shareSong()                      { player.shareSong(); }
function expandPlayer()                   { player.expandPlayer(); }
function collapsePlayer()                 { player.collapsePlayer(); }

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

// Refresh queue when DOM changes (e.g., after navigating back)
document.addEventListener('DOMContentLoaded', () => {
    if (window.__evaPlayerInstance) {
        window.__evaPlayerInstance.refreshQueueFromDOM();
    }
});
