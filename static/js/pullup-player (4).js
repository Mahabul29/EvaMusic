class PullUpPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentSong = null;
        this.isPlaying = false;
        this.isShuffle = false;
        this.repeatMode = 0;
        this.queue = [];
        this.currentIndex = 0;
        this.miniPlayer = document.getElementById('miniPlayer');
        this.fullPlayer = document.getElementById('fullPlayer');
        this.progressBar = document.getElementById('progressBar');
        this.progressContainer = document.getElementById('progressContainer');
        this.currentTimeEl = document.getElementById('currentTime');
        this.totalTimeEl = document.getElementById('totalTime');
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
    getTitle(song) { return song ? (song.title || song.name || 'Unknown') : 'Unknown'; }
    getArtist(song) { return song ? (song.artist || song.primaryArtists || 'Unknown') : 'Unknown'; }
    getId(song) { return song ? (song.id || song.song_id || '') : ''; }
    init() {
        this.miniPlayer.addEventListener('click', (e) => {
            if (!e.target.closest('.mini-player-btn')) this.expandPlayer();
        });
        let startY = 0;
        this.miniPlayer.addEventListener('touchstart', (e) => { startY = e.touches[0].clientY; }, { passive: true });
        this.miniPlayer.addEventListener('touchmove', (e) => { if (startY - e.touches[0].clientY > 50) this.expandPlayer(); }, { passive: true });
        let fullStartY = 0;
        this.fullPlayer.addEventListener('touchstart', (e) => { fullStartY = e.touches[0].clientY; }, { passive: true });
        this.fullPlayer.addEventListener('touchmove', (e) => { if (e.touches[0].clientY - fullStartY > 100) this.collapsePlayer(); }, { passive: true });
        this.progressContainer.addEventListener('click', (e) => {
            const rect = this.progressContainer.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('error', () => showToast('Failed to load audio', 'error'));
    }
    playSong(songId, songData) {
        console.log('Playing:', songId);
        this.currentSong = songData;
        const audioUrl = this.getAudioUrl(songData);
        if (!audioUrl) { showToast('No audio URL', 'error'); return; }
        this.currentIndex = this.queue.findIndex(s => this.getId(s) === songId);
        if (this.currentIndex === -1) { this.queue.push(songData); this.currentIndex = this.queue.length - 1; }
        this.audio.src = audioUrl;
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updateUI();
            this.showMiniPlayer();
            showToast('Now Playing: ' + this.getTitle(songData), 'success');
        }).catch(() => showToast('Failed to play', 'error'));
    }
    updateUI() {
        if (!this.currentSong) return;
        const title = this.getTitle(this.currentSong);
        const artist = this.getArtist(this.currentSong);
        const image = this.getImageUrl(this.currentSong);
        const miniThumb = document.getElementById('miniThumb');
        const miniTitle = document.getElementById('miniTitle');
        const miniArtist = document.getElementById('miniArtist');
        if (miniThumb) miniThumb.src = image;
        if (miniTitle) miniTitle.textContent = title;
        if (miniArtist) miniArtist.textContent = artist;
        const fullThumb = document.getElementById('fullThumb');
        const fullTitle = document.getElementById('fullTitle');
        const fullArtist = document.getElementById('fullArtist');
        if (fullThumb) fullThumb.src = image;
        if (fullTitle) fullTitle.textContent = title;
        if (fullArtist) fullArtist.textContent = artist;
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';
        document.querySelectorAll('.play-icon').forEach(el => { el.className = `fas ${icon} play-icon`; });
        const artwork = document.getElementById('fullArtwork');
        if (artwork) artwork.classList.toggle('playing', this.isPlaying);
    }
    togglePlay() {
        if (!this.currentSong) return;
        if (this.isPlaying) { this.audio.pause(); this.isPlaying = false; }
        else { this.audio.play().then(() => this.isPlaying = true).catch(() => {}); }
        this.updateUI();
    }
    showMiniPlayer() { this.miniPlayer.classList.add('active'); }
    expandPlayer() { if (!this.currentSong) return; this.fullPlayer.classList.add('active'); document.body.style.overflow = 'hidden'; }
    collapsePlayer() { this.fullPlayer.classList.remove('active'); document.body.style.overflow = ''; }
    updateProgress() {
        if (!this.audio.duration) return;
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        if (this.progressBar) this.progressBar.style.width = percent + '%';
        if (this.currentTimeEl) this.currentTimeEl.textContent = this.formatTime(this.audio.currentTime);
    }
    updateDuration() { if (this.totalTimeEl) this.totalTimeEl.textContent = this.formatTime(this.audio.duration); }
    seek(percent) { if (!this.audio.duration) return; this.audio.currentTime = percent * this.audio.duration; }
    handleEnded() {
        if (this.repeatMode === 2) { this.audio.currentTime = 0; this.audio.play(); }
        else if (this.isShuffle) this.playRandom();
        else if (this.currentIndex < this.queue.length - 1) this.next();
        else if (this.repeatMode === 1) { this.currentIndex = 0; this.playSong(this.getId(this.queue[0]), this.queue[0]); }
        else { this.isPlaying = false; this.updateUI(); }
    }
    next() {
        if (this.isShuffle) this.playRandom();
        else if (this.currentIndex < this.queue.length - 1) { this.currentIndex++; this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]); }
    }
    previous() {
        if (this.audio.currentTime > 3) this.audio.currentTime = 0;
        else if (this.currentIndex > 0) { this.currentIndex--; this.playSong(this.getId(this.queue[this.currentIndex]), this.queue[this.currentIndex]); }
    }
    playRandom() {
        if (this.queue.length <= 1) return;
        let newIndex; do { newIndex = Math.floor(Math.random() * this.queue.length); } while (newIndex === this.currentIndex);
        this.currentIndex = newIndex; this.playSong(this.getId(this.queue[newIndex]), this.queue[newIndex]);
    }
    toggleShuffle() { this.isShuffle = !this.isShuffle; document.querySelector('.shuffle-btn')?.classList.toggle('active', this.isShuffle); showToast(this.isShuffle ? 'Shuffle on' : 'Shuffle off', 'info'); }
    toggleRepeat() { this.repeatMode = (this.repeatMode + 1) % 3; const modes = ['Repeat off', 'Repeat all', 'Repeat one']; showToast(modes[this.repeatMode], 'info'); document.querySelector('.repeat-btn')?.classList.toggle('active', this.repeatMode > 0); }
    toggleFavorite() { if (!this.currentSong) return; showToast('Added to favorites', 'success'); }
    shareSong() { if (!this.currentSong) return; const url = window.location.origin + '/player/' + this.getId(this.currentSong); if (navigator.share) navigator.share({ title: this.getTitle(this.currentSong), url: url }); else navigator.clipboard.writeText(url).then(() => showToast('Link copied!', 'success')); }
    formatTime(seconds) { if (!seconds || isNaN(seconds)) return '0:00'; const mins = Math.floor(seconds / 60); const secs = Math.floor(seconds % 60); return `${mins}:${secs.toString().padStart(2, '0')}`; }
}
const player = new PullUpPlayer();
function playSong(songId, songData) { player.playSong(songId, songData); }
function togglePlay() { player.togglePlay(); }
function nextSong() { player.next(); }
function previousSong() { player.previous(); }
function toggleShuffle() { player.toggleShuffle(); }
function toggleRepeat() { player.toggleRepeat(); }
function toggleFavorite() { player.toggleFavorite(); }
function shareSong() { player.shareSong(); }
function expandPlayer() { player.expandPlayer(); }
function collapsePlayer() { player.collapsePlayer(); }
function showToast(message, type = 'info') {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.style.opacity = '1'; toast.style.transform = 'translateX(-50%) translateY(0)'; });
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(-50%) translateY(20px)'; setTimeout(() => toast.remove(), 300); }, 2000);
}