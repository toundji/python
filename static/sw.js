// static/sw.js
self.addEventListener('install', (e) => {
    console.log('Service Worker installé pour MESHORA');
});

self.addEventListener('fetch', (e) => {
    // Nécessaire pour valider le critère PWA d'Android
});
