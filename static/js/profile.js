// Profile page event handlers
(function() {
    'use strict';

    function initProfilePage() {
        var profilePage = document.getElementById('profilePage');
        if (!profilePage) return;

        // Song row clicks
        profilePage.querySelectorAll('.song-row').forEach(function(row) {
            row.addEventListener('click', function(e) {
                if (e.target.closest('.favorite-btn')) return;
                
                var songData = {
                    id: this.dataset.songId,
                    title: this.dataset.songTitle,
                    artist: this.dataset.songArtist,
                    image: this.dataset.songImage || '/static/icon-512.png',
                    url: this.dataset.songUrl || ''
                };
                
                playSongData(songData);
            });
        });

        // Song card clicks
        profilePage.querySelectorAll('.song-card').forEach(function(card) {
            card.addEventListener('click', function(e) {
                var songData = {
                    id: this.dataset.songId,
                    title: this.dataset.songTitle,
                    artist: this.dataset.songArtist,
                    image: this.dataset.songImage || '/static/icon-512.png',
                    url: this.dataset.songUrl || ''
                };
                
                playSongData(songData);
            });
        });

        // Favorite buttons
        profilePage.querySelectorAll('.favorite-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var songId = this.dataset.songId;
                var row = this.closest('.song-row');
                var songData = {
                    song_id: songId,
                    title: row ? row.dataset.songTitle : 'Unknown',
                    artist: row ? row.dataset.songArtist : 'Unknown',
                    image_url: row ? row.dataset.songImage : '',
                    audio_url: row ? row.dataset.songUrl : '',
                    source: 'jiosaavn'
                };
                
                fetch('/api/favorite', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(songData)
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.success && typeof showToast === 'function') {
                        showToast(data.action === 'added' ? 'Added to favorites' : 'Removed from favorites', 'success');
                    }
                })
                .catch(function(e) {
                    if (typeof showToast === 'function') showToast('Network error', 'error');
                });
            });
        });
    }

    function playSongData(songData) {
        if (window.EvaPlayer && typeof window.EvaPlayer.play === 'function') {
            window.EvaPlayer.play(songData);
        }

        var thumb = document.getElementById('musicBarThumb');
        var title = document.getElementById('musicBarTitle');
        var artist = document.getElementById('musicBarArtist');
        var bar = document.getElementById('musicBar');

        if (thumb) thumb.src = songData.image;
        if (title) title.textContent = songData.title;
        if (artist) artist.textContent = songData.artist || '-';
        if (bar) bar.classList.remove('hidden');

        var icon = document.getElementById('musicBarPlayIcon');
        if (icon) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
        }

        localStorage.setItem('evamusic_currentSong', JSON.stringify(songData));
        if (typeof showToast === 'function') showToast('Now playing: ' + songData.title, 'success');
    }

    // Make shareProfile global
    window.shareProfile = function() {
        var url = window.location.href;
        if (navigator.share) {
            navigator.share({ title: 'My EvaMusic Profile', url: url });
        } else if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(function() {
                if (typeof showToast === 'function') showToast('Profile link copied!', 'success');
            });
        }
    };

    // Initialize on DOM ready and after SPA navigation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initProfilePage);
    } else {
        initProfilePage();
    }

    // Also re-init after SPA page swap
    document.addEventListener('spa:navigate', initProfilePage);
})();
              
