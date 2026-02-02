import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
from folium import Icon

# -----------------------------
# CONFIG & THEME (mirip dark sidebar)
# -----------------------------
st.set_page_config(
    page_title="PPDB Makassar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS untuk mirip UI asli (dark sidebar, header, badge)
st.markdown("""
    <style>
    /* Sidebar dark theme */
    section[data-testid="stSidebar"] {
        background-color: #1a202c !important;
        color: white !important;
    }
    .sidebar .sidebar-content {
        background-color: #1a202c !important;
    }
    /* Filter title */
    .filter-title {
        color: #4299e1 !important;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    /* Button kecil All/None */
    .small-btn {
        font-size: 10px !important;
        padding: 4px 8px !important;
        background: #4a5568 !important;
        color: white !important;
        border-radius: 3px !important;
        border: none !important;
        margin-left: 5px !important;
    }
    /* Header bar */
    .header-bar {
        padding: 12px 25px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        font-weight: bold;
        color: #2d3748;
        margin-bottom: 10px;
    }
    /* Badge */
    .badge {
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10px;
        font-weight: bold;
    }
    .badge-lulus {
        background: #c6f6d5;
        color: #22543d;
    }
    .badge-tidak {
        background: #fed7d7;
        color: #822727;
    }
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    try:
        with open("ppdb.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df["lintang"] = df["lintang"].astype(str).str.replace(",", ".").astype(float)
        df["bujur"] = df["bujur"].astype(str).str.replace(",", ".").astype(float)
        return df
    except Exception as e:
        st.error(f"Gagal memuat ppdb.json: {e}")
        st.stop()

df = load_data()

# Warna per sekolah (cycle 10 warna)
colors = ['#E53E3E', '#3182CE', '#38A169', '#D69E2E', '#805AD5', '#319795', '#DD6B20', '#00B5D8', '#B794F4', '#F687B3']
school_unique = df["nama_sekolah_tujuan"].unique()
school_colors = {school: colors[i % len(colors)] for i, school in enumerate(school_unique)}

# -----------------------------
# SIDEBAR FILTER
# -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">PPDB MAKASSAR</div>', unsafe_allow_html=True)

    # Tab switcher di sidebar (mirip tombol MAP / DATA)
    view_mode = st.radio(
        "Tampilan",
        options=["MAP", "DATA"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown('<div class="filter-title">JENJANG <span></span></div>', unsafe_allow_html=True)
    jenjang_all = st.button("All", key="jenjang_all", help="Pilih semua jenjang", use_container_width=False)
    jenjang_none = st.button("None", key="jenjang_none", help="Kosongkan jenjang", use_container_width=False)

    jenjang_options = sorted(df["jenjang"].dropna().unique())
    selected_jenjang = st.multiselect(
        "Pilih Jenjang",
        options=jenjang_options,
        default=jenjang_options if jenjang_all else [],
        label_visibility="collapsed",
        key="jenjang_multi"
    )

    if jenjang_all:
        selected_jenjang = jenjang_options.copy()
    if jenjang_none:
        selected_jenjang = []

    st.markdown('<div class="filter-title">JALUR <span></span></div>', unsafe_allow_html=True)
    jalur_all = st.button("All", key="jalur_all")
    jalur_none = st.button("None", key="jalur_none")

    jalur_options = sorted(df["jalur"].dropna().unique())
    selected_jalur = st.multiselect(
        "Pilih Jalur",
        options=jalur_options,
        default=jalur_options if jalur_all else [],
        label_visibility="collapsed",
        key="jalur_multi"
    )

    if jalur_all:
        selected_jalur = jalur_options.copy()
    if jalur_none:
        selected_jalur = []

# -----------------------------
# FILTER DATA
# -----------------------------
filtered_df = df[
    df["jenjang"].isin(selected_jenjang) &
    df["jalur"].isin(selected_jalur)
]

# -----------------------------
# MAIN CONTENT
# -----------------------------
st.markdown('<div class="header-bar">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Menampilkan {len(filtered_df):,} Data**")
with col2:
    st.markdown("**O** = Lulus | **X** = Tidak Lulus", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tab_map, tab_data = st.tabs(["MAP", "DATA"])

with tab_map:
    if filtered_df.empty:
        st.info("Tidak ada data yang sesuai filter.")
    else:
        # Buat map Folium
        m = folium.Map(
            location=[-5.14, 119.42],
            zoom_start=12,
            tiles="OpenStreetMap",
            prefer_canvas=True
        )

        for _, row in filtered_df.iterrows():
            lat = row["lintang"]
            lon = row["bujur"]
            sekolah = row["nama_sekolah_tujuan"]
            color = school_colors.get(sekolah, "#666666")
            status = row.get("status_penerimaan", "Tidak Lulus")
            is_lulus = status.lower() == "lulus"

            popup_html = f"""
            <b>ID:</b> {row['pendaftaran_id']}<br>
            <b>Status:</b> {status}<br>
            <b>Sekolah:</b> {sekolah}
            """

            if is_lulus:
                # O = circle outline (no fill)
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color=color,
                    weight=3,
                    fill=False,
                    opacity=0.9,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
            else:
                # X = custom cross (gunakan icon FA times)
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.Icon(
                        color="white",
                        icon_color=color,
                        icon="times",
                        prefix="fa"
                    ),
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)

        # Render map
        st_folium(m, width="100%", height=600, returned_objects=[])

with tab_data:
    if filtered_df.empty:
        st.info("Tidak ada data yang sesuai filter.")
    else:
        # Tabel dengan badge
        def badge_status(status):
            if pd.isna(status):
                status = "Tidak Lulus"
            is_lulus = status.lower() == "lulus"
            return f'<span class="badge {"badge-lulus" if is_lulus else "badge-tidak"}">{status}</span>'

        display_df = filtered_df[["jenjang", "jalur", "nama_sekolah_tujuan", "pendaftaran_id", "status_penerimaan"]].copy()
        display_df["Status"] = display_df["status_penerimaan"].apply(badge_status)

        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)