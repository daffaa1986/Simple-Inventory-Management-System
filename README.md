# Stockify — Simple Inventory Management System

Aplikasi manajemen inventori sederhana untuk menambah, melihat, mengubah, dan menghapus
data barang beserta jumlah stok dan harga satuan.

Stockify dibangun sebagai tugas **Cloud Services**: satu perintah `docker compose up --build`
menyalakan seluruh aplikasi (frontend, backend, dan database) dengan konfigurasi environment
variables, health check otomatis, dan persistent volume sehingga data tidak hilang saat
container dibuat ulang.

> **Status:** Phase 2–6 selesai (integrasi CRUD, migrasi PostgreSQL, containerization, QA, dokumentasi).
> Laporan pengujian lengkap: [`docs/TESTING.md`](docs/TESTING.md).

---

## Daftar Isi

1. [Fitur](#fitur)
2. [Teknologi](#teknologi)
3. [Arsitektur](#arsitektur)
4. [Prasyarat](#prasyarat)
5. [Menjalankan Aplikasi (Docker Compose)](#menjalankan-aplikasi-docker-compose)
6. [Konfigurasi](#konfigurasi)
7. [Endpoint API](#endpoint-api)
8. [Struktur Proyek](#struktur-proyek)
9. [Mode Pengembangan Lokal (tanpa Docker)](#mode-pengembangan-lokal-tanpa-docker)
10. [Hasil Pengujian](#hasil-pengujian)
11. [Troubleshooting](#troubleshooting)
12. [Keamanan & Kredensial](#keamanan--kredensial)
13. [Bukti Screenshot untuk Presentasi](#bukti-screenshot-untuk-presentasi)
14. [Status Proyek & Catatan](#status-proyek--catatan)

---

## Fitur

- **CRUD barang** — tambah, lihat, ubah, hapus data barang (nama, kategori, stok, harga).
- **Dashboard statistik** — jumlah jenis barang, total stok, dan total nilai stok
  (`stok × harga`) dihitung dari data API.
- **Pencarian** — cari barang berdasarkan nama atau kategori, langsung di tabel.
- **Validasi input** — sisi browser (nama/kategori wajib, stok bilangan bulat ≥ 0, harga ≥ 0)
  dan sisi server (Pydantic + `CHECK` constraint PostgreSQL).
- **Penanganan error jelas** — koneksi API mati, service tidak tersedia, dan database
  tidak bisa diakses menghasilkan pesan yang bisa dipahami pengguna.
- **Health check** — endpoint `/health` memverifikasi koneksi PostgreSQL; tiap container
  punya health check sehingga dependensi antar-service dijamin siap.
- **Persistent volume** — data PostgreSQL tetap ada walau container dihapus dan dibuat ulang.
- **Tanpa dependensi build** — backend memakai `psycopg[binary]`, tidak butuh kompilasi.

## Teknologi

| Komponen | Teknologi | Versi |
|---|---|---|
| Frontend | HTML, CSS, JavaScript (vanilla, tanpa build step) | — |
| Web server | Nginx | `1.27.5` (`nginx:1.27-alpine`, Alpine 3.21) |
| Backend | Python, FastAPI, Uvicorn | Python `3.13.16`, FastAPI `0.155`, Uvicorn `0.54` |
| Driver database | psycopg (psycopg 3) | `3.3.6` (`psycopg[binary]`) |
| Validasi | Pydantic | `2.14.1` |
| Konfigurasi env | python-dotenv | `1.2.4` |
| Database | PostgreSQL | `16.15` (`postgres:16-alpine`) |
| Orchestration | Docker Engine + Docker Compose | Docker `29.8.2`, Compose `5.5.1` |
| Dokumentasi API | Swagger UI (otomatis dari FastAPI) | `/docs` |

> `backend/requirements.txt` sengaja **tidak** mem-pin versi, sehingga image selalu
> dibangun dengan rilis terbaru yang kompatibel. Versi di atas adalah yang benar-benar
> terpasang di image saat dokumentasi ini dibuat.

## Arsitektur

```
┌──────────────┐        http://localhost:8080         ┌────────────────────────┐
│   Browser    │ ─────────────────────────────────────▶ │  Frontend Container    │
│  (Stockify)  │                                       │  nginx:1.27-alpine     │
└──────────────┘                                       │  HTML + CSS + JS        │
                                                        └───────────┬────────────┘
                                                                    │ /api/*  (proxy, satu origin)
                                                                    ▼
                                                        ┌────────────────────────┐
                                                        │  Backend Container     │
                                                        │  FastAPI + Uvicorn     │
                                                        │  0.0.0.0:8000          │
                                                        └───────────┬────────────┘
                                                                    │ psycopg, port 5432
                                                                    ▼
                                                        ┌────────────────────────┐
                                                        │  PostgreSQL Container  │
                                                        │  postgres:16-alpine    │
                                                        │  named volume:         │
                                                        │  stockify_pgdata       │
                                                        └────────────────────────┘
```

Diagram lengkap (Mermaid + ASCII), alur request, dan alur penanganan error:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**Catatan penting:** browser **tidak pernah** mengakses hostname internal container
( seperti `http://backend:8000`). Halaman memanggil `/api/...` pada origin yang sama,
Nginx meneruskannya ke container backend. Ini membuat frontend bebas masalah CORS
dan tetap bisa diakses dari perangkat lain di jaringan yang sama.

## Prasyarat

| Kebutuhan | Keterangan |
|---|---|
| Docker Desktop / Docker Engine | Wajib untuk menjalankan lewat Docker Compose. Compose **v2+** (perintah `docker compose`, bukan `docker-compose`). |
| ≥ 4 GB RAM | PostgreSQL + FastAPI + Nginx |
| Port host bebas | `8080` (frontend), `8000` (API), `5433` (PostgreSQL) |
| Git *(opsional)* | Untuk mengkloning repository |
| Browser modern | Chrome/Edge/Firefox |

> PostgreSQL **tidak** perlu diinstall di host — sudah disediakan container `postgres:16-alpine`.

## Menjalankan Aplikasi (Docker Compose)

### 1. Siapkan konfigurasi

```bash
git clone <url-repository>
cd Simple-Inventory-Management-System

# Windows PowerShell
Copy-Item .env.example .env
# macOS / Linux
cp .env.example .env
```

Buka `.env` lalu isi `POSTGRES_PASSWORD` dengan password pilihanmu (tanpa karakter
`@ : / #` agar aman bila nanti dipakai dalam URL):

```ini
POSTGRES_PASSWORD=password_kamu_yang_kuat
```

### 2. Jalankan seluruh stack

```bash
docker compose up --build -d
```

Tunggu sampai ketiga container berstatus `healthy`:

```bash
docker compose ps
```

```
NAME                STATUS                        PORTS
stockify-backend    Up 2 minutes (healthy)        0.0.0.0:8000->8000/tcp
stockify-db         Up 2 minutes (healthy)        0.0.0.0:5433->5432/tcp
stockify-frontend   Up 2 minutes (healthy)        0.0.0.0:8080->80/tcp
```

### 3. Buka aplikasinya

| Layanan | URL |
|---|---|
| **UI Stockify** | <http://localhost:8080> |
| **Dokumentasi API (Swagger)** | <http://localhost:8000/docs> |
| **Health check** | <http://localhost:8000/health> |
| **Data barang (JSON)** | <http://localhost:8080/api/items> |

### 4. Perintah harian

```bash
docker compose ps          # status container
docker compose logs -f     # ikuti log semua service
docker compose logs backend
docker compose down        # stop (named volume tetap aman)
docker compose up -d       # start lagi, data tetap ada
```

### 5. Hapus total (hATI-HATI)

```bash
docker compose down -v    # menghapus volume -> DATA HILANG
```

## Konfigurasi

Semua konfigurasi diambil dari **environment variables**. Nilai sebenarnya disimpan di
file `.env` (root) untuk Docker Compose dan `backend/.env` untuk menjalankan backend
di luar Docker. Keduanya **tidak** masuk Git — lihat [`.env.example`](.env.example).

### Environment variables

| Variabel | Default | Dipakai oleh | Keterangan |
|---|---|---|---|
| `POSTGRES_USER` | `stockify` | `db`, `backend` | User PostgreSQL |
| `POSTGRES_PASSWORD` | `stockify` | `db`, `backend` | **Wajib diganti** di `.env` |
| `POSTGRES_DB` | `stockify` | `db`, `backend` | Nama database |
| `POSTGRES_HOST` | `localhost` | `backend` (mode lokal) | Di Docker Compose otomatis `db` |
| `POSTGRES_PORT` | `5432` | `backend` (mode lokal) | Di Docker Compose otomatis `5432` (internal) |
| `POSTGRES_CONNECT_TIMEOUT` | `5` | `backend` | Batas waktu koneksi (detik) sebelum gagal |
| `DATABASE_URL` | — | `backend` | Alternatif satu baris URL; dipakai otomatis bila ada |
| `FRONTEND_PORT` | `8080` | `compose` | Port host untuk Nginx (UI) |
| `BACKEND_PORT` | `8000` | `compose` | Port host untuk FastAPI |
| `DB_HOST_PORT` | `5433` | `compose` | Port host untuk PostgreSQL (dipakai `psql` dari host) |

### Port

| Port host | Service | Keterangan |
|---|---|---|
| `8080` | Frontend (Nginx) | Halaman UI Stockify + proxy `/api/*` |
| `8000` | Backend (FastAPI) | REST API + Swagger UI `/docs` |
| `5433` | PostgreSQL | Akses `psql` dari host (opsional) |

### Persistent volume

| Nama volume | Mount | Isi |
|---|---|---|
| `stockify_pgdata` | `/var/lib/postgresql/data` | Seluruh data PostgreSQL |

Volume bersifat **named**, sehingga data tetap ada setelah `docker compose down`
dan `up` kembali. Volume dihapus hanya bila menjalankan `docker compose down -v`
atau `docker volume rm stockify_pgdata`.

## Endpoint API

Base URL saat memakai Docker Compose: `http://localhost:8000`
(atau `http://localhost:8080/api` melalui proxy Nginx).

| Method | Path | Keterangan | Sukses |
|---|---|---|---|
| `GET` | `/` | Informasi service | `200` |
| `GET` | `/health` | Health check + verifikasi koneksi PostgreSQL | `200` |
| `GET` | `/items` | Daftar semua barang (urut id DESC) | `200` |
| `GET` | `/items/{item_id}` | Satu barang | `200` / `404` |
| `POST` | `/items` | Tambah barang | `201` / `422` |
| `PUT` | `/items/{item_id}` | Ubah barang (ganti seluruh field) | `200` / `404` / `422` |
| `DELETE` | `/items/{item_id}` | Hapus barang | `200` / `404` |

### Contoh request & response (hasil aktual)

```bash
# Health check
curl http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "database": "connected",
  "engine": "postgresql",
  "server_version": "PostgreSQL 16.15 on x86_64-pc-linux-musl"
}
```

```bash
# Read semua barang
curl http://localhost:8000/items
```
```json
[
  {
    "id": 1,
    "name": "Monitor",
    "category": "Elektronik",
    "stock": 5,
    "price": 1500000.0
  }
]
```

```bash
# Create
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard Mekanik","category":"Elektronik","stock":8,"price":750000}'
```
```json
{ "id": 2, "name": "Keyboard Mekanik", "category": "Elektronik", "stock": 8, "price": 750000.0 }
```

```bash
# Update
curl -X PUT http://localhost:8000/items/2 \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard Mekanik RGB","category":"Elektronik","stock":12,"price":899000}'
```
```json
{ "id": 2, "name": "Keyboard Mekanik RGB", "category": "Elektronik", "stock": 12, "price": 899000.0 }
```

```bash
# Delete
curl -X DELETE http://localhost:8000/items/2
```
```json
{ "message": "Barang berhasil dihapus.", "id": 2 }
```

### Aturan validasi

| Field | Aturan | Pesan error server |
|---|---|---|
| `name` | string, 1–100 karakter, tidak boleh kosong/spasi saja | `422` — `String should have at least 1 character` / `Field required` |
| `category` | string, 1–100 karakter, tidak boleh kosong/spasi saja | `422` — `String should have at least 1 character` / `Field required` |
| `stock` | integer, `0` … `2147483647` | `422` — `Input should be greater than or equal to 0` |
| `price` | float, `≥ 0`, tanpa `NaN`/`Inf` | `422` — `Input should be greater than or equal to 0` |

> Catatan: aturan di atas adalah aturan **API**. Formulir di browser imposes batas
> yang lebih ketat pada `category` (`maxlength="60"` di `frontend/index.html`),
> sedangkan API menerima hingga 100 karakter.

Contoh error validasi (`422`):

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

Contoh error lain:

| Situasi | Status | Body |
|---|---|---|
| ID tidak ada | `404` | `{"detail":"Barang tidak ditemukan."}` |
| Database tidak bisa diakses | `503` | `{"detail":"Database PostgreSQL tidak dapat diakses."}` |
| Backend mati (via proxy Nginx) | `502` | halaman error Nginx; UI menampilkan *"Layanan API sedang tidak tersedia (HTTP 502). Pastikan backend Stockify berjalan."* |

## Struktur Proyek

```
Simple-Inventory-Management-System/
├── .dockerignore              # pengecualian build context (rahasia, .venv, db)
├── .env.example               # template konfigurasi (tanpa kredensial asli)
├── .gitignore                 # .env, *.db, .venv, __pycache__ -> tidak ikut commit
├── docker-compose.yml         # orkestrasi 3 service + named volume + healthcheck
├── README.md
├── backend/
│   ├── .env                   # kredensial lokal (TIDAK ikut commit)
│   ├── Dockerfile             # python:3.13-slim + uvicorn
│   ├── inventory.db           # SQLite lama Phase 1-2 (dipertahankan, tidak dipakai lagi)
│   ├── main.py                # aplikasi FastAPI + konfigurasi DB dari env vars
│   ├── requirements.txt       # fastapi, uvicorn[standard], psycopg[binary], python-dotenv
│   └── scripts/
│       └── migrate_sqlite_to_postgres.py   # migrasi data SQLite -> PostgreSQL (read-only)
├── docker/
│   ├── frontend-config.js     # konfigurasi API untuk runtime container (apiBase "/api")
│   └── nginx/default.conf     # Nginx: static + proxy /api -> backend
├── docs/
│   ├── ARCHITECTURE.md        # diagram & detail konfigurasi container
│   ├── PRESENTATION.md        # outline slide 10 slide, pembagian peran 3 anggota, 10 Q&A
│   ├── DEMO_SCRIPT.md         # naskah demo 10 menit + risk list & pemulihan
│   └── TESTING.md             # laporan uji + checklist screenshot
└── frontend/
    ├── Dockerfile             # nginx:1.27-alpine
    ├── config.js              # konfigurasi API untuk mode dev (apiBase 127.0.0.1:8000)
    ├── index.html             # struktur halaman Stockify
    ├── script/app.js          # integrasi API (fetch) + CRUD + dashboard + validasi
    └── style/style.css        # desain Stockify
```

## Mode Pengembangan Lokal (tanpa Docker)

Frontend murni HTML/CSS/JS dapat dijalankan dengan **Live Server** (VS Code) atau
server statis apa pun, dengan backend berjalan di host:

```bash
# Terminal 1 - backend (butuh PostgreSQL)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
Copy-Item .env.example .env     # lalu isi POSTGRES_PASSWORD & host DB
uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
# Live Server -> http://127.0.0.1:5500/frontend/index.html
```

Alamat API untuk mode ini diambil dari `frontend/config.js`
(`apiBase: "http://127.0.0.1:8000"`). Backend mengizinkan CORS untuk
`localhost`/`127.0.0.1` pada port berapa pun, jadi Live Server tetap bisa dipakai.

## Hasil Pengujian

Ringkasan (detail + bukti aktual di [`docs/TESTING.md`](docs/TESTING.md)):

| Kelompok uji | Cakupan | Hasil |
|---|---|---|
| T1 Stack Compose | 3 service healthy, volume ada, config valid | **6/6 PASS** |
| T2 CRUD API langsung | Create, Read, Update, Delete, 404 | **7/7 PASS** |
| T3 CRUD via proxy Nginx | Create, Read, Update, Delete, 404 | **6/6 PASS** |
| T4 Validasi input | 9 kasus (nama, kategori, stok, harga) | **10/10 PASS** |
| T5 Health check | `/health`, `pg_isready`, healthcheck container | **10/10 PASS** |
| T6 Persistensi volume | data tetap setelah container dibuat ulang | **9/9 PASS** |
| T7 Database mati | 503 + pesan jelas + pemulihan | **7/7 PASS** |
| T8 Backend mati | 502 + pesan jelas + pemulihan | **4/4 PASS** |
| T9 Log container | log PG, uvicorn, Nginx, penyebab error | **5/5 PASS** |
| T10 Env & kredensial | tidak ada rahasia di Git/image | **9/9 PASS** |
| T11 Dokumentasi | konsistensi env var & kelengkapan dokumen | **19/20 PASS** (sisa 1: lisensi) |
| Frontend E2E (Nginx → FastAPI → PostgreSQL) | seluruh alur UI | **22/22 PASS** |
| Frontend E2E (mode dev) | regresi alur Live Server | **20/20 PASS** |

**Total 135 pemeriksaan: 134 PASS** (93 pemeriksaan API & infrastruktur → 92 PASS;
42 pemeriksaan frontend → 42 PASS). Satu-satunya sisa adalah penentuan nama pemegang
hak cipta pada berkas `LICENSE`.

Tes yang **belum** dilakukan tercatat terbuka di
[`docs/TESTING.md`](docs/TESTING.md#tes-yang-belum-dilakukan) — terutama pengujian
visual/tampilan di browser dan uji beban (load test).

## Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop belum jalan → buka Docker Desktop, tunggu ikon "running". |
| `port is already allocated` (8080/8000/5433) | Port dipakai proses lain → ubah `FRONTEND_PORT`/`BACKEND_PORT`/`DB_HOST_PORT` di `.env`, lalu `docker compose up -d`. |
| UI tampil tapi tabel kosong + pesan *"Tidak dapat terhubung ke API"* | Backend mati → `docker compose ps`, `docker compose logs backend`. |
| UI menampilkan *"Layanan API sedang tidak tersedia (HTTP 502)"* | Nginx tidak menjangkau backend → `docker compose logs backend` (lihat apakah container backend `healthy`). |
| `/health` balas `503` + *"Database PostgreSQL tidak dapat diakses."* | PostgreSQL mati/tidak siap → `docker compose logs db`; pastikan container `db` `healthy`; volume lama yang korup bisa insisted `docker compose down -v` (**data hilang**). |
| Backend gagal start: *"PostgreSQL tidak dapat diakses"* | Backend menunggu DB siap (5× percobaan, jeda 2 detik). Pastikan service `db` sudah `healthy`. |
| `password authentication failed for user "stockify"` | `POSTGRES_PASSWORD` di `.env` berbeda dari yang tersimpan di volume. Password hanya tersimpan saat volume **pertama kali** dibuat. Solusi: `docker compose down -v` lalu `up -d` (**data hilang**) atau samakan password lama. |
| Perubahan `.env` tidak berlaku | `docker compose up -d --force-recreate` agar container membaca env baru. |
| Perubahan `main.py` tidak terlihat | Mode lokal: `uvicorn --reload`; mode Docker: `docker compose up -d --build`. |
| Halaman 404 di Nginx untuk rute selain `/` | Nginx memakai `try_files ... /index.html` (SPA). Endpoint API ada di `/api/*`. |
| Error `failed to resolve host 'db'` | Container `db` belum start/healthy → `docker compose up -d`, cek `docker compose ps`. |
| Port 5432 sudah dipakai PostgreSQL lokal | Compose memakai host port `5433` (bukan 5432) agar tidak bentrok. Ubah `DB_HOST_PORT` bila perlu. |
| Ingin data kosong untuk demo | `docker compose down -v` lalu `docker compose up -d` (**data lama hilang permanen**). |

## Keamanan & Kredensial

- Password database **tidak pernah** disimpan di dalam source code, frontend, atau image Docker.
- File `.env` dan `backend/.env` ada di `.gitignore` → tidak ikut ter-commit.
- `.dockerignore` mencegah `.env`, `*.db`, `.venv`, dan `__pycache__` masuk build context.
- `.env.example` hanya berisi placeholder (`ganti_dengan_password_kamu`).
- Verifikasi: `docker run --rm --entrypoint sh <image-backend> -c "find / -name '.env*'"`
  → tidak menghasilkan file apa pun.

> **Sebelum demo/UTS:** ganti `POSTGRES_PASSWORD` di `.env`, dan pastikan
> `git status` tidak menampilkan `.env` sebelum melakukan commit.

## Bukti Screenshot untuk Presentasi

Checklist lengkap ada di [`docs/TESTING.md`](docs/TESTING.md#checklist-bukti-screenshot).
Materi presentasi (outline slide, pembagian peran 3 anggota, 10 Q&A, dan naskah demo
10 menit) ada di [`docs/PRESENTATION.md`](docs/PRESENTATION.md) dan
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

Ringkasnya yang perlu disiapkan:

1. **Dashboard** — UI Stockify menampilkan data barang + 3 kartu statistik.
2. **Tambah barang** — form terbuka, isi data, klik Simpan, pesan sukses.
3. **Edit barang** — form terisi data lama, ubah stok, hasil di tabel.
4. **Hapus barang** — konfirmasi, baris hilang dari tabel.
5. **Pencarian** — ketik kategori, tabel terfilter.
6. **Swagger UI** — <http://localhost:8000/docs> menampilkan daftar endpoint.
7. **Health check** — `/health` menampilkan `"engine": "postgresql"`.
8. **Docker Compose** — `docker compose ps` menampilkan 3 container `healthy`.
9. **Persistent volume** — `docker volume ls` + `docker compose exec db psql ...` setelah `down`/`up`.
10. **Penanganan error** — matikan DB, UI menampilkan pesan *"Database PostgreSQL tidak dapat diakses."*
11. **Log container** — `docker compose logs backend` menunjukkan penyebab error.

## Status Proyek & Catatan

| Phase | Status | Catatan |
|---|---|---|
| 1 — Fondasi | ✅ | Frontend HTML/CSS/JS + backend FastAPI + SQLite |
| 2 — Integrasi CRUD | ✅ | Dashboard terhubung ke API; CRUD Create/Read/Update/Delete |
| 3 — PostgreSQL | ✅ | Migrasi dari SQLite via `backend/scripts/migrate_sqlite_to_postgres.py`; `backend/inventory.db` **dipertahankan** sebagai arsip |
| 4 — Docker Compose | ✅ | 3 service, named volume, health check, `depends_on` |
| 5 — QA | ✅ | 90/93 pemeriksaan PASS + 42 pemeriksaan frontend PASS; 3 temuan dokumentasi sudah ditutup pada fase ini |
| 6 — Dokumentasi | ✅ | README, diagram arsitektur, laporan pengujian |
| 7 — Presentasi | ⏳ | Slide, pembagian kontribusi, simulasi demo |
| 8 — Review repository | ⏳ | Cek GitHub & daftar file pengumpulan |

### Persyaratan yang masih belum terpenuhi

- **`LICENSE`** — belum ada. Penentuan lisensi (mis. MIT) adalah keputusan tim; tambahkan
  berkas `LICENSE` sebelum repository dipublikasikan.
- **Commit awal repository** — repo Git sudah diinisialisasi (`branch: main`) tetapi belum
  memiliki commit. Lakukan setelah seluruh dokumentasi direview.
- **Bukti visual** — belum ada screenshot; lihat checklist di atas.
- **Uji beban (load test)** dan **uji lintas browser (Firefox/Safari)** belum dijalankan;
  pengujian fungsional dilakukan via Chromium/jsdom dan HTTP.

---

Dibuat untuk tugas **Cloud Services** — Tim Stockify.
