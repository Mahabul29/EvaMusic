<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#1DB954">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>{% block title %}EvaMusic{% endblock %}</title>

    <link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}">
    <link rel="apple-touch-icon" href="{{ url_for('static', filename='images/logo/icon-192x192.png') }}">
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='images/logo.png') }}">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        :root {
            --bg-color: #121212; --text-color: #ffffff; --text-secondary: #b3b3b3;
            --card-bg: #1e1e1e; --hover-bg: #2a2a2a; --border-color: #333;
            --accent-color: #1DB954; --nav-bg: #1a1a1a; --nav-active: #1DB954; --nav-inactive: #888;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-color); color: var(--text-color);
            min-height: 100vh; padding-bottom: calc(70px + env(safe-area-inset-bottom, 0px)); overflow-x: hidden;
        }
        .toast {
            position: fixed; bottom: 90px; left: 50%;
            transform: translateX(-50%) translateY(20px);
            padding: 12px 24px; border-radius: 24px;
            font-size: 14px; font-weight: 500; color: white;
            z-index: 1000; opacity: 0; transition: all 0.3s ease;
            pointer-events: none; white-space: nowrap;
        }
        .toast-success { background: #1DB954; }
        .toast-error { background: #ef4444; }
        .toast-info { background: #3b82f6; }
    </style>

    <link rel="stylesheet" href="{{ url_for('static', filename='css/bottom-nav.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/pullup-player.css') }}">

    {% block extra_css %}{% endblock %}

    <script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/sw/service-worker.js')
                .then(reg => console.log('[SW] Registered'))
                .catch(err => console.log('[SW] Failed:', err));
        });
    }
    </script>
