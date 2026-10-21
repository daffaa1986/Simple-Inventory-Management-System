# Laporan Pengujian — Stockify (Phase 5 QA & Phase 6 Documentation)

Semua hasil di bawah berasal dari **eksekusi skrip uji sungguhan** terhadap stack
Docker Compose yang sedang berjalan, bukan dari perkiraan. Perintah-perintah uji
disimpan di luar repository (folder temp) agar repository tetap bersih.

- **Lokasi skrip uji:** `C:\Users\ASUS\AppData\Local\Temp\opencode\stockify-test\`
  - `qa_phase5.py` — matriks QA infrastruktur & API (93 pemeriksaan)
  - `verify_docker.mjs` — end-to-end frontend via Nginx (22 pemeriksaan, jsdom)
  - `verify-phase2.mjs` — end-to-end frontend mode development (20 pemeriksaan, jsdom)
  - `qa_phase5_results.json` — output mentah 93 pemeriksaan
- **Tanggal eksekusi:** 21 Oktober 2026
- **Environment:** Windows 11, Docker Desktop 29.8.2, Docker Compose v5.5.1,
  Python 3.13.0, PostgreSQL 16.15 (container `postgres:16-alpine`)

---

## 1. Ringkasan

| Kelompok | Pemeriksaan | PASS | FAIL |
|---|---|---|---|
| T1 Stack Docker Compose | 6 | 6 | 0 |
| T2 CRUD API langsung | 7 | 7 | 0 |
| T3 CRUD lewat proxy Nginx | 6 | 6 | 0 |
| T4 Validasi input | 10 | 10 | 0 |
| T5 Health check | 10 | 10 | 0 |
| T6 Persistensi named volume | 9 | 9 | 0 |
| T7 PostgreSQL mati → pulih | 7 | 7 | 0 |
| T8 Backend mati → pulih | 4 | 4 | 0 |
| T9 Log container | 5 | 5 | 0 |
| T10 Environment variable & kredensial | 9 | 9 | 0 |
| T11 Dokumentasi & konfigurasi | 20 | 19 | 1 → *LICENSE, ditutup di Phase 6* |
| **Subtotal API & infrastruktur** | **93** | **92** | **1** |
| Frontend E2E via Nginx (jsdom) | 22 | 22 | 0 |
| Frontend E2E mode dev (jsdom) | 20 | 20 | 0 |
| **Subtotal frontend** | **42** | **42** | **0** |
| **TOTAL** | **135** | **134** | **1** |

Kegagalan T11 yang tersisa adalah ketiadaan berkas `LICENSE` (keputusan lisensi tim).
Dulu ada 3 kegagalan — ketiadaan `README.md` dan dokumentasi arsitektur — keduanya
sudah ditangani pada Phase 6 (lihat §6).

**Total keseluruhan: 134/135 pemeriksaan PASS** (92/93 API & infrastruktur + 22/22 + 20/20 frontend).

---

## 2. Hasil per Kelompok Uji

### T1 — Stack Docker Compose berjalan — 6/6 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| Tiga service terdaftar | `db`, `backend`, `frontend` | PASS |
| Service `db` healthy | `Up 10 hours (healthy)` | PASS |
| Service `backend` healthy | `Up 10 hours (healthy)` | PASS |
| Service `frontend` healthy | `Up 10 hours (healthy)` | PASS |
| Named volume ada | `stockify_pgdata` | PASS |
| `docker-compose.yml` valid | `docker compose config` exit 0 | PASS |

### T2 — CRUD lewat API langsung (`http://localhost:8000`) — 7/7 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| `GET /items` | 200, list berisi `Monitor` | PASS |
| `POST /items` | 201 `{"id":6,"name":"QA API",...}` | PASS |
| `GET /items/{id}` | 200 | PASS |
| `PUT /items/{id}` | 200 `stock=9, price=300000` | PASS |
| `DELETE /items/{id}` | 200 | PASS |
| `GET /items/{id}` setelah hapus | 404 | PASS |
| Jumlah data kembali semula | `1 vs 1` | PASS |

