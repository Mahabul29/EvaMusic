// ═══════════════════════════════════════════════════════════════════════════════
// EvaMusic main.js — API helpers & UI utilities
// No player logic here — that's handled by pullup-player.js (EvaPlayer)
// ═══════════════════════════════════════════════════════════════════════════════

// ─── API helpers ─────────────────────────────────────────────────────────────

async function fetchTrending(limit = 20) {
    try {
        const res = await fetch(`/api/trending?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch trending');
        return await res.json();
    } catch (e) {
        console.error('[API] fetchTrending:', e);
        return [];
    }
}

async function fetchSearch(query, limit = 30) {
    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
        if (!res.ok) throw new Error('Failed to search');
        return await res.json();
    } catch (e) {
        console.error('[API] fetchSearch:', e);
        return [];
    }
}

async function fetchSong(songId) {
    try {
        const res = await fetch(`/api/song/${songId}`);
        if (!res.ok) throw new Error('Failed to fetch song');
        return await res.json();
    } catch (e) {
        console.error('[API] fetchSong:', e);
        return null;
    }
}

// ─── API namespace ───────────────────────────────────────────────────────────
// Used by pullup-player.js EvaPlayer for fallback API calls
const API = {
    getTrending: fetchTrending,
    getSearch:   fetchSearch,
    getSong:     fetchSong,
};

// ─── UI utilities ────────────────────────────────────────────────────────────

function showTab(tabName) {
    console.log('[UI] Show tab:', tabName);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[EvaMusic] App loaded');
});
