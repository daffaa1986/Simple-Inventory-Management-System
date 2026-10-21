// Konfigurasi runtime Stockify untuk pengembangan lokal (Live Server).
// Frontend memanggil API FastAPI secara langsung di host lokal.
// Di Docker, file ini diganti oleh docker/frontend-config.js (apiBase: "/api").
window.STOCKIFY_CONFIG = {
  apiBase: "http://127.0.0.1:8000"
};
