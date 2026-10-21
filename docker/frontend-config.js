// Konfigurasi runtime Stockify untuk Docker (Nginx).
// Browser memanggil /api/... pada origin yang sama,
// Nginx meneruskannya ke container backend.
window.STOCKIFY_CONFIG = {
  apiBase: "/api"
};
