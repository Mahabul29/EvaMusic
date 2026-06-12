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
        return song.url || 
               song.downloadUrl || 
               song.media_url || 
               song.audio_url || 
               (song.downloadUrl && song.downloadUrl[0] && song.downloadUrl[0].link) ||
               (song.media_url && song.media_url[0] && song.media_url[0].link) ||
               '';
    }

    getImageUrl(song) {
        if (!song) return '/static/images/default-album.png';

        let img = song.image || song.image_url || song.thumbnail || song.cover || '';

        if (Array.isArray(img)) {
            img = img[img.length - 1] || img[0] || '';
        }

        if (typeof img === 'object' && img.link) {
            img = img.link;
        }

        return img || '/static/images/default-album.png';
    }

    getTitle(song) {
        if (!song) return 'Unknown';
        return song.title || song.name || song.song || 'Unknown Song';
    }

    getArtist(song) {
        if (!song) return 'Unknown Artist';
        return song.artist || 
               song.primaryArtists || 
               song.singers || 
               song.artists || 
               'Unknown Artist';
    }

    getId(song) {
        if (!song) return '';
        return song.id || song.song_id || '';
    }

    init() {
        this.miniPlayer.addEventListener('click', (e) => {
            if (!e.target.closest('.mini-player-btn')) {
                this.expandPlayer();
            }
        });

        let startY = 0;

        this.miniPlayer.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
        }, { passive: true });

        this.miniPlayer.addEventListener('touchmove', (e) => {
            const deltaY = startY - e.touches[0].clientY;

            if (deltaY > 50) {
                this.expandPlayer();
            }
        }, { passive: true });

        let fullStartY = 0;

        this.fullPlayer.addEventListener('touchstart', (e) => {
            fullStartY = e.touches[0].clientY;
        }, { passive: true });

        this.fullPlayer.addEventListener('touchmove', (e) => {
            const deltaY = e.touches[0].clientY - fullStartY;

            if (deltaY > 100) {
                this.collapsePlayer();
            }
        }, { passive: true });

        this.progressContainer.addEventListener('click', (e) => {
            const rect = this.progressContainer.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            this.seek(percent);
        });

        this.audio.addEventListener(
            'timeupdate',
            () => this.updateProgress()
        );

        this.audio.addEventListener(
            'ended',
            () => this.handleEnded()
        );

        this.audio.addEventListener(
            'loadedmetadata',
            () => this.updateDuration()
        );

        this.audio.addEventListener('error', (e) => {
            console.error('Audio error:', e);
            showToast('❌ Failed to load audio', 'error');
        });

        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.currentSong) {
                e.preventDefault();
                this.togglePlay();
            }
        });
    }

    playSong(songId, songData) {
        console.log('Playing song:', songId, songData);

        this.currentSong = songData;

        const audioUrl = this.getAudioUrl(songData);

        if (!audioUrl) {
            showToast('❌ No audio URL found', 'error');
            console.error('No audio URL in:', songData);
            return;
        }

        this.currentIndex = this.queue.findIndex(
            s => this.getId(s) === songId
        );

        if (this.currentIndex === -1) {
            this.queue.push(songData);
            this.currentIndex = this.queue.length - 1;
        }

        this.audio.src = audioUrl;

        this.audio.play()
            .then(() => {
                this.isPlaying = true;
                this.updateUI();
                this.showMiniPlayer();

                showToast(
                    '▶️ Now Playing: ' +
                    this.getTitle(songData),
                    'success'
                );
            })
            .catch(err => {
                console.error('Play error:', err);
                showToast(
                    '❌ Failed to play audio',
                    'error'
                );
            });
}

