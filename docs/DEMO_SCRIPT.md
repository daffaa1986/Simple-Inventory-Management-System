# Naskah Demo Stockify — 10 Menit

Naskah demo yang **dapat dijalankan langsung**. Semua perintah, output yang diharapkan,
dan durasi tercantum. Kerjakan sesuai urutan; jangan improvisasi di depan dosen.

> **Aturan emas:** jangan pernah menjalankan `docker compose down -v` selama demo —
> perintah itu menghapus volume beserta datanya.

---

## 0. Persiapan (sebelum demo, 5 menit — tidak dihitung dalam durasi)

| # | Yang disiapkan | Cara | Status |
|---|---|---|---|
| 1 | Stack sudah hidup & sehat | `docker compose ps` → 3 container `healthy` | ☐ |
| 2 | Data demo minimal sudah ada | Minimal 3 barang agar tabel & statistik terlihat ramai | ☐ |
| 3 | **Backup data** (jaring pengaman) | `docker compose exec -T db pg_dump -U stockify -d stockify > backup-demo.sql` | ☐ |
| 4 | Browser siap di halaman **kosong** (`http://localhost:8080`), tab baru | Hard refresh `Ctrl+F5` | ☐ |
| 5 | Terminal kedua terbuka di folder proyek (cadangan) | Terminal 1 = demo, Terminal 2 = cadangan | ☐ |
| 6 | Font terminal diperbesar, tema terang | mudah dibaca dari belakang ruangan | ☐ |
| 7 | Screenshot checklist terambil | 12 item, lihat `TESTING.md` | ☐ ⚠️ |

**Perintah verifikasi pra-demo (jalankan 1× sebelum mulai):**

```bash
docker compose ps
docker compose exec -T db psql -U stockify -d stockify -c "SELECT * FROM items ORDER BY id;"
```

Harus terlihat 3 container `healthy` dan beberapa baris barang.

---

## 1. Timeline Demo

| Menit | Durasi | Langkah | Who |
|---|---|---|---|
| 00:00–01:00 | 1 mnt | **Buka aplikasi** — dashboard | Anggota 1 |
| 01:00–02:30 | 1.5 mnt | **Create** + verifikasi di database | Anggota 1 + 3 |
| 02:30–03:00 | 0.5 mnt | **Read/pencarian** | Anggota 1 |
| 03:00–04:00 | 1 mnt | **Update** + statistik ikut berubah | Anggota 1 |
| 04:00–05:00 | 1 mnt | **Validasi input** ditolak | Anggota 1 |
| 05:00–05:30 | 0.5 mnt | **Delete** | Anggota 1 |
| 05:30–06:30 | 1 mnt | **Health check** + **log container** | Anggota 2 |
| 06:30–08:30 | 2 mnt | **Persistensi**: `down` → `up` → data tetap | Anggota 3 |
| 08:30–09:30 | 1 mnt | **Penanganan error**: DB mati → pesan → pulih | Anggota 3 |
| 09:30–10:00 | 0.5 mnt | Penutup + arahkan ke Q&A | Semua |

---

## 2. Langkah Demi Langkah

### L1 — Aplikasi hidup (00:00)

**Browser** → buka `http://localhost:8080`

**Harus terlihat:**
- Header "Stockify"
- Tiga kartu: **Jenis Barang**, **Total Stok**, **Total Nilai Stok** (terisi, bukan 0)
- Tabel berisi barang, tombol **Edit** & **Hapus** per baris

**Terminal** (buka terminal kedua supaya menyatu):

```bash
docker compose ps
```

**Harus terlihat:** `stockify-db`, `stockify-backend`, `stockify-frontend` — semuanya
`(healthy)`.

> Narasi: "Inilah Stockify. Satu perintah `docker compose up --build -d` menyalakan
> tiga service, dan ketiganya sudah lolos health check."

---

### L2 — Create + bukti masuk database (01:00)

**Browser** → klik **"+ Tambah Barang"** → isi:

| Field | Nilai |
|---|---|
| Nama Barang | `Monitor 27 inci` |
| Kategori | `Elektronik` |
| Jumlah Stok | `12` |
| Harga Satuan | `2499000` |

Klik **Simpan**.