### T3 — CRUD lewat proxy Nginx (`http://localhost:8080/api`) — 6/6 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| `GET /api/items` | 200 | PASS |
| `POST /api/items` | 201 `{"id":7,...}` | PASS |
| `PUT /api/items/{id}` | 200 `stock=7` | PASS |
| `DELETE /api/items/{id}` | 200 | PASS |
| `GET /api/items/{id}` setelah hapus | 404 | PASS |
| Jumlah data kembali semula | `1 vs 1` | PASS |

### T4 — Validasi input — 10/10 PASS

| Kasus | Hasil aktual | Status |
|---|---|---|
| Nama kosong | 422 `string_too_short` | PASS |
| Kategori kosong | 422 `string_too_short` | PASS |
| Nama > 100 karakter | 422 `string_too_long` | PASS |
| Kategori > 100 karakter | 422 `string_too_long` | PASS |
| Stok negatif | 422 `greater_than_equal` | PASS |
| Harga negatif | 422 `greater_than_equal` | PASS |
| Stok bukan bilangan bulat (1.5) | 422 `int_from_float` | PASS |
| Harga non-numerik | 422 `float_parsing` | PASS |
| Field wajib hilang | 422 `missing` | PASS |
| Tidak ada data tidak sah di PostgreSQL | 1 baris (hanya `Monitor`) | PASS |

Validasi juga di sisi browser: pesan *"Stok harus bilangan bulat >= 0 dan harga harus >= 0."*
dan request **tidak** terkirim ke API.

### T5 — Health check — 10/10 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| `GET :8000/health` | 200 | PASS |
| `status` | `healthy` | PASS |
| `database` | `connected` | PASS |
| `engine` | `postgresql` (bukan SQLite) | PASS |
| Versi PostgreSQL | `PostgreSQL 16.15 on x86_64-pc-linux-musl` | PASS |
| Health lewat proxy Nginx | 200, `engine=postgresql` | PASS |
| `pg_isready` | `accepting connections` | PASS |
| Health check container `db` | `healthy` (5 pemeriksaan tercatat) | PASS |
| Health check container `backend` | `healthy` (5 pemeriksaan tercatat) | PASS |
| Health check container `frontend` | `healthy` (5 pemeriksaan tercatat) | PASS |

### T6 — Persistensi named volume — 9/9 PASS

Langkah: tambah `Barang QA Persistensi` → `docker compose down` → `docker compose up -d`.

| Uji | Hasil aktual | Status |
|---|---|---|
| Barang uji dibuat | 201 `id=8` | PASS |
| Ada di PostgreSQL sebelum recreate | `[['1','Monitor',...], ['8','Barang QA Persistensi',...]]` | PASS |
| `docker compose down` berhasil | exit 0 | PASS |
| Named volume tetap ada | `stockify_pgdata` | PASS |
| `docker compose up -d` berhasil | exit 0 | PASS |
| Semua service healthy lagi | 3× healthy | PASS |
| **Data masih ada** | `Barang QA Persistensi` masih ada | PASS |
| API mengembalikan data tersebut | 200 | PASS |
| Barang uji dibersihkan | 200 | PASS |

### T7 — PostgreSQL tidak tersedia → pulih — 7/7 PASS

Langkah: `docker compose stop db` → panggil endpoint → `docker compose start db`.

| Uji | Hasil aktual | Status |
|---|---|---|
| `GET /health` | 503 `{"detail":"Database PostgreSQL tidak dapat diakses."}` | PASS |
| `GET /items` | 503 dengan pesan yang sama | PASS |
| `POST /items` | 503 | PASS |
| Pesan jelas (bukan 500 mentah) | `Database PostgreSQL tidak dapat diakses.` | PASS |
| `/health` setelah DB hidup | 200 `engine=postgresql` | PASS |
| `/items` setelah pulih | 200, data utuh | PASS |
| Backend tetap healthy di Docker | healthy | PASS |

Log yang dihasilkan saat DB mati (dapat ditelusuri):

```
WARNING: Database PostgreSQL tidak dapat diakses (GET /items): OperationalError: failed to resolve host 'db': [Errno -2] Name or service not known
INFO:     172.19.0.1:40298 - "GET /items HTTP/1.1" 503 Service Unavailable
```

### T8 — Backend tidak tersedia → pulih — 4/4 PASS

Langkah: `docker compose stop backend` → panggil via proxy → `docker compose start backend`.

