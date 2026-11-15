// 鬧熱牌局 Service Worker — 版本：v5.26（每次發版自動換快取名稱）
const VER = 'v5.26-o1';
const CACHE = 'naojiat-' + VER;
const CORE = ['./', './index.html', './install.html', './manifest.webmanifest', './icons/icon-180.png', './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png', './icons/favicon-32.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE.map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('naojiat-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('message', e => { if (e.data === 'skipWaiting') self.skipWaiting(); });

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;           // 其他網域（例如後端 API）不攔截
  if (url.pathname.endsWith('.mobileconfig')) return;       // 描述檔一律走網路
  if (/^\/(v1|ws|play|admin|agent|grafana)(\/|$)/.test(url.pathname)) return;   // 同網域後端 API／線上客戶端／後台：永不快取
  const isPage = req.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('.html');
  if (isPage) {
    // 網路優先：有網路就拿最新版（下次開啟即更新），離線才用快取
    e.respondWith(fetch(req, { cache: 'no-store' }).then(res => {
      if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match('./index.html'))));
    return;
  }
  // 靜態資源：快取優先，背景補抓
  e.respondWith(caches.match(req).then(hit => {
    const net = fetch(req).then(res => {
      if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
