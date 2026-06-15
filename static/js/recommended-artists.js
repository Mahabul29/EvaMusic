// ═══════════════════════════════════════════════════════════════
// EvaMusic — Recommended Artists Section
// File: static/js/recommended-artists.js
// ═══════════════════════════════════════════════════════════════

(function () {
  'use strict';

  // ── Config ───────────────────────────────────────────────────
  const SECTION_ID   = 'evaRecommendedArtists';
  const MAX_ARTISTS  = 10;
  const CACHE_KEY    = 'evamusic_rec_artists';
  const CACHE_TTL_MS = 30 * 60 * 1000; // 30 min

  // Curated seed artists used as fallback / enrichment
  const SEED_ARTISTS = [
    'Arijit Singh', 'Shreya Ghoshal', 'Guru Randhawa',
    'Jubin Nautiyal', 'Neha Kakkar', 'Diljit Dosanjh',
    'Badshah', 'Armaan Malik', 'Atif Aslam', 'Vishal Mishra',
    'Jasmine Sandlas', 'Shankar Ehsaan Loy', 'Pritam',
    'A.R. Rahman', 'Sonu Nigam'
  ];

  // ── Public API ───────────────────────────────────────────────
  window.RecommendedArtists = { init, refresh };

  // ── Init ─────────────────────────────────────────────────────
  function init() {
    _injectStyles();
    _render(); // show skeleton instantly
    _loadArtists().then(_populateSection);

    // Re-run after SPA swaps to home
    document.addEventListener('spa:navigated', (e) => {
      const url = (e.detail && e.detail.url) || window.location.pathname;
      if (url === '/home' || url === '/') {
        setTimeout(() => {
          _render();
          _loadArtists().then(_populateSection);
        }, 80);
      }
    });

    console.log('[RecommendedArtists] Initialized');
  }

  function refresh() {
    localStorage.removeItem(CACHE_KEY);
    _loadArtists(true).then(_populateSection);
  }

  // ── Styles ───────────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('__recArtistsCSS')) return;
    const s = document.createElement('style');
    s.id = '__recArtistsCSS';
    s.textContent = `
      /* ── Section wrapper ── */
      #${SECTION_ID} {
        padding-bottom: 4px;
      }
      .rec-artists-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px 12px;
      }
      .rec-artists-title {
        font-size: 22px;
        font-weight: 700;
        color: var(--text-color, #fff);
      }
      .rec-artists-refresh {
        background: none;
        border: none;
        color: var(--accent-color, #1DB954);
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        padding: 6px 0;
        -webkit-tap-highlight-color: transparent;
        display: flex;
        align-items: center;
        gap: 5px;
      }
      .rec-artists-refresh i { font-size: 12px; }
      .rec-artists-refresh:active { opacity: 0.6; }

      /* ── Horizontal scroll row ── */
      .rec-artists-row {
        display: flex;
        gap: 16px;
        padding: 0 20px 8px;
        overflow-x: auto;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
      }
      .rec-artists-row::-webkit-scrollbar { display: none; }

      /* ── Artist card ── */
      .rec-artist-card {
        flex: 0 0 auto;
        width: 88px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        text-decoration: none;
        color: inherit;
      }
      .rec-artist-card:active .rec-artist-avatar {
        transform: scale(0.93);
      }

      /* ── Avatar ── */
      .rec-artist-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid transparent;
        background-clip: padding-box;
        transition: transform 0.2s, border-color 0.3s;
        position: relative;
        flex-shrink: 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      }
      .rec-artist-card:hover .rec-artist-avatar,
      .rec-artist-card:active .rec-artist-avatar {
        border-color: var(--accent-color, #1DB954);
      }

      /* Gradient ring on avatar wrapper */
      .rec-artist-avatar-wrap {
        width: 84px;
        height: 84px;
        border-radius: 50%;
        padding: 2.5px;
        background: linear-gradient(135deg, #1DB954 0%, #17a344 50%, #0f6e2d 100%);
        flex-shrink: 0;
        position: relative;
        transition: transform 0.2s;
      }
      .rec-artist-card:active .rec-artist-avatar-wrap {
        transform: scale(0.93);
      }
      .rec-artist-avatar-wrap img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        display: block;
        background: #1e1e1e;
      }

      /* Playing indicator ring */
      .rec-artist-avatar-wrap.is-playing {
        background: linear-gradient(135deg, #1DB954, #1ed760, #17a344);
        animation: recRingPulse 1.5s ease-in-out infinite;
      }
      @keyframes recRingPulse {
        0%,100% { box-shadow: 0 0 0 0 rgba(29,185,84,0.5); }
        50%      { box-shadow: 0 0 0 6px rgba(29,185,84,0); }
      }

      /* ── Name ── */
      .rec-artist-name {
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 88px;
        color: var(--text-color, #fff);
      }
      .rec-artist-genre {
        font-size: 10px;
        color: var(--text-secondary, #b3b3b3);
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 88px;
        margin-top: -5px;
      }

      /* ── Skeleton loading ── */
      .rec-artist-skeleton {
        flex: 0 0 auto;
        width: 88px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
      }
      .rec-skel-circle {
        width: 84px; height: 84px;
        border-radius: 50%;
        background: linear-gradient(90deg, #2a2a2a 25%, #333 50%, #2a2a2a 75%);
        background-size: 200% 100%;
        animation: recSkel 1.4s ease infinite;
      }
      .rec-skel-line {
        height: 10px; width: 64px; border-radius: 5px;
        background: linear-gradient(90deg, #2a2a2a 25%, #333 50%, #2a2a2a 75%);
        background-size: 200% 100%;
        animation: recSkel 1.4s ease infinite;
      }
      .rec-skel-line.short { width: 44px; height: 8px; }
      @keyframes recSkel {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `;
    document.head.appendChild(s);
  }

  // ── Render skeleton + inject into home page ──────────────────
  function _render() {
    const anchor = document.getElementById('recArtistsAnchor');
    if (!anchor) return;

    // Clear any previous section
    let section = document.getElementById(SECTION_ID);
    if (section) section.remove();

    section = document.createElement('div');
    section.id = SECTION_ID;
    section.innerHTML = `
      <div class="rec-artists-head">
        <span class="rec-artists-title">Artists For You</span>
        <button class="rec-artists-refresh" onclick="RecommendedArtists.refresh()">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
      </div>
      <div class="rec-artists-row" id="recArtistsRow">
        ${_skeletonHTML(8)}
      </div>
    `;
    anchor.after(section);
  }

  function _skeletonHTML(n) {
    return Array.from({ length: n }).map(() => `
      <div class="rec-artist-skeleton">
        <div class="rec-skel-circle"></div>
        <div class="rec-skel-line"></div>
        <div class="rec-skel-line short"></div>
      </div>
    `).join('');
  }

  // ── Load artists from API + listening history ────────────────
  async function _loadArtists(force = false) {
    // Check cache
    if (!force) {
      const cached = _getCache();
      if (cached) return cached;
    }

    const artists = new Map(); // name → { name, image, genre, songId }

    // 1. Pull from listening history — most personal signal
    try {
      const res  = await fetch('/api/history?limit=50');
      const hist = await res.json();
      for (const item of hist) {
        const raw = item.artist || item.primaryArtists || '';
        const names = raw.split(/[,&]/).map(n => n.trim()).filter(Boolean);
        for (const name of names) {
          if (!artists.has(name)) {
            artists.set(name, {
              name,
              image: item.image_url || item.image || '',
              genre: '',
              songId: item.song_id || ''
            });
          }
        }
      }
    } catch (e) { /* history unavailable */ }

    // 2. Pull from favorites
    try {
      const res  = await fetch('/api/favorites');
      const favs = await res.json();
      for (const item of favs) {
        const raw = item.artist || '';
        const names = raw.split(/[,&]/).map(n => n.trim()).filter(Boolean);
        for (const name of names) {
          if (!artists.has(name)) {
            artists.set(name, {
              name,
              image: item.image_url || item.image || '',
              genre: '',
              songId: item.song_id || ''
            });
          }
        }
      }
    } catch (e) { /* favorites unavailable */ }

    // 3. Enrich with trending songs — extract new artists
    try {
      const res     = await fetch('/api/trending?limit=20');
      const songs   = await res.json();
      const songArr = _extractSongs(songs);
      for (const s of songArr) {
        const raw = s.artist || s.primaryArtists || s.singers || '';
        const names = raw.split(/[,&]/).map(n => n.trim()).filter(Boolean);
        const img   = _extractImage(s);
        for (const name of names) {
          if (!artists.has(name)) {
            artists.set(name, { name, image: img, genre: 'Trending', songId: s.id || '' });
          }
        }
      }
    } catch (e) { /* trending unavailable */ }

    // 4. Add seeds that aren't already present
    for (const name of SEED_ARTISTS) {
      if (!artists.has(name)) {
        artists.set(name, { name, image: '', genre: 'Popular', songId: '' });
      }
    }

    // 5. Dedupe, limit, shuffle slightly so it feels fresh
    let list = Array.from(artists.values()).slice(0, MAX_ARTISTS * 3);
    list = _shuffle(list).slice(0, MAX_ARTISTS);

    // 6. Fetch a representative image for any artist missing one
    list = await _enrichImages(list);

    _setCache(list);
    return list;
  }

  // ── Enrich missing images via /api/search ───────────────────
  async function _enrichImages(artists) {
    const needs = artists.filter(a => !a.image);
    const batch = needs.slice(0, 5); // max 5 extra fetches
    await Promise.all(batch.map(async (a) => {
      try {
        const res   = await fetch(`/api/search?q=${encodeURIComponent(a.name)}&limit=3`);
        const data  = await res.json();
        const songs = _extractSongs(data);
        if (songs.length) {
          a.image   = _extractImage(songs[0]);
          a.songId  = a.songId || songs[0].id || '';
          a.genre   = a.genre  || (songs[0].artist || '').split(',')[0].trim();
        }
      } catch (e) {}
    }));
    return artists;
  }

  // ── Populate the section with real cards ─────────────────────
  function _populateSection(artists) {
    const row = document.getElementById('recArtistsRow');
    if (!row) return;
    if (!artists || artists.length === 0) {
      const section = document.getElementById(SECTION_ID);
      if (section) section.remove();
      return;
    }

    row.innerHTML = artists.map(a => _cardHTML(a)).join('');

    // Attach click → navigate to artist page
    row.querySelectorAll('.rec-artist-card').forEach(card => {
      card.addEventListener('click', () => {
        const name = card.dataset.artistName;
        if (!name) return;
        const url = `/artist/${encodeURIComponent(name)}`;
        if (window._spaNavigateTo) window._spaNavigateTo(url);
        else window.location.href = url;
      });
    });

    // Highlight currently-playing artist
    _syncPlayingArtist();
  }

  function _cardHTML(a) {
    const img  = a.image || '/static/images/default-album.png';
    const name = _esc(a.name);
    const genre = _esc(a.genre || '');
    return `
      <div class="rec-artist-card" data-artist-name="${name}" title="${name}">
        <div class="rec-artist-avatar-wrap">
          <img src="${img}"
               alt="${name}"
               loading="lazy"
               onerror="this.src='/static/images/default-album.png'">
        </div>
        <div class="rec-artist-name">${name}</div>
        ${genre ? `<div class="rec-artist-genre">${genre}</div>` : ''}
      </div>
    `;
  }

  // ── Highlight the artist whose song is currently playing ─────
  function _syncPlayingArtist() {
    const row = document.getElementById('recArtistsRow');
    if (!row || !window.player || !window.player.currentSong) return;
    const playing = (window.player.getArtist(window.player.currentSong) || '')
      .split(/[,&]/)[0].trim().toLowerCase();

    row.querySelectorAll('.rec-artist-card').forEach(card => {
      const wrap = card.querySelector('.rec-artist-avatar-wrap');
      if (!wrap) return;
      const match = (card.dataset.artistName || '').toLowerCase() === playing;
      wrap.classList.toggle('is-playing', match);
    });
  }

  // Sync whenever song changes
  document.addEventListener('eva:playstate', _syncPlayingArtist);
  // Piggyback on player bar updates too
  const _origUpdateBar = window.EvaPlayer &&
    window.EvaPlayer.prototype &&
    window.EvaPlayer.prototype._updateBarUI;
  if (_origUpdateBar) {
    window.EvaPlayer.prototype._updateBarUI = function(song) {
      _origUpdateBar.call(this, song);
      _syncPlayingArtist();
    };
  }

  // ── Cache helpers ────────────────────────────────────────────
  function _getCache() {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      const { ts, data } = JSON.parse(raw);
      if (Date.now() - ts > CACHE_TTL_MS) return null;
      return data;
    } catch (e) { return null; }
  }

  function _setCache(data) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data }));
    } catch (e) {}
  }

  // ── Helpers ──────────────────────────────────────────────────
  function _extractSongs(data) {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    for (const key of ['data', 'results', 'songs']) {
      const v = data[key];
      if (Array.isArray(v) && v.length) return v;
      if (v && Array.isArray(v.results)) return v.results;
    }
    return [];
  }

  function _extractImage(song) {
    let img = song.image || song.image_url || song.thumbnail || '';
    if (Array.isArray(img) && img.length) {
      const last = img[img.length - 1];
      img = (typeof last === 'object') ? (last.url || last.link || '') : last;
    }
    return img || '';
  }

  function _shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function _esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // ── Boot ─────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 100);
  }

})();
          
