class MusicPlayer {
    constructor() {
        this.audio = document.getElementById('audioPlayer');
        this.currentSong = null;
        this.queue = [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.isShuffled = false;
        this.repeatMode = 0; // 0: off, 1: all, 2: one
        
        this.elements = {
            playPauseBtn: document.getElementById('playPauseBtn'),
            playPauseBtnMain: document.getElementById('playPauseBtnMain'),
            prevBtn: document.getElementById('prevBtn'),
            prevBtnMain: document.getElementById('prevBtnMain'),
            nextBtn: document.getElementById('nextBtn'),
            nextBtnMain: document.getElementById('nextBtnMain'),
            progressBar: document.getElementById('progressBar'),
            progressFill: document.getElementById('progressFill'),
            scrubberBar: document.getElementById('scrubberBar'),
            scrubberFill: document.getElementById('scrubberFill'),
            scrubberThumb: document.getElementById('scrubberThumb'),
            currentTime: document.getElementById('currentTime'),
            fullCurrentTime: document.getElementById('fullCurrentTime'),
            duration: document.getElementById('duration'),
            fullDuration: document.getElementById('fullDuration'),
            volumeSlider: document.getElementById('volumeSlider'),
            playerTitle: document.getElementById('playerTitle'),
            playerArtist: document.getElementById('playerArtist'),
            playerThumb: document.getElementById('playerThumb'),
            shuffleBtn: document.getElementById('shuffleBtn'),
            repeatBtn: document.getElementById('repeatBtn')
        };
        
        this.init();
    }
    
    init() {
        // Event Listeners
        this.elements.playPauseBtn?.addEventListener('click', () => this.togglePlay());
        this.elements.playPauseBtnMain?.addEventListener('click', () => this.togglePlay());
        this.elements.prevBtn?.addEventListener('click', () => this.prev());
        this.elements.prevBtnMain?.addEventListener('click', () => this.prev());
        this.elements.nextBtn?.addEventListener('click', () => this.next());
        this.elements.nextBtnMain?.addEventListener('click', () => this.next());
        
        this.elements.progressBar?.addEventListener('click', (e) => this.seek(e, this.elements.progressBar));
        this.elements.scrubberBar?.addEventListener('click', (e) => this.seek(e, this.elements.scrubberBar));
        
        this.elements.volumeSlider?.addEventListener('input', (e) => {
            this.audio.volume = e.target.value / 100;
        });
        
        this.elements.shuffleBtn?.addEventListener('click', () => this.toggleShuffle());
        this.elements.repeatBtn?.addEventListener('click', () => this.toggleRepeat());
        
        // Audio Events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('ended', () => this.onEnded());
        this.audio.addEventListener('error', () => this.onError());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                this.togglePlay();
            }
            if (e.code === 'ArrowRight' && e.ctrlKey) this.next();
            if (e.code === 'ArrowLeft' && e.ctrlKey) this.prev();
        });
    }
    
    async loadSong(song) {
        this.currentSong = song;
        this.audio.src = song.url;
        this.audio.load();
        
        // Update UI
        this.elements.playerTitle && (this.elements.playerTitle.textContent = song.title);
        this.elements.playerArtist && (this.elements.playerArtist.textContent = song.artist);
        this.elements.playerThumb && (this.elements.playerThumb.src = song.image);
        
        // Update full player if exists
        const fullAlbumArt = document.getElementById('fullAlbumArt');
        if (fullAlbumArt) fullAlbumArt.src = song.image;
        
        // Update page title
        document.title = `${song.title} - ${song.artist} | JioSaavn Music`;
        
        // Save to recently played
        this.addToRecentlyPlayed(song);
        
        await this.play();
    }
    
    async play() {
        try {
            await this.audio.play();
            this.isPlaying = true;
            this.updatePlayButton();
        } catch (err) {
            console.error('Play error:', err);
        }
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.updatePlayButton();
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    updatePlayButton() {
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';
        [this.elements.playPauseBtn, this.elements.playPauseBtnMain].forEach(btn => {
            if (btn) btn.innerHTML = `<i class="fas ${icon}"></i>`;
        });
    }
    
    prev() {
        if (this.queue.length === 0) return;
        this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
        this.loadSong(this.queue[this.currentIndex]);
    }
    
    next() {
        if (this.queue.length === 0) return;
        this.currentIndex = (this.currentIndex + 1) % this.queue.length;
        this.loadSong(this.queue[this.currentIndex]);
    }
    
    seek(e, bar) {
        const rect = bar.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        this.audio.currentTime = percent * this.audio.duration;
    }
    
    updateProgress() {
        const percent = (this.audio.currentTime / this.audio.duration) * 100 || 0;
        
        this.elements.progressFill && (this.elements.progressFill.style.width = `${percent}%`);
        this.elements.scrubberFill && (this.elements.scrubberFill.style.width = `${percent}%`);
        this.elements.scrubberThumb && (this.elements.scrubberThumb.style.left = `${percent}%`);
        
        const time = this.formatTime(this.audio.currentTime);
        this.elements.currentTime && (this.elements.currentTime.textContent = time);
        this.elements.fullCurrentTime && (this.elements.fullCurrentTime.textContent = time);
    }
    
    updateDuration() {
        const time = this.formatTime(this.audio.duration || 0);
        this.elements.duration && (this.elements.duration.textContent = time);
        this.elements.fullDuration && (this.elements.fullDuration.textContent = time);
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    onEnded() {
        if (this.repeatMode === 2) {
            this.audio.currentTime = 0;
            this.play();
        } else {
            this.next();
        }
    }
    
    onError() {
        console.error('Audio error');
        // Try next song
        setTimeout(() => this.next(), 2000);
    }
    
    toggleShuffle() {
        this.isShuffled = !this.isShuffled;
        this.elements.shuffleBtn?.classList.toggle('active', this.isShuffled);
        if (this.isShuffled) {
            this.queue = this.shuffleArray([...this.queue]);
        }
    }
    
    toggleRepeat() {
        this.repeatMode = (this.repeatMode + 1) % 3;
        const icons = ['fa-redo', 'fa-redo', 'fa-redo-alt'];
        const titles = ['Repeat Off', 'Repeat All', 'Repeat One'];
        if (this.elements.repeatBtn) {
            this.elements.repeatBtn.innerHTML = `<i class="fas ${icons[this.repeatMode]}"></i>`;
            this.elements.repeatBtn.title = titles[this.repeatMode];
            this.elements.repeatBtn.classList.toggle('active', this.repeatMode > 0);
        }
    }
    
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
    
    addToQueue(songs) {
        this.queue = songs;
        this.currentIndex = 0;
    }
    
    addToRecentlyPlayed(song) {
        let recent = JSON.parse(localStorage.getItem('recentlyPlayed') || '[]');
        recent = recent.filter(s => s.id !== song.id);
        recent.unshift(song);
        recent = recent.slice(0, 50);
        localStorage.setItem('recentlyPlayed', JSON.stringify(recent));
    }
}

// Global player instance
let player;

document.addEventListener('DOMContentLoaded', () => {
    player = new MusicPlayer();
});

// Global play function
function playSong(songId, songData = null) {
    if (songData) {
        player.loadSong(songData);
    } else {
        // Fetch song details
        fetch(`/api/song/${songId}`)
            .then(res => res.json())
            .then(song => {
                player.loadSong(song);
            });
    }
}

function addToLibrary(songId) {
    let library = JSON.parse(localStorage.getItem('library') || '[]');
    if (!library.includes(songId)) {
        library.push(songId);
        localStorage.setItem('library', JSON.stringify(library));
        // Show toast
        showToast('Added to Library');
    }
}

function shareSong(songId) {
    const url = `${window.location.origin}/player/${songId}`;
    if (navigator.share) {
        navigator.share({ title: 'Check out this song!', url });
    } else {
        navigator.clipboard.writeText(url);
        showToast('Link copied to clipboard');
    }
}

function downloadSong(songId) {
    showToast('Download started...');
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 110px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--primary);
        color: var(--bg);
        padding: 12px 25px;
        border-radius: 25px;
        font-weight: 600;
        z-index: 9999;
        animation: fadeInUp 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
          }
          
