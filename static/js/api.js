const API = {
    async search(query, limit = 20) {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
        return res.json();
    },
    
    async getTrending(limit = 20) {
        const res = await fetch(`/api/trending?limit=${limit}`);
        return res.json();
    },
    
    async getSong(id) {
        const res = await fetch(`/api/song/${id}`);
        return res.json();
    }
};