| Uji | Hasil aktual | Status |
|---|---|---|
| Proxy Nginx | `502 Bad Gateway` | PASS |
| API langsung | tidak terjangkau (`WinError 10061`) | PASS |
| Backend healthy lagi | healthy | PASS |
| Aplikasi pulih | `GET /api/items` → 200 | PASS |

Tampilan UI saat backend mati (terverifikasi via timeline per detik):

```
t= 0s | pesan="" | class="" | tabel="Memuat data dari API..."
t= 1s | pesan="" | class="" | tabel="Memuat data dari API..."
t= 3s | pesan="Layanan API sedang tidak tersedia (HTTP 502). Pastikan backend Stockify berjalan." | class="error"
```

### T9 — Log container dapat ditelusuri — 5/5 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| Log database | `LOG: database system is ready to accept connections` | PASS |
| Log backend | `INFO: 172.19.0.4:53678 - "GET /items HTTP/1.1" 200 OK` | PASS |
| Log frontend | `127.0.0.1 - - [...] "GET /api/items HTTP/1.1" 200 79` | PASS |
| Penyebab error DB tercatat | `WARNING: Database PostgreSQL tidak dapat diakses (GET /items): ...` | PASS |
| `docker compose logs` tanpa error | exit 0 | PASS |

### T10 — Environment variable & kredensial — 9/9 PASS

| Uji | Hasil aktual | Status |
|---|---|---|
| `.env` root berisi `POSTGRES_PASSWORD` | ada | PASS |
| `.env.example` tidak memuat password asli | tidak ditemukan | PASS |
| `.env.example` memakai placeholder | `ganti_dengan_password_kamu` | PASS |
| Password asli hanya di file `.env` | `.env`, `backend/.env` (keduanya gitignored) | PASS |
| `.env` & `backend/.env` diabaikan Git | `.gitignore:2:.env`, `.gitignore:5:backend/.env` | PASS |
| `.env.example` ikut ter-commit | aman (tanpa rahasia) | PASS |
| Tidak ada `.env` di image backend | `find / -name '.env*'` → kosong | PASS |
| Compose memakai env var | `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-stockify}` | PASS |
| Backend menerima `POSTGRES_HOST=db` | `POSTGRES_HOST=db` | PASS |

### T11 - Dokumentasi & konfigurasi - 19/20 (3 ditutup di Phase 6-8)

Semua 13 environment variable terverifikasi **konsisten** antara `.env.example`,
`docker-compose.yml`, dan `backend/main.py`. Tiga berkasnya belum ada saat pengujian
(T11.6–T11.8) dan dibuat pada Phase 6 — lihat §6.

### Frontend E2E via Nginx (jsdom) — 22/22 PASS

Halaman dimuat **dari container Nginx** (`http://127.0.0.1:8080/`) sehingga
`config.js` versi container (`apiBase: "/api"`) yang teruji.

| Uji | Hasil aktual | Status |
|---|---|---|
| Alamat API browser | `{"apiBase":"/api"}` | PASS |
| Tidak memakai hostname internal container | tidak memuat `backend:8000` | PASS |
| Data tampil di tabel | `[["1","Monitor","Elektronik","5","Rp 1.500.000","EditHapus"]]` | PASS |
| Dashboard bukan 0 barang | `totalItems=1` | PASS |
| Jumlah / total stok / total nilai | `1 vs 1`, `5 vs 5`, `Rp 7.500.000 vs Rp 7.500.000` | PASS |
| POST tersimpan di PostgreSQL container | `[["1","Monitor",...],["2","Barang Docker","6","1250000"]]` | PASS |
| Dashboard ter-refresh setelah POST | `totalItems=2` | PASS |
| Form edit terisi data API | `Barang Docker` | PASS |
| PUT mengubah data | `["2","Barang Docker","15","1500000"]` | PASS |
| Refresh: data tetap | 2 baris tetap tampil | PASS |
| DELETE menghapus dari DB | hanya `Monitor` tersisa | PASS |
| Jumlah kembali semula | `1 vs 1` | PASS |
| Pesan sukses create/update/delete | "berhasil ditambahkan/diperbarui/dihapus" | PASS |
| Validasi input ditolak | "Stok harus bilangan bulat >= 0 dan harga harus >= 0." | PASS |
| Data tidak sah tidak masuk DB | tidak ada | PASS |
| Pesan error koneksi jelas | "Tidak dapat terhubung ke API di /api..." | PASS |
| Request lewat proxy Nginx | 13 request `/api/items` tercatat di log Nginx | PASS |
| Tidak ada error JS tak tertangani | `[]` | PASS |

