(function() {
    'use strict';
    window.selectAvatar = function(el) {
        document.querySelectorAll('.avatar-option').forEach(function(o) { o.classList.remove('selected'); });
        el.classList.add('selected');
        var inp = document.getElementById('avatarInput');
        if (inp) inp.value = el.dataset.avatar;
    };
    window.selectTheme = function(el) {
        document.querySelectorAll('.theme-option').forEach(function(o) { o.classList.remove('selected'); });
        el.classList.add('selected');
        var inp = document.getElementById('themeInput');
        if (inp) inp.value = el.dataset.theme;
    };
    window.selectColor = function(el) {
        document.querySelectorAll('.color-option').forEach(function(o) { o.classList.remove('selected'); o.innerHTML = ''; });
        el.classList.add('selected');
        el.innerHTML = '<i class="fas fa-check"></i>';
        var inp = document.getElementById('accentInput');
        if (inp) inp.value = el.dataset.color;
    };
    function initBioCounter() {
        var bio = document.querySelector('textarea[name="bio"]');
        var counter = document.getElementById('bioCounter');
        if (!bio || !counter) return;
        function update() { var len = bio.value.length; counter.textContent = len + '/150'; counter.style.color = len > 135 ? '#FF6B6B' : 'var(--text-secondary, #b3b3b3)'; }
        bio.addEventListener('input', update); update();
    }
    window.saveProfile = function(event) {
        event.preventDefault();
        var form = document.getElementById('editProfileForm');
        if (!form) return;
        var formData = new FormData(form);
        var data = {};
        formData.forEach(function(v, k) { data[k] = v; });
        var n = form.querySelector('input[name="notifications"]');
        var a = form.querySelector('input[name="auto_play"]');
        data.notifications = n ? n.checked : false;
        data.auto_play = a ? a.checked : false;
        if (typeof showToast === 'function') showToast('Saving...', 'info');
        fetch('/api/profile/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function(r) { return r.json(); })
        .then(function(res) {
            if (res.success) { if (typeof showToast === 'function') showToast('Saved!', 'success'); setTimeout(function() { window.location.href = '/profile'; }, 800); }
            else { if (typeof showToast === 'function') showToast(res.message || 'Failed', 'error'); }
        })
        .catch(function() { if (typeof showToast === 'function') showToast('Network error', 'error'); });
    };
    window.confirmDelete = function() {
        if (confirm('Delete account permanently?')) {
            fetch('/api/profile/delete', { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function(res) { if (res.success) { if (typeof showToast === 'function') showToast('Deleted', 'success'); setTimeout(function() { window.location.href = '/'; }, 1000); } })
            .catch(function() { if (typeof showToast === 'function') showToast('Error', 'error'); });
        }
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBioCounter);
    else initBioCounter();
})();
