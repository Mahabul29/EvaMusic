// ─────────────────────────────────────────────────────────────────────────────
// media-session-patch.js
// Drop this function into pullup-player.js and call updateMediaSession()
// every time a new song starts playing.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Call this whenever a song starts (in playSong / barTogglePlay / etc.)
 * Pass the song object that your player already uses.
 *
 * Expected song fields (use whatever your backend sends):
 *   song.title, song.artist, song.album
 *   song.thumbnail || song.cover || song.image   ← any one will work
 */
function updateMediaSession(song, audioEl) {
    if (!('mediaSession' in navigator)) return;   // not supported — silent skip

    // ── 1. Metadata (title + thumbnail) ──────────────────────────────────────
    const artworkUrl =
        song.thumbnail ||
        song.cover     ||
        song.image     ||
        song.artwork   ||
        '/static/images/default-album.png';   // absolute fallback

    // MediaSession requires an absolute URL for artwork
    const absoluteArt = artworkUrl.startsWith('http')
        ? artworkUrl
        : (window.location.origin + (artworkUrl.startsWith('/') ? '' : '/') + artworkUrl);

    navigator.mediaSession.metadata = new MediaMetadata({
        title:  song.title  || 'Unknown Title',
        artist: song.artist || 'Unknown Artist',
        album:  song.album  || '',
        artwork: [
            { src: absoluteArt, sizes: '96x96',   type: 'image/jpeg' },
            { src: absoluteArt, sizes: '128x128',  type: 'image/jpeg' },
            { src: absoluteArt, sizes: '192x192',  type: 'image/jpeg' },
            { src: absoluteArt, sizes: '256x256',  type: 'image/jpeg' },
            { src: absoluteArt, sizes: '512x512',  type: 'image/jpeg' },
        ]
    });

    // ── 2. Action handlers (notification panel buttons) ───────────────────────
    navigator.mediaSession.setActionHandler('play', () => {
        audioEl.play();
        navigator.mediaSession.playbackState = 'playing';
    });

    navigator.mediaSession.setActionHandler('pause', () => {
        audioEl.pause();
        navigator.mediaSession.playbackState = 'paused';
    });

    // previoustrack / nexttrack — wire to your existing queue functions
    navigator.mediaSession.setActionHandler('previoustrack', () => {
        if (typeof window.player?.prevSong === 'function') {
            window.player.prevSong();
        } else if (typeof barPrev === 'function') {
            barPrev();
        }
    });

    navigator.mediaSession.setActionHandler('nexttrack', () => {
        if (typeof window.player?.nextSong === 'function') {
            window.player.nextSong();
        } else if (typeof barNext === 'function') {
            barNext();
        }
    });

    // seekto — lets the notification slider actually work
    navigator.mediaSession.setActionHandler('seekto', (details) => {
        if (details.seekTime !== undefined) {
            audioEl.currentTime = details.seekTime;
        }
    });

    // ── 3. Keep position-state in sync ───────────────────────────────────────
    function syncPosition() {
        if (!audioEl.duration) return;
        try {
            navigator.mediaSession.setPositionState({
                duration:     audioEl.duration,
                playbackRate: audioEl.playbackRate,
                position:     audioEl.currentTime,
            });
        } catch (_) { /* ignore if not supported */ }
    }

    // Update position every second and on key events
    audioEl.addEventListener('timeupdate', syncPosition, { passive: true });
    audioEl.addEventListener('play',  () => { navigator.mediaSession.playbackState = 'playing'; syncPosition(); });
    audioEl.addEventListener('pause', () => { navigator.mediaSession.playbackState = 'paused';  syncPosition(); });

    // Fire once immediately so the notification shows current state
    syncPosition();
    navigator.mediaSession.playbackState = audioEl.paused ? 'paused' : 'playing';
}


// ─────────────────────────────────────────────────────────────────────────────
// HOW TO INTEGRATE into pullup-player.js
// ─────────────────────────────────────────────────────────────────────────────
//
// Find wherever you call  audioEl.src = ...  or  audioEl.play()  after loading
// a new song, then add ONE line:
//
//     updateMediaSession(songData, audioEl);
//
// Example — inside your playSong() function:
//
//   playSong(id, songData) {
//       this.audio.src = songData.stream_url;
//       this.currentSong = songData;
//       this.audio.play();
//
//       updateMediaSession(songData, this.audio);   // ← add this line
//       syncMusicBar(songData);
//   }
//
// That's it. The notification panel will now show:
//   ✅  Song thumbnail / album art
//   ✅  Previous track button
//   ✅  Play / Pause button
//   ✅  Next track button
//   ✅  Seek slider synced to actual position
// ─────────────────────────────────────────────────────────────────────────────
             
