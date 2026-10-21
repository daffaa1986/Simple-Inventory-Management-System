# Materi Presentasi — Stockify (Simple Inventory Management System)

Dokumen ini adalah materi presentasi tugas **Cloud Services**. Seluruh angka, versi, dan
perilaku yang disebut di sini **diverifikasi langsung dari implementasi dan hasil
pengujian** (lihat [`TESTING.md`](TESTING.md)). Bagian yang membutuhkan bukti tambahan
ditandai dengan ⚠️.

---

## Pembagian Peran (Ringkas)

| Anggota | Area | Slide |
|---|---|---|
| **Anggota 1** — Frontend & Fitur Aplikasi | HTML/CSS/JS, dashboard, pencarian, validasi sisi browser, UX pesan error | 3, 4, 9 (bagian CRUD) |
| **Anggota 2** — Backend, API & Database | FastAPI, 7 endpoint, Pydantic, PostgreSQL, skema tabel, migrasi | 5, 6, 10 |
| **Anggota 3** — Docker, Pengujian & Deployment | Docker Compose, Dockerfiles, volume, health check, environment variables, laporan uji | 2, 7, 8, 11 |

> Semua anggota wajib paham arsitektur menyeluruh (slide 4) karena pertanyaan Q&A bisa
> mengarah ke area mana pun.

---

## Outline Slide (10 slide, target 8–10 menit presentasi + 10 menit demo)

### Slide 1 — Judul & Tim *(Anggota 1, 20 detik)*

- **Stockify — Simple Inventory Management System**
- Tugas Cloud Services · Sistem manajemen inventori berbasis Docker Compose
- Nama & NIM 3 anggota
- Subjudul: *"Satu perintah menjalankan frontend, API, dan database — dengan data yang tidak hilang."*

> Narasi singkat: "Kami membangun Stockify, aplikasi manajemen stok sederhana, dan
> seluruhnya dijalankan dalam Docker Compose agar bisa dijalankan siapa pun,
> di mana pun, dengan satu perintah."

---

### Slide 2 — Masalah & Solusi *(Anggota 3, 40 detik)*

**Masalah:**

- Manajemen inventori biasanya butuh install aplikasi + database terpisah di tiap mesin
- Konfigurasi database sering ditulis manual di kode → rawan tidak konsisten & bocor ke repository
- Data hilang saat mesin/VM di-reinstall karena database ikut ter-format
- Sulit dipakai bersama tim: tiap orang harus setup environment berbeda

**Solusi Stockify:**

- Satu perintah: `docker compose up --build -d` → 3 service jalan & saling terhubung
- Konfigurasi database **100% environment variables** → tidak ada password di kode
- **Named volume** → data tetap ada walau container dihapus dan dibuat ulang
- **Health check** → container hanya dianggap siap setelah DB benar-benar bisa diakses
- Dokumentasi API otomatis (Swagger UI) + laporan uji otomatis

---

### Slide 3 — Fitur Aplikasi *(Anggota 1, 50 detik)*

