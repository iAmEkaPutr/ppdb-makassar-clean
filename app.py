import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json

# Load data
@st.cache_data
def load_data():
    with open("ppdb.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# Sidebar filters
st.sidebar.title("Filter PPDB Makassar")

jenjang_options = sorted(df["jenjang"].unique())
selected_jenjang = st.sidebar.multiselect(
    "Jenjang",
    options=jenjang_options,
    default=jenjang_options
)

jalur_options = sorted(df["jalur"].unique())
selected_jalur = st.sidebar.multiselect(
    "Jalur",
    options=jalur_options,
    default=jalur_options
)

# Filter data
filtered_df = df[
    df["jenjang"].isin(selected_jenjang) &
    df["jalur"].isin(selected_jalur)
]

st.title("PPDB Makassar Dashboard")
st.write(f"Menampilkan {len(filtered_df):,} data")

# Tampilkan tabel
st.subheader("Data Tabel")
st.dataframe(
    filtered_df[["jenjang", "jalur", "nama_sekolah_tujuan", "pendaftaran_id", "status_penerimaan"]],
    use_container_width=True
)

# Buat map dengan Folium
if not filtered_df.empty:
    st.subheader("Peta Distribusi")

    # Center map ke Makassar
    m = folium.Map(location=[-5.14, 119.42], zoom_start=12, tiles="OpenStreetMap")

    # Warna berdasarkan sekolah (sederhana)
    school_colors = {school: color for school, color in zip(
        filtered_df["nama_sekolah_tujuan"].unique(),
        ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]
    )}

    for _, row in filtered_df.iterrows():
        lat = float(str(row["lintang"]).replace(",", "."))
        lon = float(str(row["bujur"]).replace(",", "."))
        status = row["status_penerimaan"] or "Tidak Lulus"
        color = school_colors.get(row["nama_sekolah_tujuan"], "gray")

        if status.lower() == "lulus":
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"ID: {row['pendaftaran_id']}<br>Status: Lulus<br>Sekolah: {row['nama_sekolah_tujuan']}"
            ).add_to(m)
        else:
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color="red", icon="times", prefix="fa"),
                popup=f"ID: {row['pendaftaran_id']}<br>Status: {status}<br>Sekolah: {row['nama_sekolah_tujuan']}"
            ).add_to(m)

    # Render map di Streamlit
    st_folium(m, width=1000, height=600)
else:
    st.info("Tidak ada data yang cocok dengan filter.")