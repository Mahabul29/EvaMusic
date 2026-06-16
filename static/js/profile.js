// profile.js — EvaMusic profile page functionality

document.addEventListener('DOMContentLoaded', function() {
    loadProfileStats();
    loadProfileFavorites();
    loadProfilePlaylists();
});

function loadProfileStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            const favEl = document.getElementById('stat-favorites');
            const playEl = document.getElementById('stat-playlists');
            const hoursEl = document.getElementById('stat-hours');

            if (favEl) favEl.textContent = data.total_favorites || 0;
            if (playEl) playEl.textContent = data.total_playlists || 0;
            if (hoursEl) hoursEl.textContent = (data.listening_hours || 0).toFixed(1);
        })
        .catch(e => console.log('Stats load error:', e));
}

function loadProfileFavorites() {
    fetch('/api/favorites')
        .then(r => r.json())
        .then(songs => {
            const container = document.getElementById('profile-favorites');
            if (!container) return;

            if (!songs || songs.length === 0) {
                container.innerHTML = '<p class="text-gray-400 text-sm">No favorites yet</p>';
                return;
            }

            container.innerHTML = songs.slice(0, 5).map(song => `
                <div class="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                    <img src="${song.image_url || '/static/images/default-album.png'}" 
                         class="w-10 h-10 rounded object-cover"
                         onerror="this.src='/static/images/default-album.png'">
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium truncate">${song.title || 'Unknown'}</p>
                        <p class="text-xs text-gray-400 truncate">${song.artist || 'Unknown'}</p>
                    </div>
                </div>
            `).join('');
        })
        .catch(e => console.log('Favorites load error:', e));
}

function loadProfilePlaylists() {
    fetch('/api/playlists')
        .then(r => r.json())
        .then(playlists => {
            const container = document.getElementById('profile-playlists');
            if (!container) return;

            if (!playlists || playlists.length === 0) {
                container.innerHTML = '<p class="text-gray-400 text-sm">No playlists yet</p>';
                return;
            }

            container.innerHTML = playlists.slice(0, 5).map(pl => `
                <div class="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                    <div class="w-10 h-10 rounded bg-purple-500/20 flex items-center justify-center">
                        <svg class="w-5 h-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"/>
                        </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium truncate">${pl.name || 'My Playlist'}</p>
                        <p class="text-xs text-gray-400">${pl.song_count || 0} songs</p>
                    </div>
                </div>
            `).join('');
        })
        .catch(e => console.log('Playlists load error:', e));
}

// Edit profile form handling
function initEditProfile() {
    const form = document.getElementById('edit-profile-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const data = {
            display_name: document.getElementById('display_name')?.value,
            bio: document.getElementById('bio')?.value,
            avatar_url: document.querySelector('input[name="avatar"]:checked')?.value
        };

        fetch('/api/profile/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showToast('Profile updated!');
                setTimeout(() => window.location.href = '/profile', 500);
            } else {
                showToast(result.message || 'Update failed');
            }
        })
        .catch(e => {
            console.error('Update error:', e);
            showToast('Something went wrong');
        });
    });
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-20 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-2 rounded-full text-sm z-50 animate-fade-in';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

// Initialize edit profile if on edit page
if (document.getElementById('edit-profile-form')) {
    initEditProfile();
}
