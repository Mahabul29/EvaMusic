// EvaMusic - Profile Edit Page JavaScript
(function() {
    'use strict';

    // ── Avatar Selection ──────────────────────────────
    window.selectAvatar = function(el) {
        document.querySelectorAll('.avatar-option').forEach(function(opt) {
            opt.classList.remove('selected');
        });
        el.classList.add('selected');
        var avatarUrl = el.dataset.avatar;
        var input = document.getElementById('avatarInput');
        if (input) input.value = avatarUrl;
    };

    // ── Theme Selection ───────────────────────────────
    window.selectTheme = function(el) {
        document.querySelectorAll('.theme-option').forEach(function(opt) {
            opt.classList.remove('selected');
        });
        el.classList.add('selected');
        var theme = el.dataset.theme;
        var input = document.getElementById('themeInput');
        if (input) input.value = theme;
    };

    // ── Color Selection ───────────────────────────────
    window.selectColor = function(el) {
        document.querySelectorAll('.color-option').forEach(function(opt) {
            opt.classList.remove('selected');
            opt.innerHTML = '';
        });
        el.classList.add('selected');
        el.innerHTML = '<i class="fas fa-check"></i>';
        var color = el.dataset.color;
        var input = document.getElementById('accentInput');
        if (input) input.value = color;
    };

    // ── Bio Character Counter ─────────────────────────
    function initBioCounter() {
        var bio = document.querySelector('textarea[name="bio"]');
        var counter = document.getElementById('bioCounter');
        if (!bio || !counter) return;

        function update() {
            var len = bio.value.length;
            counter.textContent = len + '/150';
            if (len > 135) {
                counter.style.color = '#FF6B6B';
            } else {
                counter.style.color = 'var(--text-secondary, #b3b3b3)';
            }
        }
        bio.addEventListener('input', update);
        update();
    }

    // ── Save Profile ──────────────────────────────────
    window.saveProfile = function(event) {
        event.preventDefault();
        var form = document.getElementById('editProfileForm');
        if (!form) return;

        var formData = new FormData(form);
        var data = {};
        formData.forEach(function(value, key) {
            data[key] = value;
        });

        // Collect toggle states
        var notifications = form.querySelector('input[name="notifications"]');
        var autoPlay = form.querySelector('input[name="auto_play"]');
        data.notifications = notifications ? notifications.checked : false;
        data.auto_play = autoPlay ? autoPlay.checked : false;

        showToast('Saving profile...', 'info');

        fetch('/api/profile/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(function(res) { return res.json(); })
        .then(function(result) {
            if (result.success) {
                showToast('Profile saved!', 'success');
                setTimeout(function() {
                    window.location.href = '/profile';
                }, 800);
            } else {
                showToast(result.message || 'Failed to save', 'error');
            }
        })
        .catch(function(err) {
            console.error(err);
            showToast('Network error. Please try again.', 'error');
        });
    };

    // ── Delete Account ────────────────────────────────
    window.confirmDelete = function() {
        if (confirm('Are you sure? This will permanently delete your account and all data.')) {
            fetch('/api/profile/delete', { method: 'POST' })
            .then(function(res) { return res.json(); })
            .then(function(result) {
                if (result.success) {
                    showToast('Account deleted', 'success');
                    setTimeout(function() { window.location.href = '/'; }, 1000);
                } else {
                    showToast(result.message || 'Failed to delete', 'error');
                }
            })
            .catch(function() {
                showToast('Network error', 'error');
            });
        }
    };

    // ── Toast Helper ──────────────────────────────────
    window.showToast = function(message, type) {
        document.querySelectorAll('.toast').forEach(function(t) { t.remove(); });
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = message;
        document.body.appendChild(toast);
        requestAnimationFrame(function() {
            toast.classList.add('show');
        });
        setTimeout(function() {
            toast.classList.remove('show');
            setTimeout(function() { toast.remove(); }, 300);
        }, 3000);
    };

    // ── Init ──────────────────────────────────────────
    function init() {
        initBioCounter();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
