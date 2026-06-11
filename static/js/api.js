const API = {
    async search(query, limit = 20) {
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        } catch(e) {
            console.error('API.search error:', e);
            return [];
        }
    },

    async getTrending(limit = 20) {
        try {
            const res = await fetch(`/api/trending?limit=${limit}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        } catch(e) {
            console.error('API.getTrending error:', e);
            return [];
        }
    },

    async getSong(id) {
        try {
            const res = await fetch(`/api/song/${id}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const song = await res.json();
            if (song.error) throw new Error(song.error);
            return song;
        } catch(e) {
            console.error('API.getSong error:', e);
            return null;
        }
    }
};
        