**Harus terlihat:** pesan hijau *"Barang berhasil ditambahkan."*, baris baru di tabel,
kartu **Jenis Barang** naik 1, **Total Stok** naik 12, **Total Nilai Stok** naik
12 × 2.499.000 = **Rp 29.988.000**.

**Terminal** — buktikan benar-benar masuk PostgreSQL:

```bash
docker compose exec -T db psql -U stockify -d stockify \
  -c "SELECT id,name,stock,price FROM items ORDER BY id DESC LIMIT 3;"
```

**Harus terlihat:** baris `Monitor 27 inci | 12 | 2499000`.

> Narasi: "Angka di dashboard bukan dummy — dihitung dari data API. Dan baris ini
> benar-benar ada di PostgreSQL, bukan di memori browser."

---

### L3 — Read & pencarian (02:30)

**Browser** → ketik `elektron` di kotak **"Cari nama atau kategori..."**

**Harus terlihat:** tabel terfilter hanya kategori Elektronik. Ketik `zzzz` → muncul
*"Tidak ada barang yang ditemukan."* Kosongkan lagi.

> Narasi: "Pencarian memfilter di sisi client berdasarkan data yang sudah diunduh dari
> API — responsif tanpa request tambahan."

---

### L4 — Update (03:00)

**Browser** → klik **Edit** pada `Monitor 27 inci` → ubah:

- Jumlah Stok: `12` → `20`
- Harga: `2499000` → `2299000`

Klik **Simpan**.

**Harus terlihat:** pesan *"Barang berhasil diperbarui."*, tabel menunjukkan stok 20,
dan kartu **Total Stok** naik 8 (20 − 12), **Total Nilai Stok** berubah.

**Terminal** (opsional, 5 detik):

```bash
docker compose exec -T db psql -U stockify -d stockify \
  -c "SELECT name,stock,price FROM items WHERE name='Monitor 27 inci';"
```

**Harus terlihat:** `20 | 2299000`.

---

### L5 — Validasi input (04:00)

**Browser** → klik **"+ Tambah Barang"** → isi nama `Barang Invalid`, kategori `Uji`,
stok **`-5`**, harga `1000` → klik **Simpan**.

**Harus terlihat:**
- Pesan merah: *"Stok harus bilangan bulat >= 0 dan harga harus >= 0."*
- **Barang tidak muncul** di tabel

> Narasi: "Validasi berjalan di dua lapis. Browser menolak lebih dulu supaya user
> cepat tahu; server juga memvalidasi ulang karena browser bisa dimanipulasi."

**Terminal** — binti tidak ada yang bocor ke database:

```bash
docker compose exec -T db psql -U stockify -d stockify \
  -c "SELECT count(*) FROM items WHERE name='Barang Invalid';"
```

**Harus terlihat:** `0`.

---

### L6 — Delete (05:00)

**Browser** → klik **Hapus** pada `Monitor 27 inci` → konfirmasi **OK**.

**Harus terlihat:** pesan *"Barang berhasil dihapus."*, baris hilang, kartu statistik
kembali seperti semula.

---

### L7 — Health check & log (05:30) — *Anggota 2*

**Terminal:**

```bash
curl http://localhost:8000/health
```

**Harus terlihat:**

```json
{"status":"healthy","database":"connected","engine":"postgresql",
 "server_version":"PostgreSQL 16.15 on x86_64-pc-linux-musl"}
```

**Terminal:**

```bash
docker compose logs backend --tail 5
```

**Harus terlihat** baris seperti:
`INFO:  172.19.0.4:53678 - "GET /items HTTP/1.1" 200 OK`

**Terminal:**

```bash
docker compose logs db --tail 3
```

**Harus terlihat:** `LOG:  database system is ready to accept connections`

> Narasi: "Health check bukan sekadar 'proses hidup' — ia benar-benar membuka koneksi
> ke PostgreSQL dan melaporkan versinya. Semua request juga tercatat di log container."

---

### L8 — Persistensi data (06:30) — *Anggota 3* ⚠️ langkah paling penting

> **Peringatan:** gunakan `down` **tanpa** `-v`. Jangan ketik `down -v`.

**Terminal:**

```bash
docker compose down
```

**Harus terlihat:** container dihapus, dan **named volume tetap ada**:

```bash
docker volume ls | grep stockify
```

**Harus terlihat:** `stockify_pgdata`

**Terminal:**