Tampilkan UI Stockify (screenshot #1).

| Fitur | Perilaku nyata |
|---|---|
| CRUD barang | Tambah, lihat, ubah, hapus — semuanya lewat REST API |
| Dashboard statistik | Jumlah barang, total stok, total nilai (`stok × harga`) — dihitung dari data API |
| Pencarian | Filter berdasarkan nama atau kategori, langsung di tabel |
| Validasi input | Di browser (form) **dan** di server (Pydantic + CHECK constraint) |
| Pesan error jelas | Saat backend/DB mati, user melihat pesan yang bisa ditindaklanjuti |
| Health check | `/health` memverifikasi koneksi PostgreSQL, bukan sekadar "proses hidup" |

> Tekankan: statistik dashboard **bukan angka dummy** — dihitung dari array data
> yang diambil dari API setiap kali data berubah.

---

### Slide 4 — Arsitektur *(Anggota 1, 60 detik)*

Gunakan diagram Mermaid/ASCII dari [`ARCHITECTURE.md`](ARCHITECTURE.md#2-alur-request-sequence-diagram).

```
Browser ──http://localhost:8080──▶ Nginx (frontend)
                                      │ /api/*  (satu origin → tanpa CORS)
                                      ▼
                                  FastAPI :8000
                                      │ psycopg (5432)
                                      ▼
                              PostgreSQL 16 + named volume
```

**Titik kunci yang harus bisa dijelaskan:**

1. **Browser tidak pernah memakai `http://backend:8000`** — nama itu hanya berlaku di
   dalam jaringan Docker. Browser memakai `/api` pada origin yang sama → tanpa CORS.
2. **Address API taken dari `config.js`** (`apiBase`), sehingga kode frontend identik
   antara mode development (Live Server) dan mode Docker.
3. **Nginx me-resolve `backend` saat request** (`resolver 127.0.0.11`), jadi container
   backend boleh dibuat ulang tanpa membuat Nginx salah alamat.

---

### Slide 5 — Backend & API *(Anggota 2, 60 detik)*

Tampilkan Swagger UI (screenshot #6).

**7 endpoint** (terverifikasi dari `/openapi.json`):

| Method | Path | Fungsi | Kode sukses |
|---|---|---|---|
| GET | `/` | Info service | 200 |
| GET | `/health` | Health check + versi PostgreSQL | 200 |
| GET | `/items` | Daftar barang | 200 |
| GET | `/items/{item_id}` | Satu barang | 200 / 404 |
| POST | `/items` | Tambah barang | **201** / 422 |
| PUT | `/items/{item_id}` | Ubah barang | 200 / 404 / 422 |
| DELETE | `/items/{item_id}` | Hapus barang | 200 / 404 |

**Teknik penting:**

- Driver **`psycopg` (psycopg 3)** → sinkron, kompatibel dengan Python 3.13, tanpa
  kompilasi (`psycopg[binary]`), cocok dengan fungsi `def` milik FastAPI.
- `INSERT ... RETURNING id` menggantikan `lastrowid` milik SQLite.
- `connect_timeout` 5 detik → request tidak menggantung saat DB mati.
- Error `psycopg` ditangkap global → dibalas **503** + dicatat ke log (bukan 500 mentah).

---

### Slide 6 — Database PostgreSQL *(Anggota 2, 50 detik)*

```sql
CREATE TABLE IF NOT EXISTS items (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    category TEXT NOT NULL,
    stock    INTEGER NOT NULL CHECK (stock >= 0),
    price    DOUBLE PRECISION NOT NULL CHECK (price >= 0)
);
```

- Skema dibuat otomatis saat aplikasi start (`CREATE TABLE IF NOT EXISTS`).
- Validasi **dua lapis**: Pydantic (model) + CHECK constraint (database).
- `SERIAL` = auto-increment; urutan dijaga `setval` saat migrasi.
- **Migrasi dari SQLite** via `backend/scripts/migrate_sqlite_to_postgres.py`:
  file SQLite dibuka **read-only** (`mode=ro`), skrip **idempoten** (aman dijalankan
  berulang). Berkas SQLite lama **dipertahankan** sebagai arsip.
- Kenapa PostgreSQL, bukan SQLite? → concurrency, integritas constraint, dan mendukung
  deployment lewat container dengan managed service (seperti AWS RDS).

---

### Slide 7 — Docker Compose *(Anggota 3, 70 detik)*

Tampilkan `docker compose ps` (screenshot #8).

```yaml
services:
  db:        postgres:16-alpine   + named volume + healthcheck (pg_isready)
  backend:   built dari backend/Dockerfile
             environment: POSTGRES_HOST=db, POSTGRES_PASSWORD=...
             depends_on: db (condition: service_healthy)
  frontend:  nginx:1.27-alpine     + proxy /api/*
             depends_on: backend (condition: service_healthy)
volumes:
  stockify_pgdata:
```

**Penjelasan:**

- **Health check** = perintah yang dijalankan Docker berkala di dalam container.
  Container hanya ditandai `healthy` bila perintahnya sukses.
- **`depends_on: condition: service_healthy`** = container berikutnya baru start
  setelah yang sebelumnya benar-benar siap, bukan sekadar "sudah dibuat".
- **Environment variables** = password tidak pernah ada di source code/image.
  `.env` (gitignored) + `.env.example` (placeholder) untuk repository.
- Ukuran image: backend 261 MB, frontend 73.7 MB.

---

### Slide 8 — Hasil Pengujian *(Anggota 3, 60 detik)*

**Angka resmi** (dari [`TESTING.md`](TESTING.md)):

| Kelompok | PASS |
|---|---|
| Stack Compose, CRUD API, CRUD proxy, validasi, health check | 39/39 |
| Persistensi named volume | 9/9 |
| Handling error (DB mati & backend mati) + pemulihan | 11/11 |
| Log container | 5/5 |
| Environment variable & kredensial | 9/9 |
| Dokumentasi & konfigurasi | 19/20 |
| **Subtotal API & infrastruktur** | **92/93** |
| Frontend end-to-end via Nginx (jsdom) | 22/22 |
| Frontend end-to-end mode dev (jsdom) | 20/20 |
| **TOTAL** | **134/135** |

**Yang terbukti berjalannya (bukan klaim):**

- Data tetap ada setelah `docker compose down` → `up` (**volume tidak dihapus**)
- PostgreSQL mati → semua endpoint balas **503** dengan pesan jelas → DB hidup → **pulih**
- Backend mati → Nginx balas **502** → UI menampilkan
  *"Layanan API sedang tidak tersedia (HTTP 502). Pastikan backend Stockify berjalan."*
- 9 kasus input tidak sah ditolak **422**, tidak ada yang bocor ke database
- Password asli **tidak ada** di Git, tidak ada di image Docker, tidak ada di dokumentasi

**Satu-satunya yang belum:** berkas `LICENSE` (keputusan tim) ⚠️

> ⚠️ **Perlu bukti tambahan sebelum presentasi:** screenshot UI (checklist 12 item),
> serta uji manual lintas browser.

---

### Slide 9 — Demo *(Anggota 1 + 3, 10 menit)*

Ringkas, detail di [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

1. Tunjukkan `docker compose ps` → 3 container healthy
2. Buka UI → dashboard menampilkan barang + statistik
3. **Tambah** barang → cek di `psql` bahwa baris benar-benar masuk PostgreSQL
4. **Cari** barang → tabel terfilter
5. **Ubah** stok → statistik ikut berubah
6. **Validasi**: isi stok `-5` → pesan error, request tidak terkirim
7. **Health check** → `/health` menampilkan `"engine": "postgresql"`
8. **Log** → `docker compose logs backend --tail 5`
9. **Persistensi**: `docker compose down` → `up -d` → data masih ada ⚠️ *peringatan: jangan `down -v`*
10. **Error handling**: `docker compose stop db` → UI menampilkan pesan → `docker compose start db` → pulih

---

### Slide 10 — Kesimpulan *(Anggota 2, 40 detik)*

**Yang tercapai:**

- CRUD penuh dari UI sampai database, teruji otomatis
- 1 perintah menjalankan 3 service yang saling terkoordinasi & sehat
- Konfigurasi aman (env var, tidak ada rahasia di repository)
- Data persisten melintasi pembuatan ulang container
- Error ditangani dengan pesan yang bisa ditindaklanjuti + tercatat di log
- Dokumentasi lengkap: README, diagram arsitektur, laporan uji

**Pelajaran /cknowledgmentment (opsional):** arsitektur same-origin lewat proxy Nginx
menghilangkan kebutuhan CORS di produksi; `connect_timeout` + health check membuat
kegagalan terdeteksi cepat, bukan menggantung.

**Penutup:** "Terima kasih — kami siap menjawab pertanyaan."

---

## Pertanyaan Q&A (10 pertanyaan, jawaban berbasis implementasi aktual)

> Jawaban berikut merujuk pada kode & konfigurasi nyata. Angka hasil uji diambil dari
> [`TESTING.md`](TESTING.md).

### Q1. Mengapa memakai Docker? Kenapa tidak install langsung di laptop?

**Jawaban:** Karena tujuannya aplikasi yang bisa dijalankan konsisten di mesin manapun
oleh dosen maupun anggota tim. `docker compose up --build -d` menjalankan 3 service
(frontend, backend, database) tanpa perlu install Python, PostgreSQL, atau konfigurasi
manual. Versi software dikunci di dalam image (`postgres:16-alpine`, `python:3.13-slim`,
`nginx:1.27-alpine`) sehingga hasilnya identik di semua mesin. Ini juga memenuhi
persyaratan tugas Cloud Services: konfigurasi lewat environment variables, health
check, dan persistent volume.

### Q2. Kenapa PostgreSQL, bukan SQLite seperti di awal?

**Jawaban:** SQLite cocok untuk satu file lokal, tapi tidak multi-user yang kuat dan
tidak cocok dengan deployment berbasis container/cloud (managed database seperti RDS
justru PostgreSQL). Kami mulai dengan SQLite di Phase 2, lalu migrasi ke PostgreSQL di
Phase 3 memakai skrip `backend/scripts/migrate_sqlite_to_postgres.py` — file SQLite
dibuka read-only dan **tidak dihapus**. Keuntungan nyata: constraint database
(`CHECK (stock >= 0)`) ditegakkan di level data, bukan hanya di aplikasi.

### Q3. Apa itu persistent volume dan kenapa penting?

**Jawaban:** Named volume `stockify_pgdata` memetakan folder data PostgreSQL
(`/var/lib/postgresql/data`) ke storage di luar lifecycle container. Kalau database
berada di dalam container saja, data hilang saat `docker compose down`. Dengan named
volume, data tetap ada. **Bukti:** kami menambah barang, menjalankan `docker compose down`
lalu `up -d`, dan datanya masih ada — tercatat sebagai uji T6 (9/9 PASS). Catatan
penting: `docker compose down -v` **akan menghapus** volume dan datanya.

### Q4. Apa gunanya health check? Bukankah container yang jalan sudah cukup?

**Jawaban:** Container bisa hidup tapi belum siap — PostgreSQL butuh beberapa detik
setelah start. Health check adalah perintah yang dijalankan Docker berkala di dalam
container; statusnya jadi `healthy`/`unhealthy`. Kami memakai `depends_on:
condition: service_healthy` sehingga backend baru start setelah database benar-benar
siap, dan frontend baru start setelah backend sehat. `/health` juga memeriksa koneksi
PostgreSQL sungguhan — hasilnya menampilkan `"engine": "postgresql"` beserta versi
PostgreSQL, bukan sekadar "proses hidup". Semua 3 healthcheck terverifikasi `healthy`
(5 pemeriksaan tercatat per container).

### Q5. Kenapa validasi input dilakukan dua kali (browser dan server)?

**Jawaban:** Validasi di browser memberi umpan balik cepat (form tidak terkirim, pesan
langsung tampil), tapi browser bisa dimanipulasi — jadi tidak bisa diandalkan. Server
tetap memvalidasi dengan Pydantic (nama/kategori 1–100 karakter, stok integer ≥ 0,
harga ≥ 0 tanpa NaN/Inf) dan PostgreSQL menambah lapisan ketiga lewat `CHECK`
constraint. Bukti: 9 kasus tidak sah semuanya ditolak `422` dan tidak ada satu pun
memasuki database. Kami juga menguji validasi sisi browser: stok `-5` ditolak dan
request tidak pernah terkirim.

### Q6. Apa yang terjadi kalau database mati saat aplikasi berjalan?

**Jawaban:** Backend membungkus seluruh operasi database dengan `connect_timeout`
5 detik. Saat koneksi gagal, error `psycopg` ditangkap global handler dan dibalas
**503** dengan pesan `"Database PostgreSQL tidak dapat diakses."`, sekaligus
**dicatat ke log** (`WARNING: Database PostgreSQL tidak dapat diakses (GET /items):
OperationalError: ...`) supaya penyebabnya bisa ditelusuri. UI menampilkan pesan
yang jelas. Setelah database dihidupkan lagi, aplikasi langsung pulih tanpa restart —
terbukti pada uji T7 (7/7 PASS).

### Q7. Kalau backend-nya mati, apakah frontend masih bisa jalan?

**Jawaban:** Nginx mengembalikan **502 Bad Gateway** dan UI menampilkan
*"Layanan API sedang tidak tersedia (HTTP 502). Pastikan backend Stockify berjalan."*
Halaman statis tetap bisa dibuka, jadi user tahu aplikasinya hidup, hanya API-nya
yang bermasalah. Ada satu detail teknis yang perlu kami jelaskan: di Nginx, variabel
`$backend_upstream` **harus** di-`set` **sebelum** `rewrite ... break`, karena
`rewrite ... break` menghentikan fase rewrite — kalau terbalik hasilnya 500
(`invalid URL prefix in "http://"`). Ini sempat menjadi bug dan sudah diperbaiki.

### Q8. Bagaimana cara memastikan password database tidak bocor?

**Jawaban:** Empat lapis. (1) Konfigurasi hanya dari environment variables —
`backend/main.py` membaca `POSTGRES_*` atau `DATABASE_URL`; tidak ada string
password di source code. (2) `.env` dan `backend/.env` ada di `.gitignore`, sedangkan
`.env.example` hanya berisi placeholder. (3) `.dockerignore` mencegah `.env`,
`*.db`, `.venv` masuk build context — kami buktikan dengan `find / -name '.env*'`
di dalam image yang hasilnya kosong. (4) Audit otomatis: password asli hanya
ditemukan di 2 file `.env` yang memang gitignored.

### Q9. Bagaimana proses pengujiannya? Apa itu "terbukti"?

**Jawaban:** Pengujian dilakukan dengan skrip yang benar-benar dijalankan terhadap
stack Docker Compose yang hidup, bukan pemeriksaan manual. Untuk API dan infrastruktur
kami memakai Python (HTTP + `psycopg` untuk querying database langsung), untuk
frontend kami memakai jsdom yang memuat halaman Stockify sungguhan lalu
**mengklik** tombol Simpan/Edit/Hapus dan memeriksa hasilnya di PostgreSQL. Total
**135 pemeriksaan, 134 lulus**. Uji persistensi dilakukan sungguhan: tambah barang →
`down` → `up` → data masih ada. Hasil lengkap ada di `docs/TESTING.md`.

### Q10. Apa tantangan terbesar dan bagaimana mengatasinya?

**Jawaban:** Tiga tantangan nyata: (1) **Frontend awal menampilkan 0 barang** —
ternyata `app.js` belum pernah memanggil API, hanya menyimpan data di array lokal;
(2) **Endpoint `PUT` selalu 500** — ada teks nyasar di dalam string SQL; (3) **Nginx
balas 500 pada `/api/*`** — urutan directive `set` dan `rewrite` yang salah, seperti
dijelaskan di Q7. Semuanya kami telusuri dengan membaca log container dan menguji
ulang secara bertahap. Prinsip yang kami pakai: **jangan menebak — baca log, buat
hipotesis, uji, perbaiki, lalu uji ulang.** Semua perbaikan kami dokumentasikan di
`docs/TESTING.md` beserta bukti sebelum dan sesudahnya.

---

## Checklist Bukti Screenshot (12 item)

> ⚠️ **BELUM ADA** — browser desktop tidak terhubung ke sesi pengujian otomatis, jadi
> screenshot harus diambil manual sebelum presentasi. Detail cara ambilnya ada di
> [`TESTING.md`](TESTING.md#checklist-bukti-screenshot).

| # | Yang direkam | Tujuan |
|---|---|---|
| 1 | Dashboard Stockify | Data tampil + 3 kartu statistik |
| 2 | Form tambah barang + pesan sukses | Bukti Create |
| 3 | Form edit (terisi data lama) | Bukti Update |
| 4 | Konfirmasi hapus | Bukti Delete |
| 5 | Pencarian terfilter | Bukti fitur pencarian |
| 6 | Swagger UI `/docs` | Bukti 7 endpoint |
| 7 | `/health` → `"engine": "postgresql"` | Bukti koneksi DB |
| 8 | `docker compose ps` → 3 healthy | Bukti orkestrasi |
| 9 | `docker volume ls` → `stockify_pgdata` | Bukti persistent volume |
| 10 | `psql` setelah `down`/`up` | Bukti persistensi data |
| 11 | UI saat DB dimatikan | Bukti penanganan error |
| 12 | `docker compose logs backend` | Bukti log bisa ditelusuri |

Simpan sebagai `docs/screenshots/01-dashboard.png` … `12-logs.png`.

---

## Risk List Demo & Pemulihan

Lihat bagian terakhir [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md#7-risk-list--langkah-pemulihan).
Ringkasan: siapkan **terminal kedua** sebagai cadangan, simpan dump data
(`pg_dump`) sebelum demo, dan **jangan pernah** menjalankan `docker compose down -v`
di depan dosen.
