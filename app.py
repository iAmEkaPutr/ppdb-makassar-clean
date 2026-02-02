import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json

# Config halaman
st.set_page_config(
    page_title="PPDB Makassar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS mirip app HTML asli
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #1a202c !important;
        color: white !important;
    }
    .sidebar .sidebar-content {
        background-color: #1a202c !important;
    }
    .filter-title {
        color: #4299e1 !important;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .small-btn {
        font-size: 10px !important;
        padding: 4px 8px !important;
        background: #4a5568 !important;
        color: white !important;
        border-radius: 3px !important;
        border: none !important;
        margin-left: 5px !important;
        cursor: pointer;
    }
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
        border-radius: 4px;
    }
    .badge {
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10px;
        font-weight: bold;
    }
    .badge-lulus { background: #c6f6d5; color: #22543d; }
    .badge-tidak { background: #fed7d7; color: #822727; }
    #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Load data
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

# Warna sekolah
colors = ['#E53E3E', '#3182CE', '#38A169', '#D69E2E', '#805AD5', 
          '#319795', '#DD6B20', '#00B5D8', '#B794F4', '#F687B3']
school_unique = df["nama_sekolah_tujuan"].dropna().unique()
school_colors = {school: colors[i % len(colors)] for i, school in enumerate(school_unique)}

# SIDEBAR
with st.sidebar:
    st.markdown('<div class="sidebar-header">PPDB MAKASSAR</div>', unsafe_allow_html=True)
    
    view_mode = st.radio(
        "Tampilan",
        options=["MAP", "DATA"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Filter JENJANG
    st.markdown('<div class="filter-title">JENJANG</div>', unsafe_allow_html=True)
    col_all, col_none = st.columns(2)
    with col_all:
        if st.button("All", key="jenjang_all", use_container_width=True):
            st.session_state["selected_jenjang"] = list(df["jenjang"].dropna().unique())
    with col_none:
        if st.button("None", key="jenjang_none", use_container_width=True):
            st.session_state["selected_jenjang"] = []
    
    jenjang_options = sorted(df["jenjang"].dropna().unique())
    selected_jenjang = st.multiselect(
        "jenjang",
        options=jenjang_options,
        default=st.session_state.get("selected_jenjang", jenjang_options),
        label_visibility="collapsed",
        key="jenjang_multi"
    )
    st.session_state["selected_jenjang"] = selected_jenjang
    
    # Filter JALUR
    st.markdown('<div class="filter-title">JALUR</div>', unsafe_allow_html=True)
    col_all_j, col_none_j = st.columns(2)
    with col_all_j:
        if st.button("All", key="jalur_all", use_container_width=True):
            st.session_state["selected_jalur"] = list(df["jalur"].dropna().unique())
    with col_none_j:
        if st.button("None", key="jalur_none", use_container_width=True):
            st.session_state["selected_jalur"] = []
    
    jalur_options = sorted(df["jalur"].dropna().unique())
    selected_jalur = st.multiselect(
        "jalur",
        options=jalur_options,
        default=st.session_state.get("selected_jalur", jalur_options),
        label_visibility="collapsed",
        key="jalur_multi"
    )
    st.session_state["selected_jalur"] = selected_jalur

# Filter data
filtered_df = df[
    (df["jenjang"].isin(selected_jenjang)) &
    (df["jalur"].isin(selected_jalur))
]

# Header bar
st.markdown(f"""
    <div class="header-bar">
        <div><strong>Map Kosong</strong> (default) – {len(filtered_df):,} data setelah filter</div>
        <div><strong>O</strong> = Lulus | <strong>X</strong> = Tidak Lulus</div>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab_map, tab_data = st.tabs(["MAP", "DATA"])

with tab_map:
    # Default: peta kosong
    m = folium.Map(
        location=[-5.14, 119.42],
        zoom_start=12,
        tiles="OpenStreetMap",
        prefer_canvas=True
    )
    
    # Hanya render marker jika ada filter yang aktif (ada data terpilih)
    if len(selected_jenjang) > 0 or len(selected_jalur) > 0:
        if filtered_df.empty:
            st.info("Tidak ada data yang sesuai dengan filter yang dipilih.")
        else:
            for _, row in filtered_df.iterrows():
                lat = row["lintang"]
                lon = row["bujur"]
                sekolah = row.get("nama_sekolah_tujuan", "-")
                color = school_colors.get(sekolah, "#666666")
                status = row.get("status_penerimaan", "Tidak Lulus")
                is_lulus = status.lower() == "lulus"
                
                popup_html = f"""
                <b>ID:</b> {row['pendaftaran_id']}<br>
                <b>Status:</b> {status}<br>
                <b>Sekolah:</b> {sekolah}
                """
                
                if is_lulus:
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
                    folium.Marker(
                        location=[lat, lon],
                        icon=folium.Icon(color="white", icon_color=color, icon="times", prefix="fa"),
                        popup=folium.Popup(popup_html, max_width=300)
                    ).add_to(m)
    
    # Tampilkan map (kosong jika belum ada filter)
    st_folium(m, width="100%", height=650, returned_objects=[])

with tab_data:
    if filtered_df.empty:
        st.info("Tidak ada data yang sesuai filter. Pilih jenjang atau jalur di sidebar.")
    else:
        def badge_status(s):
            if pd.isna(s):
                s = "Tidak Lulus"
            cls = "badge-lulus" if s.lower() == "lulus" else "badge-tidak"
            return f'<span class="badge {cls}">{s}</span>'
        
        display_df = filtered_df[["jenjang", "jalur", "nama_sekolah_tujuan", "pendaftaran_id", "status_penerimaan"]].copy()
        display_df["Status"] = display_df["status_penerimaan"].apply(badge_status)
        
        st.markdown(
            display_df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )