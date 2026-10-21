
// Alamat API datang dari frontend/config.js (runtime config).
// Dev (Live Server) : http://127.0.0.1:8000
// Docker (Nginx)    : /api  (satu origin, proxy ke container backend)
const API_BASE =
  (window.STOCKIFY_CONFIG && window.STOCKIFY_CONFIG.apiBase) ||
  "http://127.0.0.1:8000";

const items = [];
let editingId = null;
let isLoading = true;

const $ = (id) => document.getElementById(id);

const formPanel = $("formPanel");
const itemForm = $("itemForm");
const itemTable = $("itemTable");
const message = $("message");

// Label field error dari FastAPI agar pesannya mudah dipahami.
const FIELD_LABELS = {
  name: "Nama barang",
  category: "Kategori",
  stock: "Stok",
  price: "Harga"
};

const rupiah = (value) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 2
  }).format(value);

function showMessage(text, type = "success") {
  message.textContent = text;
  message.className = type;
}

// Error dari API (koneksi gagal atau response tidak sukses).
class ApiError extends Error {
  constructor(text, status = 0) {
    super(text);
    this.name = "ApiError";
    this.status = status;
  }
}

function detailToMessage(payload, status) {
  const detail = payload ? payload.detail : null;

  if (typeof detail === "string" && detail) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((error) => {
        const field = Array.isArray(error.loc)
          ? error.loc[error.loc.length - 1]
          : null;
        const label = FIELD_LABELS[field] || field;

        return label ? `${label}: ${error.msg}` : error.msg;
      })
      .join(" ");
  }

  // 502/503/504 berarti layanan di belakang API tidak bisa dihubungi.
  if (status === 502 || status === 503 || status === 504) {
    return `Layanan API sedang tidak tersedia (HTTP ${status}). ` +
      "Pastikan backend Stockify berjalan.";
  }

  return `Permintaan ke API gagal (HTTP ${status}).`;
}

// Satu pintu untuk semua panggilan ke backend Stockify.
async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
  } catch (error) {
    throw new ApiError(
      `Tidak dapat terhubung ke API di ${API_BASE}. ` +
        "Pastikan backend berjalan (python -m uvicorn main:app --reload).",
      0
    );
  }

  const text = await response.text();
  let payload = null;

  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      payload = null;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      detailToMessage(payload, response.status),
      response.status
    );
  }

  return payload;
}

// READ: ambil daftar barang dari API.
async function loadItems() {
  const data = await apiRequest("/items");

  items.splice(
    0,
    items.length,
    ...(Array.isArray(data) ? data : [])
  );

  isLoading = false;
  renderItems();
}

function appendEmptyRow(text) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");

  cell.colSpan = 6;
  cell.className = "empty";
  cell.textContent = text;

  row.appendChild(cell);
  itemTable.appendChild(row);
}

function renderItems() {
  const query = $("searchInput").value.toLowerCase().trim();

  const filtered = items.filter((item) => {
    const name = String(item.name ?? "").toLowerCase();
    const category = String(item.category ?? "").toLowerCase();

    return name.includes(query) || category.includes(query);
  });

  $("totalItems").textContent = items.length;
  $("totalStock").textContent = items.reduce(
    (sum, item) => sum + Number(item.stock || 0),
    0
  );

  $("totalValue").textContent = rupiah(
    items.reduce(
      (sum, item) =>
        sum + Number(item.stock || 0) * Number(item.price || 0),
      0
    )
  );

  itemTable.replaceChildren();

  if (isLoading) {
    appendEmptyRow("Memuat data dari API...");
    return;
  }

  if (filtered.length === 0) {
    appendEmptyRow(
      query
        ? "Tidak ada barang yang ditemukan."
        : "Belum ada data barang."
    );
    return;
  }

  filtered.forEach((item) => {
    const row = document.createElement("tr");

    [
      item.id,
      item.name,
      item.category,
      item.stock,
      rupiah(item.price)
    ].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });

    const actions = document.createElement("td");

    const editBtn = document.createElement("button");
    editBtn.textContent = "Edit";
    editBtn.className = "action-btn";
    editBtn.addEventListener("click", () => editItem(item.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Hapus";
    deleteBtn.className = "action-btn delete-btn";
    deleteBtn.addEventListener("click", () => deleteItem(item.id));

    actions.append(editBtn, deleteBtn);
    row.appendChild(actions);
    itemTable.appendChild(row);
  });
}