```bash
docker compose up -d
docker compose ps
```

Tunggu sampai 3 container `healthy` (±30 detik).

**Browser** → refresh `http://localhost:8080`.

**Harus terlihat:** barang yang tersisa **masih ada**, kartu statistik sama seperti
sebelumnya.

**Terminal** (bukti terakhir):

```bash
docker compose exec -T db psql -U stockify -d stockify \
  -c "SELECT count(*) AS jumlah_barang FROM items;"
```

**Harus terlihat:** jumlah barang **sama** dengan sebelum `down`.

> Narasi: "Container-nya dihapus dan dibuat ulang, tapi datanya tetap. Itu karena
> PostgreSQL menyimpan datanya di named volume, bukan di dalam container."

---

### L9 — Penanganan error & pemulihan (08:30) — *Anggota 3*

**Terminal:**

```bash
docker compose stop db
```

**Browser** → refresh `http://localhost:8080` (tunggu ±5 detik).

**Harus terlihat:** pesan merah
*"Database PostgreSQL tidak dapat diakses."* (atau *"Layanan API sedang tidak tersedia…"*)
dan tabel kosong — **aplikasi tidak freeze**.

**Terminal** — buktikan penyebabnya tercatat di log:

```bash
docker compose logs backend --tail 5
```

**Harus terlihat:**

```
WARNING: Database PostgreSQL tidak dapat diakses (GET /items): OperationalError: ...
INFO:     172.19.0.1:40298 - "GET /items HTTP/1.1" 503 Service Unavailable
```

**Pemulihan:**

```bash
docker compose start db
```

Tunggu ±10 detik → **Browser refresh** → aplikasi normal kembali, data utuh.

> Narasi: "Kalau database mati, user tidak melihat halaman error generik. Dia melihat
> pesan yang jelas, dan penyebabnya tercatat di log — jadi mudah blameshift."

---

### L10 — Penutup (09:30)

Kembali ke terminal, jalankan sekali:

```bash
docker compose ps
```

**Harus terlihat:** 3 container `healthy`.

> Narasi: "Jadi: satu perintah menjalankan semuanya, data tidak hilang, error ditangani
> dengan pesan yang jelas dan tercatat di log. Terima kasih — kami siap menjawab
> pertanyaan."

---

## 3. Ringkasan yang Wajib Hafal

| Factsheet | Nilai |
|---|---|
| Perintah menjalankan | `docker compose up --build -d` |
| UI | http://localhost:8080 |
| API + Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Data JSON | http://localhost:8080/api/items |
| Service | `db`, `backend`, `frontend` |
| Named volume | `stockify_pgdata` |
| Endpoint | 7 (`/`, `/health`, `/items`, `/items/{id}`, ×POST/PUT/DELETE) |
| Hasil uji | 134/135 pemeriksaan PASS (92/93 API+infra, 22/22 & 20/20 frontend) |
| Satu-satunya yang belum | berkas `LICENSE` ⚠️ (keputusan tim) |

---

## 4. Angka yang Harus Benar (cek sebelum demo)

Demo involves nilai yang harus cocok. Hitung ulang setelah mengisi data demo:

| Nilai | Cara cek |
|---|---|
| Total stok | `docker compose exec -T db psql -U stockify -d stockify -c "SELECT sum(stock) FROM items;"` |
| Jumlah barang | `... -c "SELECT count(*) FROM items;"` |
| Total nilai | `... -c "SELECT sum(stock*price) FROM items;"` (bandingkan dengan kartu di UI) |

---

## 5. Yang Jangan Dilakukan

| Jangan | Alasan |
|---|---|
| `docker compose down -v` | **Menghapus volume & data.** Tinggalkan `down` biasa. |
| `docker system prune -a --volumes` | Sama — menghapus volume. |
| `docker volume rm stockify_pgdata` | Menghapus data demo. |
| Menjalankan `docker compose down -v` "untuk demo persistensi" | Justru menghapus bukti persistensi. |
| Mengubah kode saat demo | Risiko tinggi; siapkan slide sebagai cadangan. |
| Membuka terminal yang menampilkan password | Tutup `.env` sebelum presentasi. |

---

## 6. Konten Cadangan (jika ada waktu atau demo gagal)

