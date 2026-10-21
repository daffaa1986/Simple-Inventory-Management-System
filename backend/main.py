
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import time

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, Field


# Folder backend sebagai lokasi .env dan skrip migrasi.
BASE_DIR = Path(__file__).resolve().parent

# Konfigurasi diambil dari environment variables.
# File .env hanya dipakai untuk pengembangan lokal (tidak ikut di-commit).
load_dotenv(BASE_DIR / ".env")

# Logging supaya error database bisa ditelusuri lewat log container.
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("stockify")


def get_database_config():
    """Mengambil konfigurasi koneksi PostgreSQL dari environment variables.

    Mendukung dua bentuk:
    1. DATABASE_URL  -> postgresql://user:password@host:port/database
    2. POSTGRES_HOST / POSTGRES_PORT / POSTGRES_DB / POSTGRES_USER /
       POSTGRES_PASSWORD (dipakai bila DATABASE_URL tidak diset).

    connect_timeout mencegah request menggantung tak terbatas saat
    PostgreSQL tidak bisa dijangkau (penting untuk health check).
    """
    try:
        connect_timeout = int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5"))
    except ValueError:
        connect_timeout = 5

    config = {"connect_timeout": connect_timeout}

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        config["conninfo"] = database_url
        return config

    config.update(
        {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "dbname": os.getenv("POSTGRES_DB", "stockify"),
            "user": os.getenv("POSTGRES_USER", "stockify"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
    )

    return config


def get_connection():
    """Membuka koneksi baru ke PostgreSQL."""
    return psycopg.connect(**get_database_config(), row_factory=dict_row)


def initialize_database():
    """Membuat tabel items bila belum ada.

    Menunggu PostgreSQL siap dipakai (berguna saat container baru start)
    lalu membuat skema tabel Stockify.
    """
    last_error = None

    for attempt in range(1, 6):
        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        stock INTEGER NOT NULL CHECK (stock >= 0),
                        price DOUBLE PRECISION NOT NULL CHECK (price >= 0)
                    )
                    """
                )
            return
        except psycopg.Error as error:
            last_error = error
            if attempt < 5:
                time.sleep(2)

    raise RuntimeError(
        f"PostgreSQL tidak dapat diakses: {last_error}"
    ) from last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Simple Inventory Management API",
    description="REST API untuk mengelola data barang.",
    version="1.0.0",
    lifespan=lifespan,
)


# Untuk pengembangan lokal dengan Live Server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(psycopg.Error)
def handle_database_error(request, exc):
    """Ubah error PostgreSQL menjadi 503 yang jelas (bukan 500 mentah).

    Error juga dicatat ke log container supaya penyebabnya bisa ditelusuri.
    """
    logger.warning(
        "Database PostgreSQL tidak dapat diakses (%s %s): %s: %s",
        request.method,
        request.url.path,
        type(exc).__name__,
        exc,
    )

    return JSONResponse(
        status_code=503,
        content={"detail": "Database PostgreSQL tidak dapat diakses."},
    )


# Model untuk memvalidasi input.
class ItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0, le=2_147_483_647)
    price: float = Field(ge=0, allow_inf_nan=False)


def normalize_item(item: ItemInput):
    name = item.name.strip()
    category = item.category.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Nama barang tidak boleh kosong.",
        )

    if not category:
        raise HTTPException(
            status_code=422,
            detail="Kategori barang tidak boleh kosong.",
        )

    return name, category, item.stock, item.price


def row_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "stock": row["stock"],
        "price": row["price"],
    }


@app.get("/")
def root():
    return {
        "message": "Simple Inventory Management API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    try:
        connection = get_connection()
    except psycopg.Error as error:
        logger.warning(
            "Health check gagal: PostgreSQL tidak dapat diakses: %s: %s",
            type(error).__name__,
            error,
        )
        raise HTTPException(
            status_code=503,
            detail="Database PostgreSQL tidak dapat diakses.",
        ) from error

    try:
        with connection:
            row = connection.execute("SELECT version()").fetchone()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Database PostgreSQL tidak dapat diakses.",
        ) from error

    server_version = row["version"].split(",")[0] if row else "tidak diketahui"

    return {
        "status": "healthy",
        "database": "connected",
        "engine": "postgresql",
        "server_version": server_version,
    }


# READ: mengambil semua barang.
@app.get("/items")
def get_items():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM items ORDER BY id DESC"
        ).fetchall()

    return [row_to_dict(row) for row in rows]


# READ: mengambil satu barang berdasarkan ID.
@app.get("/items/{item_id}")
def get_item(item_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM items WHERE id = %s",
            (item_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Barang tidak ditemukan.",
        )

    return row_to_dict(row)


# CREATE: menambahkan barang baru.
@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemInput):
    name, category, stock, price = normalize_item(item)

    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO items (name, category, stock, price)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, category, stock, price
            """,
            (name, category, stock, price),
        ).fetchone()

    return row_to_dict(row)


# UPDATE: mengganti seluruh data barang berdasarkan ID.
@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemInput):
    name, category, stock, price = normalize_item(item)

    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE items
            SET name = %s, category = %s, stock = %s, price = %s
            WHERE id = %s
            RETURNING id, name, category, stock, price
            """,
            (name, category, stock, price, item_id),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Barang tidak ditemukan.",
        )

    return row_to_dict(row)


# DELETE: menghapus barang berdasarkan ID.
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM items WHERE id = %s",
            (item_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Barang tidak ditemukan.",
            )

    return {
        "message": "Barang berhasil dihapus.",
        "id": item_id,
    }