</head>
<body>
    <div class="main-content">
        {% block content %}{% endblock %}
    </div>

    <div class="mini-player" id="miniPlayer">
        <img src="/static/images/default-album.png" alt="" class="mini-player-thumb" id="miniThumb">
        <div class="mini-player-info">
            <div class="mini-player-title" id="miniTitle">Select a song</div>
            <div class="mini-player-artist" id="miniArtist">-</div>
        </div>
        <div class="mini-player-controls">
            <button class="mini-player-btn" onclick="event.stopPropagation(); previousSong()">
                <i class="fas fa-step-backward"></i>
            </button>
            <button class="mini-player-btn play-btn" onclick="event.stopPropagation(); togglePlay()">
                <i class="fas fa-play play-icon"></i>
            </button>
            <button class="mini-player-btn" onclick="event.stopPropagation(); nextSong()">
                <i class="fas fa-step-forward"></i>
            </button>
        </div>
    </div>

 .mini-player {
    position: fixed; bottom: 60px; left: 0; right: 0;
    height: 64px; background: var(--card-bg, #1e1e1e);
    border-top: 1px solid var(--border-color, #333);
    display: flex; align-items: center;
    padding: 0 16px; gap: 12px; z-index: 99;
    transform: translateY(100%); transition: transform 0.3s ease;
    cursor: pointer;
}
.mini-player.active { transform: translateY(0); }
.mini-player-thumb { width: 48px; height: 48px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.mini-player-info { flex: 1; min-width: 0; overflow: hidden; }
.mini-player-title { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-color, #fff); }
.mini-player-artist { font-size: 12px; color: var(--text-secondary, #b3b3b3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mini-player-controls { display: flex; align-items: center; gap: 16px; }
.mini-player-btn { background: none; border: none; color: var(--text-color, #fff); font-size: 20px; cursor: pointer; padding: 8px; display: flex; align-items: center; justify-content: center; }
.mini-player-btn.play-btn { width: 40px; height: 40px; background: var(--accent-color, #1DB954); border-radius: 50%; color: white; }

.full-player {
    position: fixed; inset: 0; background: var(--bg-color, #121212);
    z-index: 200; transform: translateY(100%);
    transition: transform 0.4s cubic-bezier(0.32, 0.72, 0, 1);
    display: flex; flex-direction: column; overflow: hidden;
}
.full-player.active { transform: translateY(0); }

.full-player-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 20px; padding-top: calc(16px + env(safe-area-inset-top, 0px));
}
.full-player-header .down-btn { background: none; border: none; color: var(--text-color, #fff); font-size: 24px; cursor: pointer; padding: 8px; }
.full-player-header .queue-btn { background: none; border: none; color: var(--text-color, #fff); font-size: 20px; cursor: pointer; padding: 8px; }
.full-player-header h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary, #b3b3b3); text-transform: uppercase; letter-spacing: 1px; }

.full-player-content {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 20px; gap: 32px;
}
.full-player-artwork { width: 280px; height: 280px; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.5); position: relative; }
.full-player-artwork img { width: 100%; height: 100%; object-fit: cover; }
.full-player-artwork .vinyl-disc { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; background: #000; border-radius: 50%; border: 4px solid #333; display: none; }
.full-player-artwork.playing .vinyl-disc { display: block; animation: spin 3s linear infinite; }
@keyframes spin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
.full-player-details { text-align: center; width: 100%; }
.full-player-title { font-size: 24px; font-weight: 700; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.full-player-artist { font-size: 16px; color: var(--text-secondary, #b3b3b3); }

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
    
    init() {
        this.miniPlayer.addEventListener('click', (e) => {
            if (!e.target.closest('.mini-player-btn')) this.expandPlayer();
        });
        let startY = 0;
        this.miniPlayer.addEventListener('touchstart', (e) => { startY = e.touches[0].clientY; }, { passive: true });
        this.miniPlayer.addEventListener('touchmove', (e) => {
            if (startY - e.touches[0].clientY > 50) this.expandPlayer();
        }, { passive: true });
        let fullStartY = 0;
        this.fullPlayer.addEventListener('touchstart', (e) => { fullStartY = e.touches[0].clientY; }, { passive: true });
        this.fullPlayer.addEventListener('touchmove', (e) => {
            if (e.touches[0].clientY - fullStartY > 100) this.collapsePlayer();
        }, { passive: true });
        this.progressContainer.addEventListener('click', (e) => {
            const rect = this.progressContainer.getBoundingClientRect();
            this.seek((e.clientX - rect.left) / rect.width);
        });
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.currentSong) { e.preventDefault(); this.togglePlay(); }
        });
    }
    
    playSong(songId, songData) {
        this.currentSong = songData;
        this.currentIndex = this.queue.findIndex(s => s.id === songId);
        if (this.currentIndex === -1) { this.queue.push(songData); this.currentIndex = this.queue.length - 1; }
        this.audio.src = songData.url || songData.downloadUrl || songData.media_url;
        this.audio.play(); this.isPlaying = true;
        this.updateUI(); this.showMiniPlayer();
    }
    
    updateUI() {
        if (!this.currentSong) return;
        const title = this.currentSong.title || this.currentSong.name || 'Unknown';
        const artist = this.currentSong.artist || this.currentSong.primaryArtists || 'Unknown Artist';
        const image = this.currentSong.image || this.currentSong.image_url || '/static/images/default-album.png';
        document.getElementById('miniThumb').src = image;
        document.getElementById('miniTitle').textContent = title;
        document.getElementById('miniArtist').textContent = artist;
        document.getElementById('fullThumb').src = image;
        document.getElementById('fullTitle').textContent = title;
        document.getElementById('fullArtist').textContent = artist;
        const icon = this.isPlaying ? 'fa-pause' : 'fa-play';
        document.querySelectorAll('.play-icon').forEach(el => { el.className = `fas ${icon} play-icon`; });
        const artwork = document.getElementById('fullArtwork');
        artwork.classList.toggle('playing', this.isPlaying);
    }
    
    togglePlay() {
        if (!this.currentSong) return;
        if (this.isPlaying) { this.audio.pause(); this.isPlaying = false; }
        else { this.audio.play(); this.isPlaying = true; }
        this.updateUI();
    }
    
    showMiniPlayer() { this.miniPlayer.classList.add('active'); }
    hideMiniPlayer() { this.miniPlayer.classList.remove('active'); }
    expandPlayer() { if (!this.currentSong) return; this.fullPlayer.classList.add('active'); document.body.style.overflow = 'hidden'; }
    collapsePlayer() { this.fullPlayer.classList.remove('active'); document.body.style.overflow = ''; }
    
    updateProgress() {
        if (!this.audio.duration) return;
        this.progressBar.style.width = (this.audio.currentTime / this.audio.duration * 100) + '%';
        this.currentTimeEl.textContent = this.formatTime(this.audio.currentTime);
    }
    
    updateDuration() { this.totalTimeEl.textContent = this.formatTime(this.audio.duration); }
    seek(percent) { if (!this.audio.duration) return; this.audio.currentTime = percent * this.audio.duration; }
