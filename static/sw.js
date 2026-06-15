const CACHE_NAME = 'medibridge-v1'
const ASSETS = [
  '/',
  '/static/Logo.jpeg',
]

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  )
  self.skipWaiting()
})

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', e => {
  // For API calls — always go to network
  if (e.request.url.includes('/api/')) {
    return e.respondWith(fetch(e.request))
  }
  // For everything else — cache first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  )
})