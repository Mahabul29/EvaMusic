const CACHE_NAME = 'jiosaavn-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/css/player.css',
    '/static/js/main.js',
    '/static/js/player.js',
    '/static/images/logo.png',
    '/static/images/default-album.png'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then(response => {
            return response || fetch(e.request).catch(() => {
                if (e.request.mode === 'navigate') {
                    return caches.match('/offline');
                }
            });
        })
    );
});
      
