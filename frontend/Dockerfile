# Stockify - Frontend Nginx
FROM nginx:1.27-alpine

# Halaman, CSS, dan JavaScript Stockify.
COPY frontend/ /usr/share/nginx/html/

# Konfigurasi server Nginx (static + proxy ke backend).
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# Konfigurasi API untuk runtime container:
# browser memakai /api (satu origin) -> Nginx meneruskan ke backend.
COPY docker/frontend-config.js /usr/share/nginx/html/config.js

EXPOSE 80
