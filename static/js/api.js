// API helper functions

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

function addToLibrary(songId) {
    console.log('[Library] Add:', songId);
    // TODO: Implement with localStorage or backend API
    alert('Added to library!');
}

function shareSong(songId) {
    const url = `${window.location.origin}/player/${songId}`;
    if (navigator.share) {
        navigator.share({ title: 'Check out this song!', url });
    } else {
        navigator.clipboard.writeText(url);
        alert('Link copied to clipboard!');
    }
}

function downloadSong(songId) {
    console.log('[Download]', songId);
    alert('Download started!');
}