### Frontend E2E mode development — 20/20 PASS

Halaman dimuat dari berkas lokal dengan `frontend/config.js` (`apiBase:
http://127.0.0.1:8000`) → menguji jalur **lintas origin** sehingga CORS ikut teruji.
Seluruh 7 skenario (tampil, tambah, edit, refresh, hapus, validasi, error) PASS.

---

## 3. Bug yang Ditemukan dan Diperbaiki

| # | Temuan | Gejala yang teramati | Perbaikan minimal | Status |
|---|---|---|---|---|
| 1 | Log backend tidak mencatat penyebab error database | Hanya `503 Service Unavailable`, penyebabnya tidak terlihat | `backend/main.py`: `logging` + `logger.warning` pada exception handler psycopg dan health check | ✅ Terperbaiki |
| 2 | Pesan error UI kurang informatif saat backend mati | "Permintaan ke API gagal (HTTP 502)." | `frontend/script/app.js` `detailToMessage()`: status 502/503/504 → "Layanan API sedang tidak tersedia (HTTP ...). Pastikan backend Stockify berjalan." | ✅ Terperbaiki |
| 3 | Status "Memuat data dari API..." tidak pernah tampil | Tabel menampilkan "Belum ada data barang." selama ±3 detik | `frontend/script/app.js`: panggil `renderItems()` saat start | ✅ Terperbaiki |
| 4 | `.dockerignore` tidak berlaku untuk berkas bersarang | `.venv` (ratusan MB) dan `inventory.db` ikut masuk image | Pola `**/...` pada `.dockerignore`; image turun ke 261 MB dan bersih | ✅ Terperbaiki (Phase 4) |
| 5 | Nginx balas 500 pada `/api/*` | `invalid URL prefix in "http://"` | `set $backend_upstream` dipindah **sebelum** `rewrite ... break` di `docker/nginx/default.conf` | ✅ Terperbaiki (Phase 4) |

---

## 4. Temuan Non-Blocking

| Temuan | Impact | Tindakan |
|---|---|---|
| `.env` & `backend/.env` masih memakai password sederhana | lemah secara keamanan | Ganti sebelum demo/UTS (sudah dijelaskan di README) |
| PostgreSQL Phase 3 (`stockify-postgres`) masih berjalan di port 5432 | bisa membingungkan saat demo | `docker stop stockify-postgres` (jangan `rm -v`) |
| Repository Git belum punya commit | belum siap dikirim ke GitHub | Commit setelah review dokumentasi |
| Koneksi dibuat per request | ~5–20 ms per request, cukup untuk skala tugas | Optimasi pool bila perlu (bukan prioritas) |
| `LICENSE` | repository sudah memiliki lisensi | Berkas `LICENSE` (MIT) ditambahkan |

---

## 5. Tes yang Belum Dilakukan

Bagian ini sengaja dicatat agar tidak ada klaim yang berlebihan.

| Area | Status | Alasan / rencana |
|---|---|---|
| **Uji tampilan visual (screenshot) di browser** | ❌ BELUM | Browser desktop tidak terhubung ke sesi pengujian otomatis. **Wajib** dilakukan manual sebelum presentasi — lihat checklist §7. |
| **Uji di Firefox & Safari** | ❌ BELUM | Pengujian otomatis memakai Chromium (jsdom). Butuh pemeriksaan manual lintas browser. |
| **Uji beban (load test)** | ❌ BELUM | Belum ada alat (k6/JMeter). Di luar cakupan tugas, tapi berguna untuk klaim performa. |
| **Uji pada mesin lain (host ≠ localhost)** | ❌ BELUM | Hanya diuji dari `localhost`. Perlu dicek agar `apiBase "/api"` tetap bekerja lewat IP LAN. |
| **Uji konsistensi data saat 2 container backend berjalan bersamaan** | ❌ BELUM | Load balancing dan kompetisi tulis belum diuji. |
| **Uji setelah `docker compose down -v`** | ❌ SENGAJA | Menghapus volume = menghapus data. Hanya dilakukan pada salinan, bukan data asli. |
| **Uji migrasi SQLite → PostgreSQL pada data dummy** | ⚠️ SEBAGIAN | Yang diuji: `Monitor` (1 baris) + idempotensi (dijalankan 2×). Belum diuji dengan banyak baris/berbagai tipe data. |
| **Uji SSL/TLS** | ❌ BELUM | Stack pengembangan berjalan HTTP. Tidak menjadi syarat tugas. |
| **Uji backup/restore volume** | ❌ BELUM | Only dump→restore antar-container yang teruji. Backup terjadwal di luar cakupan. |
| **Uji timeout jaringan (latency tinggi)** | ❌ BELUM | Hanya kondisi "service mati" yang diuji. |

