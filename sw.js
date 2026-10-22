// Cache-first so the app works offline inside the fair. Bump VERSION on every deploy.
const VERSION = 'cc-v2';
const ASSETS = ['./', 'index.html', 'xlsx.mini.min.js', 'manifest.webmanifest', 'data/catalog.json', 'data/plan.enc.json', 'data/map-area-a.jpg',
  'icons/icon-180.png', 'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  // Page and plan: try the network briefly so updates arrive, fall back to cache when offline or slow.
  const p = new URL(e.request.url).pathname;
  if (e.request.mode === 'navigate' || p.endsWith('index.html') || p.endsWith('plan.enc.json') || p.endsWith('catalog.json')) {
    const net = fetch(e.request).then((res) => { if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(e.request, copy)); } return res; });
    const timeout = new Promise((r) => setTimeout(r, 2500));
    e.respondWith(Promise.race([net, timeout]).then((res) => res || caches.match(e.request, { ignoreSearch: true }))
      .catch(() => caches.match(e.request, { ignoreSearch: true })).then((res) => res || net));
    return;
  }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then((hit) => hit || fetch(e.request).then((res) => {
    if (res.ok && new URL(e.request.url).origin === location.origin) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(e.request, copy)); }
    return res;
  })));
});