function openForm(item = null) {
  editingId = item ? item.id : null;

  $("formTitle").textContent =
    item ? "Edit Barang" : "Tambah Barang";

  $("name").value = item?.name ?? "";
  $("category").value = item?.category ?? "";
  $("stock").value = item?.stock ?? "";
  $("price").value = item?.price ?? "";

  formPanel.hidden = false;
  formPanel.scrollIntoView({ behavior: "smooth" });
}

function editItem(id) {
  const item = items.find((entry) => entry.id === id);
  if (item) openForm(item);
}

// DELETE: hapus barang melalui API.
async function deleteItem(id) {
  const item = items.find((entry) => entry.id === id);

  if (!confirm(`Yakin ingin menghapus "${item ? item.name : id}"?`)) {
    return;
  }

  try {
    await apiRequest(`/items/${id}`, { method: "DELETE" });
  } catch (error) {
    showMessage(error.message, "error");
    return;
  }

  try {
    await loadItems();
    showMessage("Barang berhasil dihapus.");
  } catch (error) {
    showMessage(
      `Barang berhasil dihapus, tetapi gagal memuat ulang daftar: ${error.message}`,
      "error"
    );
  }
}

function setBusy(isBusy) {
  $("saveBtn").disabled = isBusy;
  $("saveBtn").textContent = isBusy ? "Menyimpan..." : "Simpan";
  $("addBtn").disabled = isBusy;
}

// CREATE dan UPDATE: kirim data form ke API.
itemForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = $("name").value.trim();
  const category = $("category").value.trim();
  const stock = Number($("stock").value);
  const price = Number($("price").value);

  if (!name || !category) {
    showMessage("Nama dan kategori wajib diisi.", "error");
    return;
  }

  if (
    $("stock").value.trim() === "" ||
    !Number.isInteger(stock) ||
    stock < 0 ||
    $("price").value.trim() === "" ||
    !Number.isFinite(price) ||
    price < 0
  ) {
    showMessage(
      "Stok harus bilangan bulat >= 0 dan harga harus >= 0.",
      "error"
    );
    return;
  }

  const isUpdate = editingId !== null;
  const payload = JSON.stringify({ name, category, stock, price });

  setBusy(true);

  try {
    if (isUpdate) {
      await apiRequest(`/items/${editingId}`, {
        method: "PUT",
        body: payload
      });
    } else {
      await apiRequest("/items", { method: "POST", body: payload });
    }
  } catch (error) {
    showMessage(error.message, "error");
    setBusy(false);
    return;
  }

  setBusy(false);

  formPanel.hidden = true;
  itemForm.reset();
  editingId = null;

  try {
    await loadItems();
    showMessage(
      isUpdate
        ? "Barang berhasil diperbarui."
        : "Barang berhasil ditambahkan."
    );
  } catch (error) {
    showMessage(
      `Barang berhasil disimpan, tetapi gagal memuat ulang daftar: ${error.message}`,
      "error"
    );
  }
});

$("addBtn").addEventListener("click", () => openForm());

$("cancelBtn").addEventListener("click", () => {
  formPanel.hidden = true;
  itemForm.reset();
  editingId = null;
});

$("searchInput").addEventListener("input", renderItems);

// Tampilkan status "Memuat data dari API..." sebelum request pertama selesai.
renderItems();

// Muat data dari API saat halaman dibuka.
(async function init() {
  try {
    await loadItems();
  } catch (error) {
    items.length = 0;
    isLoading = false;
    renderItems();
    showMessage(error.message, "error");
  }
})();