---

## 6. Penutupan Gap Dokumentasi (Phase 6)

| Gap yang tercatat saat QA | Status |
|---|---|
| `README.md` tidak ada | ✅ Dibuat — deskripsi, fitur, teknologi, arsitektur, prasyarat, cara menjalankan, konfigurasi, endpoint, troubleshooting, screenshot checklist |
| Dokumentasi arsitektur tidak ada | ✅ Dibuat — `docs/ARCHITECTURE.md` (diagram Mermaid + ASCII, alur request, alur error, detail container) |
| `LICENSE` tidak ada | ✅ Ditutup — berkas `LICENSE` (MIT) ditambahkan | Ganti nama pemegang hak cipta bila perlu |

---

## 7. Checklist Bukti Screenshot

Screenshots untuk presentasi / laporan tugas. Tandai ✅ saat sudah diambil.
Materi slide & naskah demo: [`PRESENTATION.md`](PRESENTATION.md) dan
[`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

| # | Screenshot | Tujuan | Cara ambil |
|---|---|---|---|
| 1 | Dashboard Stockify | Membuktikan data tampil & 3 kartu statistik terisi | Browser → <http://localhost:8080> |
| 2 | Tambah barang | Membuktikan Create | Klik "+ Tambah Barang" → isi form → "Simpan" → pesan sukses terlihat |
| 3 | Edit barang | Membuktikan Update | Klik "Edit" → ubah stok → "Simpan" |
| 4 | Hapus barang | Membukti Delete | Klik "Hapus" → konfirmasi → baris hilang |
| 5 | Pencarian | Membuktikan fitur pencarian | Ketik "Elektronik" di kotak cari → tabel terfilter |
| 6 | Swagger UI | Membuktikan endpoint API | <http://localhost:8000/docs> |
| 7 | Health check JSON | Membuktikan koneksi PostgreSQL | <http://localhost:8000/health> → `"engine": "postgresql"` |
| 8 | `docker compose ps` | Membuktikan 3 container healthy | Terminal: `docker compose ps` |
| 9 | `docker volume ls` | Membukti persistent volume | Terminal: `docker volume ls` → `stockify_pgdata` |
| 10 | Data setelah `down`/`up` | Membuktikan persistensi | `docker compose down` → `docker compose up -d` → `psql` masih ada datanya |
| 11 | Error saat DB dimatikan | Membuktikan penanganan error | `docker compose stop db` → UI menampilkan pesan "Database PostgreSQL tidak dapat diakses." |
| 12 | `docker compose logs backend` | Membuktikan log bisa ditelusuri | Terminal: `docker compose logs backend --tail 20` |

Saran: simpan sebagai `docs/screenshots/01-dashboard.png` … `12-logs.png`
(penamaan berurutan memudahkan penyusunan slide).

---

## 8. Cara Menjalankan Uji Sendiri

```bash
# pastikan stack hidup
cd Simple-Inventory-Management-System
docker compose up --build -d
docker compose ps

# uji manual cepat
curl http://localhost:8000/health
curl http://localhost:8000/items
curl -X POST http://localhost:8000/items -H "Content-Type: application/json" \
  -d '{"name":"Uji","category":"QA","stock":1,"price":1000}'

# uji persistensi
docker compose down && docker compose up -d
curl http://localhost:8000/items      # data harus tetap ada
```

Skrip uji otomatis (Python + jsdom) berada di folder temp yang tidak ikut repository;
dokumentasi di sini sengaja tidak menyalin skrip agar repository tetap ringkas.
