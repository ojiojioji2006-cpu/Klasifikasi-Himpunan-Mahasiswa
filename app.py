import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# KONFIGURASI APLIKASI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Klasifikasi Himpunan Mahasiswa",
    page_icon="📊",
    layout="wide",
)

DATASET_A_PATH = "dataset/mahasiswa.csv"
DATASET_B_PATH = "dataset/mahasiswa_akademik.csv"


# -----------------------------------------------------------------------------
# FUNGSI PENDUKUNG
# -----------------------------------------------------------------------------
@st.cache_data
def load_dataset(filepath: str) -> pd.DataFrame:
    """Membaca CSV dengan auto-detect separator dan merapikan header."""
    try:
        df = pd.read_csv(filepath, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(filepath, sep=",")

    df.columns = df.columns.astype(str).str.strip()
    return df


def get_default_key(df: pd.DataFrame) -> str:
    """Mencari nama kolom kunci yang paling umum."""
    candidates = ["NIM", "NAMA", "ID", "NAMA_MAHASISWA"]
    for col in df.columns:
        if col.upper() in candidates:
            return col
    return df.columns[0]


def run_set_operation(
    op: str, df_a: pd.DataFrame, df_b: pd.DataFrame, key_a: str, key_b: str
) -> tuple[pd.DataFrame, str]:
    """Menjalankan kalkulasi teori himpunan berbasis set operator Python."""
    set_a = set(df_a[key_a])
    set_b = set(df_b[key_b])

    if op == "Irisan (A ∩ B)":
        keys = set_a & set_b
        desc = "Anggota yang terdaftar di Himpunan A **sekaligus** Himpunan B."
        result = df_a[df_a[key_a].isin(keys)].copy()

    elif op == "Gabungan (A ∪ B)":
        desc = "Seluruh anggota Himpunan A dan Himpunan B (tanpa duplikasi)."
        result = pd.concat([df_a, df_b], ignore_index=True).drop_duplicates(
            subset=[key_a] if key_a in df_b.columns else None
        )

    elif op == "Selisih (A - B)":
        keys = set_a - set_b
        desc = "Anggota Himpunan A yang **tidak ada** di Himpunan B."
        result = df_a[df_a[key_a].isin(keys)].copy()

    elif op == "Selisih (B - A)":
        keys = set_b - set_a
        desc = "Anggota Himpunan B yang **tidak ada** di Himpunan A."
        result = df_b[df_b[key_b].isin(keys)].copy()

    elif op == "Beda Setangkai (A ⊕ B)":
        keys = set_a ^ set_b
        desc = "Anggota yang **hanya ada di salah satu** himpunan (eksklusif A atau B)."
        res_a = df_a[df_a[key_a].isin(keys)]
        res_b = df_b[df_b[key_b].isin(keys)]
        result = pd.concat([res_a, res_b], ignore_index=True)

    else:
        result = pd.DataFrame()
        desc = ""

    return result, desc


# -----------------------------------------------------------------------------
# APLIKASI UTAMA
# -----------------------------------------------------------------------------
def main():
    st.title("📊 Klasifikasi Himpunan Mahasiswa")
    st.caption("Proyek PJBL 2 — Pengolahan Data Teori Himpunan")

    # Load dataset
    try:
        df_a = load_dataset(DATASET_A_PATH)
        df_b = load_dataset(DATASET_B_PATH)
    except FileNotFoundError as e:
        st.error(f"Dataset tidak ditemukan di folder `dataset/`. Detail: {e}")
        return
    except Exception as e:
        st.error(f"Gagal membaca dataset: {e}")
        return

    # Panel Kontrol (Sidebar)
    st.sidebar.header("Kontrol Data")

    # Pemilih kolom acuan (auto-select tapi bisa diganti manual jika perlu)
    def_a = get_default_key(df_a)
    def_b = get_default_key(df_b)

    key_a = st.sidebar.selectbox("Kolom Acuan Himpunan A", df_a.columns, index=list(df_a.columns).index(def_a))
    key_b = st.sidebar.selectbox("Kolom Acuan Himpunan B", df_b.columns, index=list(df_b.columns).index(def_b))

    # Sanitasi string pada kolom acuan
    df_a[key_a] = df_a[key_a].astype(str).str.strip()
    df_b[key_b] = df_b[key_b].astype(str).str.strip()

    st.sidebar.divider()

    operation = st.sidebar.selectbox(
        "Operasi Himpunan",
        [
            "Irisan (A ∩ B)",
            "Gabungan (A ∪ B)",
            "Selisih (A - B)",
            "Selisih (B - A)",
            "Beda Setangkai (A ⊕ B)",
        ],
    )

    search_query = st.sidebar.text_input("Cari Data", placeholder="Ketik kata kunci...")

    # Ringkasan Metrik (Native Streamlit Components)
    set_a = set(df_a[key_a])
    set_b = set(df_b[key_b])

    col1, col2, col3 = st.columns(3)
    col1.metric("Anggota Himpunan A", len(set_a))
    col2.metric("Anggota Himpunan B", len(set_b))
    col3.metric("Total Unik (A ∪ B)", len(set_a | set_b))

    st.divider()

    # Preview Dataset Mentah
    with st.expander("Lihat Data Mentah", expanded=False):
        tab1, tab2 = st.tabs(["Himpunan A (Mahasiswa)", "Himpunan B (Akademik)"])
        with tab1:
            st.dataframe(df_a, use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(df_b, use_container_width=True, hide_index=True)

    # Eksekusi Operasi Himpunan
    df_result, description = run_set_operation(operation, df_a, df_b, key_a, key_b)

    st.subheader(f"Hasil: {operation}")
    st.info(f"{description}\n\n**Total Data:** {len(df_result)} baris")

    # Filter Pencarian (Opsional)
    if search_query:
        mask = df_result.apply(
            lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1
        )
        df_result = df_result[mask]
        st.caption(f"Menampilkan hasil pencarian untuk '{search_query}': {len(df_result)} data.")

    # Tampilan Tabel Hasil & Download Button
    if not df_result.empty:
        st.dataframe(df_result, use_container_width=True, hide_index=True)

        csv_data = df_result.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV Hasil",
            data=csv_data,
            file_name="hasil_himpunan.csv",
            mime="text/csv",
        )
    else:
        st.warning("Tidak ada data yang memenuhi kriteria operasi ini.")


if __name__ == "__main__":
    main()