- `docs/ARCHITECTURE.md` — diagram Mermaid & ASCII untuk slide
- `docs/TESTING.md` — 134 pemeriksaan + bukti aktual + 5 bug yang ditemukan
- `README.md` — cara instalasi, konfigurasi, endpoint, troubleshooting
- `docs/PRESENTATION.md` — outline slide, pembagian peran, 10 Q&A

---

## 7. Risk List & Langkah Pemulihan

| # | Risiko | Gejala | Pemulihan (teruji) | Waktu |
|---|---|---|---|---|
| R1 | **Container `db` tidak healthy** saat demo | `/health` → 503, UI error | `docker compose restart db` → tunggu 15 dtk → `docker compose ps` | 30 dtk |
| R2 | **Backend mati / tidak start** | UI: *"Layanan API sedang tidak tersedia (HTTP 502)"* | `docker compose up -d backend` → tunggu healthy | 30 dtk |
| R3 | **Frontend mati** | Halaman tidak terbuka di :8080 | `docker compose up -d frontend` | 20 dtk |
| R4 | **Port bentrok** (`port is already allocated`) | `docker compose up` gagal | Cek `netstat -ano | findstr :8080`; matikan prosesnya, atau ubah `FRONTEND_PORT` di `.env` lalu `up -d` | 2 mnt |
| R5 | **Volume terisi data lama yang tidak sesuai** | Tabel menampilkan data tak terduga | `docker compose exec -T db psql -U stockify -d stockify -c "DELETE FROM items WHERE id > 1;"` (hapus baris demo, pertahankan `Monitor`) | 20 dtk |
| R6 | **Data demo tidak sengaja terhapus** | Tabel kosong | Restore dari backup: `docker compose exec -T db psql -U stockify -d stockify < backup-demo.sql` | 1 mnt |
| R7 | **Docker Desktop mati** | Semua perintah docker gagal | Buka Docker Desktop, tunggu "running", lalu `docker compose up -d` | 2–3 mnt |
| R8 | **`.env` hilang / password tidak cocok dengan volume** | 503 & log `password authentication failed` | `docker compose down` (bukan `-v`) → pastikan `.env` berisi password yang sama → `up -d`. **Jangan** `down -v` (menghapus data) | 1 mnt |
| R9 | **Jaringan kampus memblokir localhost:8080 dari perangkat lain** | Browser di laptop lain tidak bisa buka | Demo dari laptop presenter sendiri (localhost selalu boleh) | 0 dtk |
| R10 | **Nginx balas 500 di `/api/*`** | Halaman terbuka, API error | Gejala ini pernah terjadi dan sudah diperbaiki (urutan `set` sebelum `rewrite`). Pastikan image terbaru: `docker compose up -d --build frontend` | 2 mnt |
| R11 | **Demo terlalu lama** | Terlambat | Lewati L3 (pencarian) & L4 (update terminal), sebut ringkas: "bagian ini sudah terbukti di laporan uji" | — |
| R12 | **Browser cache file lama** | Tampilan tidak sesuai | `Ctrl+Shift+R` (hard refresh) | 5 dtk |

**Skenario terburuk (semua gagal):** buka `docs/TESTING.md` dan tunjukkan tabel hasil uji
(134/135 PASS) + screenshot yang sudah disiapkan. Jelaskan bahwa aplikasinya berjalan,
hanya lingkungan presentasi yang bermasalah.

---

## 8. Verifikasi Naskah Ini (sudah dijalankan)

| Yang diperiksa | Cara | Hasil |
|---|---|---|
| Semua perintah demo valid | `docker compose ps`, `psql`, `curl`, `logs`, `volume ls` dijalankan nyata | ✅ |
| `down` → `up` benar-benar mempertahankan data | Uji T6 (9/9 PASS) | ✅ |
| Health check & log menghasilkan output seperti di naskah | Uji T5 & T9 | ✅ |
| Pesan error saat DB mati persis seperti ditulis | Uji T7 + timeline frontend | ✅ |
| Nilai versi PostgreSQL quoted benar | `docker exec stockify-db postgres --version` | `16.15` |

> ⚠️ **Bukti tambahan yang dibutuhkan:** screenshot 12 item, dan konfirmasi manual
> bahwa pesan yang tampil di layar sama persis dengan kutipan pada naskah ini
> (kalimatnya bisa sedikit berbeda — lebih baik ditunjukkan lewat screenshot).
