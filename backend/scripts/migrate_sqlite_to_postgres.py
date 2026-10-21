"""Migrasi data barang dari SQLite lama ke PostgreSQL (Phase 3 Stockify).

Aturan penting:
- File SQLite dibuka READ-ONLY (mode=ro). Data lama tidak diubah atau dihapus.
- Skrip idempoten: aman dijalankan berulang kali (ON CONFLICT DO NOTHING).
- PostgreSQL menjadi sumber data utama setelah migrasi.

Cara pakai:
    cd backend
    .\\.venv\\Scripts\\python.exe scripts\\migrate_sqlite_to_postgres.py
    .\\.venv\\Scripts\\python.exe scripts\\migrate_sqlite_to_postgres.py --dry-run
"""

import argparse
from pathlib import Path
import sqlite3
import sys

import psycopg


BACKEND_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BACKEND_DIR / "inventory.db"

# Impor konfigurasi database yang sama dengan backend/main.py.
sys.path.insert(0, str(BACKEND_DIR))

from main import get_database_config, initialize_database  # noqa: E402


def read_sqlite_items():
    """Membaca barang dari SQLite tanpa mengubah file-nya."""
    if not SQLITE_PATH.exists():
        print(f"[SQLite] File tidak ditemukan: {SQLITE_PATH}")
        return []

    # mode=ro -> SQLite dijamin hanya membaca, tidak menulis/menghapus.
    uri = f"{SQLITE_PATH.as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)

    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, name, category, stock, price FROM items ORDER BY id"
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def migrate(items, dry_run=False):
    """Menyalin barang dari SQLite ke PostgreSQL."""
    copied = 0
    skipped = 0

    # Pastikan tabel items sudah ada di PostgreSQL (idempotent).
    initialize_database()

    with psycopg.connect(**get_database_config()) as connection:
        for item in items:
            if dry_run:
                print(
                    f"  [dry-run] akan menyalin id={item['id']} "
                    f"{item['name']} ({item['category']})"
                )
                copied += 1
                continue

            row = connection.execute(
                """
                INSERT INTO items (id, name, category, stock, price)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                (
                    item["id"],
                    item["name"],
                    item["category"],
                    item["stock"],
                    item["price"],
                ),
            ).fetchone()

            if row:
                copied += 1
                print(
                    f"  tersalin : id={item['id']} {item['name']} "
                    f"({item['category']}) stok={item['stock']} "
                    f"harga={item['price']}"
                )
            else:
                skipped += 1
                print(
                    f"  dilewati : id={item['id']} {item['name']} "
                    "(sudah ada di PostgreSQL)"
                )

        if not dry_run:
            # Samakan sequence SERIAL dengan id terbesar agar insert
            # otomatis berikutnya tidak bentrok dengan id yang disalin.
            connection.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('items', 'id'),
                    COALESCE((SELECT MAX(id) FROM items), 1)
                )
                """
            )
            print("  sequence id (SERIAL) sudah diselaraskan.")

    return copied, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Migrasi data SQLite ke PostgreSQL untuk Stockify."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tampilkan rencana tanpa menulis ke PostgreSQL.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("MIGRASI SQLITE -> POSTGRAGSQL (Stockify Phase 3)")
    print("=" * 70)

    items = read_sqlite_items()
    print(f"\n[SQLite] {len(items)} baris dibaca dari {SQLITE_PATH}")

    config = dict(get_database_config())
    if "password" in config:
        config["password"] = "***"
    print(f"[PostgreSQL] target: {config}\n")

    copied, skipped = migrate(items, dry_run=args.dry_run)

    print("\n" + "-" * 70)
    print(f"Selesai. disalin={copied} dilewati={skipped}")
    print(f"File SQLite TIDAK dihapus dan tetap utuh: {SQLITE_PATH}")
    print("Verifikasi dengan: SELECT * FROM items;")
    print("-" * 70)


if __name__ == "__main__":
    main()