updateUI() {
        if (!this.currentSong) return;

        const title = this.getTitle(this.currentSong);
        const artist = this.getArtist(this.currentSong);
        const image = this.getImageUrl(this.currentSong);

        const miniThumb =
            document.getElementById('miniThumb');

        const miniTitle =
            document.getElementById('miniTitle');

        const miniArtist =
            document.getElementById('miniArtist');

        if (miniThumb) miniThumb.src = image;
        if (miniTitle) miniTitle.textContent = title;
        if (miniArtist) miniArtist.textContent = artist;

        const fullThumb =
            document.getElementById('fullThumb');

        const fullTitle =
            document.getElementById('fullTitle');

        const fullArtist =
            document.getElementById('fullArtist');

        if (fullThumb) fullThumb.src = image;
        if (fullTitle) fullTitle.textContent = title;
        if (fullArtist) fullArtist.textContent = artist;

        const icon =
            this.isPlaying
                ? 'fa-pause'
                : 'fa-play';

        document
            .querySelectorAll('.play-icon')
            .forEach(el => {
                el.className =
                    `fas ${icon} play-icon`;
            });

        const artwork =
            document.getElementById(
                'fullArtwork'
            );

        if (artwork) {
            artwork.classList.toggle(
                'playing',
                this.isPlaying
            );
        }
    }

    togglePlay() {
        if (!this.currentSong) return;

        if (this.isPlaying) {
            this.audio.pause();
            this.isPlaying = false;
        } else {
            this.audio.play()
                .then(() => {
                    this.isPlaying = true;
                })
                .catch(err => {
                    console.error(
                        'Resume error:',
                        err
                    );
                });
        }

        this.updateUI();
    }

    showMiniPlayer() {
        this.miniPlayer
            .classList
            .add('active');
    }

    hideMiniPlayer() {
        this.miniPlayer
            .classList
            .remove('active');
    }

    expandPlayer() {
        if (!this.currentSong) return;

        this.fullPlayer
            .classList
            .add('active');

        document.body
            .style
            .overflow = 'hidden';
    }

    collapsePlayer() {
        this.fullPlayer
            .classList
            .remove('active');

        document.body
            .style
            .overflow = '';
    }

    updateProgress() {
        if (!this.audio.duration) return;

        const percent =
            (
                this.audio.currentTime /
                this.audio.duration
            ) * 100;

        if (this.progressBar) {
            this.progressBar.style.width =
                percent + '%';
        }

        if (this.currentTimeEl) {
            this.currentTimeEl.textContent =
                this.formatTime(
                    this.audio.currentTime
                );
        }
    }

    updateDuration() {
        if (this.totalTimeEl) {
            this.totalTimeEl.textContent =
                this.formatTime(
                    this.audio.duration
                );
        }
    }

    seek(percent) {
        if (!this.audio.duration) return;

        this.audio.currentTime =
            percent *
            this.audio.duration;
    }

    handleEnded() {
        if (this.repeatMode === 2) {
            this.audio.currentTime = 0;
            this.audio.play();

        } else if (
            this.isShuffle
        ) {
            this.playRandom();

        } else if (
            this.currentIndex <
            this.queue.length - 1
        ) {
            this.next();

        } else if (
            this.repeatMode === 1
        ) {
            this.currentIndex = 0;

            this.playSong(
                this.getId(
                    this.queue[0]
                ),
                this.queue[0]
            );

        } else {
            this.isPlaying = false;
            this.updateUI();
        }
    }

    next() {
        if (this.isShuffle) {
            this.playRandom();

        } else if (
            this.currentIndex <
            this.queue.length - 1
        ) {
            this.currentIndex++;

            const song =
                this.queue[
                    this.currentIndex
                ];

            this.playSong(
                this.getId(song),
                song
            );
        }
    }

    previous() {
        if (
            this.audio.currentTime > 3
        ) {
            this.audio.currentTime = 0;

        } else if (
            this.currentIndex > 0
        ) {
            this.currentIndex--;

            const song =
                this.queue[
                    this.currentIndex
                ];

            this.playSong(
                this.getId(song),
                song
            );
        }
    }

    playRandom() {
        if (
            this.queue.length <= 1
        ) return;

        let newIndex;

        do {
            newIndex =
                Math.floor(
                    Math.random() *
                    this.queue.length
                );

        } while (
            newIndex ===
            this.currentIndex
        );

        this.currentIndex =
            newIndex;

        this.playSong(
            this.getId(
                this.queue[newIndex]
            ),
            this.queue[newIndex]
        );
    }

    toggleShuffle() {
        this.isShuffle =
            !this.isShuffle;

        const btn =
            document.querySelector(
                '.shuffle-btn'
            );

        if (btn) {
            btn.classList.toggle(
                'active',
                this.isShuffle
            );
        }

        showToast(
            this.isShuffle
                ? '🔀 Shuffle on'
                : '🔀 Shuffle off',
            'info'
        );
    }

    toggleRepeat() {
        this.repeatMode =
            (this.repeatMode + 1) % 3;

        const modes = [
            '🔁 Repeat off',
            '🔁 Repeat all',
            '🔂 Repeat one'
        ];

        showToast(
            modes[
                this.repeatMode
            ],
            'info'
        );

        const btn =
            document.querySelector(
                '.repeat-btn'
            );

        if (btn) {
            btn.classList.toggle(
                'active',
                this.repeatMode > 0
            );
        }
    }

    toggleFavorite() {
        if (!this.currentSong) return;

        showToast(
            '❤️ Added to favorites',
            'success'
        );
    }

    shareSong() {
        if (!this.currentSong) return;

        const url =
            window.location.origin +
            '/player/' +
            this.getId(
                this.currentSong
            );

        if (navigator.share) {
            navigator.share({
                title:
                    this.getTitle(
                        this.currentSong
                    ),
                url: url
            });

        } else {
            navigator.clipboard
                .writeText(url)
                .then(() => {
                    showToast(
                        '🔗 Link copied!',
                        'success'
                    );
                });
        }
    }

    formatTime(seconds) {
        if (
            !seconds ||
            isNaN(seconds)
        ) {
            return '0:00';
        }

        const mins =
            Math.floor(
                seconds / 60
            );

        const secs =
            Math.floor(
                seconds % 60
            );

        return `${mins}:${secs
            .toString()
            .padStart(2, '0')}`;
    }
}

const player =
    new PullUpPlayer();

function playSong(
    songId,
    songData
) {
    player.playSong(
        songId,
        songData
    );
}

function togglePlay() {
    player.togglePlay();
}

function nextSong() {
    player.next();
}

function previousSong() {
    player.previous();
}

function toggleShuffle() {
    player.toggleShuffle();
}

function toggleRepeat() {
    player.toggleRepeat();
}

function toggleFavorite() {
    player.toggleFavorite();
}

function shareSong() {
    player.shareSong();
}

function expandPlayer() {
    player.expandPlayer();
}

function collapsePlayer() {
    player.collapsePlayer();
}

function showToast(
    message,
    type = 'info'
) {
    document
        .querySelectorAll(
            '.toast'
        )
        .forEach(t => t.remove());

    const toast =
        document.createElement(
            'div'
        );

    toast.className =
        `toast toast-${type}`;

    toast.textContent =
        message;

    document.body
        .appendChild(
            toast
        );

    requestAnimationFrame(
        () => {
            toast.style.opacity =
                '1';

            toast.style.transform =
                'translateX(-50%) translateY(0)';
        }
    );

    setTimeout(() => {
        toast.style.opacity =
            '0';

        toast.style.transform =
            'translateX(-50%) translateY(20px)';

        setTimeout(
            () => toast.remove(),
            300
        );
    }, 2000);
                  }
