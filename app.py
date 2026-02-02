import streamlit as st
import json
import pandas as pd
import os

# Config halaman
st.set_page_config(page_title="PPDB Makassar", layout="wide", initial_sidebar_state="expanded")

# CSS mirip app HTML lama
st.markdown("""
<style>
    section[data-testid="stSidebar"] { background-color: #1a202c !important; color: white !important; }
    .sidebar .sidebar-content { background-color: #1a202c !important; }
    .filter-title { color: #4299e1 !important; font-weight: bold; font-size: 13px; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .header-bar { padding: 12px 25px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: bold; color: #2d3748; margin-bottom: 10px; }
    .badge { padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; }
    .badge-lulus { background: #c6f6d5; color: #22543d; }
    .badge-tidak { background: #fed7d7; color: #822727; }
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    json_path = "ppdb.json"
    if not os.path.exists(json_path):
        st.error("File ppdb.json tidak ditemukan di root repo. Commit & push ulang.")
        st.stop()
    try:
        df = pd.read_json(json_path)
        df["lintang"] = pd.to_numeric(df["lintang"].astype(str).str.replace(",", "."), errors='coerce')
        df["bujur"] = pd.to_numeric(df["bujur"].astype(str).str.replace(",", "."), errors='coerce')
        df = df.dropna(subset=["lintang", "bujur"])
        return df
    except Exception as e:
        st.error(f"Error baca JSON: {e}")
        st.stop()

df = load_data()

# Warna sekolah
colors = ['#E53E3E', '#3182CE', '#38A169', '#D69E2E', '#805AD5', '#319795', '#DD6B20', '#00B5D8', '#B794F4', '#F687B3']
school_unique = df["nama_sekolah_tujuan"].unique()
school_colors = {s: colors[i % len(colors)] for i, s in enumerate(school_unique)}

# Sidebar filter
with st.sidebar:
    st.markdown('<div class="sidebar-header">PPDB MAKASSAR</div>', unsafe_allow_html=True)
    
    view_mode = st.radio("Tampilan", ["MAP", "DATA"], horizontal=True, label_visibility="collapsed")
    
    st.markdown('<div class="filter-title">JENJANG</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("All", key="jenjang_all_btn", use_container_width=True):
            st.session_state.jenjang = list(df["jenjang"].dropna().unique())
    with col2:
        if st.button("None", key="jenjang_none_btn", use_container_width=True):
            st.session_state.jenjang = []
    
    jenjang_opts = sorted(df["jenjang"].dropna().unique())
    selected_jenjang = st.multiselect("jenjang", jenjang_opts, default=st.session_state.get("jenjang", []), label_visibility="collapsed", key="jenjang_select")
    st.session_state.jenjang = selected_jenjang
    
    st.markdown('<div class="filter-title">JALUR</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("All", key="jalur_all_btn", use_container_width=True):
            st.session_state.jalur = list(df["jalur"].dropna().unique())
    with col2:
        if st.button("None", key="jalur_none_btn", use_container_width=True):
            st.session_state.jalur = []
    
    jalur_opts = sorted(df["jalur"].dropna().unique())
    selected_jalur = st.multiselect("jalur", jalur_opts, default=st.session_state.get("jalur", []), label_visibility="collapsed", key="jalur_select")
    st.session_state.jalur = selected_jalur

# Filter data
filtered = df[df["jenjang"].isin(selected_jenjang) & df["jalur"].isin(selected_jalur)]

# Header bar
st.markdown(f"""
<div class="header-bar">
    <div><strong>Map Kosong</strong> – {len(filtered):,} data setelah filter</div>
    <div><strong>O</strong> = Lulus | <strong>X</strong> = Tidak Lulus</div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_map, tab_data = st.tabs(["MAP", "DATA"])

with tab_map:
    if len(selected_jenjang) == 0 and len(selected_jalur) == 0:
        st.info("Pilih jenjang atau jalur di sidebar untuk menampilkan data di peta.")
    elif filtered.empty:
        st.info("Tidak ada data yang cocok dengan filter.")
    else:
        # Siapkan data untuk JS
        data_points = []
        for _, row in filtered.iterrows():
            data_points.append({
                "lat": row["lintang"],
                "lon": row["bujur"],
                "id": row["pendaftaran_id"],
                "status": row.get("status_penerimaan", "Tidak Lulus"),
                "sekolah": row["nama_sekolah_tujuan"],
                "color": school_colors.get(row["nama_sekolah_tujuan"], "#666666"),
                "lulus": row.get("status_penerimaan", "").lower() == "lulus"
            })
        
        # Embed Leaflet JS + MarkerCluster (ringan & cepat)
        html_map = f"""
        <div id="map" style="height: 650px; width: 100%;"></div>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
        
        <script>
        const map = L.map('map', {{preferCanvas: true}}).setView([-5.14, 119.42], 12);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        
        const markers = L.markerClusterGroup({{maxClusterRadius: 40, disableClusteringAtZoom: 15}});
        map.addLayer(markers);
        
        const data = {json.dumps(data_points)};
        
        data.forEach(p => {{
            let marker;
            if (p.lulus) {{
                marker = L.circleMarker([p.lat, p.lon], {{
                    radius: 6,
                    color: p.color,
                    weight: 3,
                    fillOpacity: 0,
                    opacity: 0.9
                }});
            }} else {{
                marker = L.circleMarker([p.lat, p.lon], {{
                    radius: 6,
                    color: p.color,
                    weight: 4,
                    fillOpacity: 0,
                    opacity: 0.9
                }});
                marker.bindTooltip('X', {{permanent: true, direction: 'center', className: 'cross-tooltip'}});
            }}
            
            marker.bindPopup(`<b>ID:</b> ${{p.id}}<br><b>Status:</b> ${{p.status}}<br><b>Sekolah:</b> ${{p.sekolah}}`);
            markers.addLayer(marker);
        }});
        
        // Custom CSS untuk X tooltip
        const style = document.createElement('style');
        style.innerHTML = '.cross-tooltip {{ font-size: 18px; font-weight: bold; color: inherit; background: transparent; border: none; box-shadow: none; }}';
        document.head.appendChild(style);
        </script>
        """
        
        st.components.v1.html(html_map, height=650)

with tab_data:
    if filtered.empty:
        st.info("Tidak ada data. Pilih filter di sidebar.")
    else:
        def badge(s):
            s = s or "Tidak Lulus"
            cls = "badge-lulus" if s.lower() == "lulus" else "badge-tidak"
            return f'<span class="badge {cls}">{s}</span>'
        
        df_show = filtered[["jenjang", "jalur", "nama_sekolah_tujuan", "pendaftaran_id", "status_penerimaan"]].copy()
        df_show["Status"] = df_show["status_penerimaan"].apply(badge)
        st.markdown(df_show.to_html(escape=False, index=False), unsafe_allow_html=True)