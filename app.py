import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json

# ================= CONFIG =================
st.set_page_config(
    page_title="PPDB Makassar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================= CSS =================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #1a202c !important;
    color: white !important;
}
.filter-title {
    color: #63b3ed;
    font-weight: bold;
    font-size: 13px;
    margin: 10px 0;
}
.header-bar {
    padding: 12px 20px;
    background: white;
    box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    border-radius: 5px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
}
#MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    with open("ppdb.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df["lintang"] = df["lintang"].astype(str).str.replace(",", ".").astype(float)
    df["bujur"] = df["bujur"].astype(str).str.replace(",", ".").astype(float)
    return df

df = load_data()

# ================= WARNA SEKOLAH =================
warna_list = [
    "#e53e3e", "#3182ce", "#38a169", "#d69e2e",
    "#805ad5", "#319795", "#dd6b20", "#00b5d8",
    "#b794f4", "#f687b3"
]

sekolah_unik = df["nama_sekolah_tujuan"].dropna().unique()
school_colors = {
    sekolah: warna_list[i % len(warna_list)]
    for i, sekolah in enumerate(sekolah_unik)
}

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🏫 PPDB MAKASSAR")

    st.markdown('<div class="filter-title">JENJANG</div>', unsafe_allow_html=True)
    selected_jenjang = []
    for j in sorted(df["jenjang"].dropna().unique()):
        if st.checkbox(j, key=f"jenjang_{j}"):
            selected_jenjang.append(j)

    st.markdown('<div class="filter-title">JALUR</div>', unsafe_allow_html=True)
    selected_jalur = []
    for j in sorted(df["jalur"].dropna().unique()):
        if st.checkbox(j, key=f"jalur_{j}"):
            selected_jalur.append(j)

# ================= FILTER DATA =================
if selected_jenjang or selected_jalur:
    filtered_df = df.copy()

    if selected_jenjang:
        filtered_df = filtered_df[filtered_df["jenjang"].isin(selected_jenjang)]

    if selected_jalur:
        filtered_df = filtered_df[filtered_df["jalur"].isin(selected_jalur)]
else:
    filtered_df = pd.DataFrame()  # MAP KOSONG

# ================= HEADER =================
st.markdown(f"""
<div class="header-bar">
    <div><b>Map PPDB</b> – Default Kosong</div>
    <div><b>O</b> = Lulus &nbsp;&nbsp; <b>X</b> = Tidak Lulus</div>
</div>
""", unsafe_allow_html=True)

# ================= TABS =================
tab_map, tab_data = st.tabs(["🗺 MAP", "📋 DATA"])

# ================= MAP =================
with tab_map:
    m = folium.Map(
        location=[-5.14, 119.42],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            lat, lon = row["lintang"], row["bujur"]
            sekolah = row["nama_sekolah_tujuan"]
            warna = school_colors.get(sekolah, "#666666")
            status = str(row.get("status_penerimaan", "")).lower()

            popup = f"""
            <b>ID:</b> {row['pendaftaran_id']}<br>
            <b>Sekolah:</b> {sekolah}<br>
            <b>Status:</b> {row['status_penerimaan']}
            """

            if status == "lulus":
                # O (Lingkaran)
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=7,
                    color=warna,
                    weight=3,
                    fill=False,
                    popup=popup
                ).add_to(m)
            else:
                # X
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.Icon(
                        icon="times",
                        prefix="fa",
                        icon_color=warna,
                        color="white"
                    ),
                    popup=popup
                ).add_to(m)

    st_folium(m, width="100%", height=650)

# ================= DATA =================
with tab_data:
    if filtered_df.empty:
        st.info("Centang filter di sidebar untuk menampilkan data.")
    else:
        st.dataframe(
            filtered_df[
                ["jenjang", "jalur", "nama_sekolah_tujuan",
                 "pendaftaran_id", "status_penerimaan"]
            ],
            use_container_width=True
        )
