"""
Streamlit App for Climbing Route Explorer
Deploy to: streamlit.io (free hosting)

To run locally:
    streamlit run streamlit_app.py

To deploy:
    1. Push this file to GitHub
    2. Go to share.streamlit.io
    3. Connect your GitHub repo
    4. Deploy!
"""

import streamlit as st
import pickle
import zipfile
import numpy as np
import pandas as pd
import tempfile
import shutil
import plotly.graph_objects as go
import sqlite3

# Page config
st.set_page_config(
    page_title="🧗 Climbing Route Explorer",
    page_icon="🧗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly layout
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stPlotlyChart {
        height: 450px;
    }
    h1 {
        font-size: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(zip_path='gnn_results.zip', db_path='kilter.db'):
    """Load and process all data"""
    print(f"Loading data from {zip_path}...")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Load files
        embeddings = np.load(f'{temp_dir}/embeddings.npy')
        
        with open(f'{temp_dir}/uuids.pkl', 'rb') as f:
            uuids = pickle.load(f)
        
        meta_df = pd.read_pickle(f'{temp_dir}/meta_df.pkl')
        
        with open(f'{temp_dir}/holds_by_uuid.pkl', 'rb') as f:
            holds_by_uuid = pickle.load(f)
        
        # Filter routes
        mask = meta_df['display_difficulty'] >= 15
        embeddings = embeddings[mask]
        uuids = [u for u, m in zip(uuids, mask) if m]
        meta_df = meta_df[mask].reset_index(drop=True)
        
        # Reduce to 2D with PaCMAP
        import pacmap
        reducer = pacmap.PaCMAP(
            n_components=2,
            n_neighbors=15,
            MN_ratio=0.5,
            FP_ratio=2.0,
            random_state=42
        )
        embedding_2d = reducer.fit_transform(embeddings)
        
        # Build dataframe
        df = meta_df[meta_df['uuid'].isin(uuids)].copy().reset_index(drop=True)
        df['emb_x'] = embedding_2d[:, 0]
        df['emb_y'] = embedding_2d[:, 1]
        df['uuid'] = df['uuid'].astype(str)
        df['ascents'] = df['ascensionist_count'].fillna(0).astype(int)
        df['quality'] = df['quality_average'].fillna(0.0)
        df['grade'] = df['display_difficulty'].fillna(0.0)
        df['name'] = df['name_x'].fillna('Unnamed')
        df['setter'] = df['setter_username'].fillna('Unknown')
        
        # Load board geometry
        conn = sqlite3.connect(db_path)
        layout_ids = df['layout_id'].dropna().astype(int).unique().tolist()
        
        if layout_ids:
            ph_l = ",".join(["?"] * len(layout_ids))
            holes_df = pd.read_sql_query(
                f"""
                SELECT p.layout_id, h.x, h.y
                FROM placements p
                JOIN holes h ON p.hole_id = h.id
                WHERE p.layout_id IN ({ph_l})
                """,
                conn, params=layout_ids
            )
        else:
            holes_df = pd.DataFrame(columns=['layout_id', 'x', 'y'])
        
        bg_by_layout = {int(lid): sub[['x', 'y']].copy()
                        for lid, sub in holes_df.groupby('layout_id')}
        conn.close()
        
        return df, holds_by_uuid, bg_by_layout
        
    finally:
        shutil.rmtree(temp_dir)

# Initialize session state
if 'selected_uuid' not in st.session_state:
    st.session_state.selected_uuid = None

# Title
st.title("🧗 Climbing Route Explorer")

# Load data
try:
    df, holds_by_uuid, bg_by_layout = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    
    # Search
    search_query = st.text_input("Search route name", "")
    
    # Grade range
    grade_range = st.slider(
        "Grade Range",
        float(df['grade'].min()),
        float(df['grade'].max()),
        (float(df['grade'].min()), float(df['grade'].max())),
        step=0.1,
        format="V%.1f"
    )
    
    # Ascent range
    ascent_range = st.slider(
        "Ascent Range",
        int(df['ascents'].min()),
        int(df['ascents'].max()),
        (int(df['ascents'].min()), int(df['ascents'].max())),
        step=1
    )

# Apply filters
filtered_df = df[
    (df['grade'] >= grade_range[0]) &
    (df['grade'] <= grade_range[1]) &
    (df['ascents'] >= ascent_range[0]) &
    (df['ascents'] <= ascent_range[1])
]

# Apply search
if search_query:
    filtered_df = filtered_df[
        filtered_df['name'].str.contains(search_query, case=False, na=False)
    ]

st.write(f"Showing {len(filtered_df)} of {len(df)} routes")

# Create embedding plot
fig_embed = go.Figure()

# Determine colors and sizes based on selection
if st.session_state.selected_uuid:
    colors = ['red' if uuid == st.session_state.selected_uuid else grade 
              for uuid, grade in zip(filtered_df['uuid'], filtered_df['grade'])]
    sizes = [12 if uuid == st.session_state.selected_uuid else 5 
             for uuid in filtered_df['uuid']]
    showscale = False
else:
    colors = filtered_df['grade']
    sizes = 5
    showscale = True

fig_embed.add_trace(go.Scattergl(
    x=filtered_df['emb_x'],
    y=filtered_df['emb_y'],
    mode="markers",
    marker=dict(
        size=sizes,
        color=colors,
        colorscale="Viridis" if not st.session_state.selected_uuid else None,
        line=dict(width=0.3, color="black"),
        showscale=showscale,
        colorbar=dict(title="Grade") if showscale else None
    ),
    text=(filtered_df['name'] + "<br>V" + filtered_df['grade'].round(1).astype(str) +
          " | ★" + filtered_df['quality'].round(2).astype(str) +
          "<br>" + filtered_df['setter']),
    customdata=filtered_df['uuid'],
    hovertemplate="%{text}<extra></extra>",
))

fig_embed.update_layout(
    title="Climbing Routes Embedding Space (Click a point to view route)",
    xaxis=dict(title="Dimension 1"),
    yaxis=dict(title="Dimension 2"),
    height=450,
    template="plotly_white",
    hovermode='closest'
)

# Display embedding plot and capture clicks
selected_point = st.plotly_chart(fig_embed, use_container_width=True, 
                                  key="embed_plot", 
                                  on_select="rerun")

# Handle point selection
if selected_point and 'selection' in selected_point:
    if 'points' in selected_point['selection'] and len(selected_point['selection']['points']) > 0:
        point_idx = selected_point['selection']['points'][0]['point_index']
        st.session_state.selected_uuid = filtered_df.iloc[point_idx]['uuid']

# Display route visualization if selected
if st.session_state.selected_uuid:
    route = df[df['uuid'] == st.session_state.selected_uuid].iloc[0]
    
    st.markdown("---")
    st.subheader(f"📍 {route['name']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Grade", f"V{route['grade']:.1f}")
    col2.metric("Quality", f"{route['quality']:.1f}★")
    col3.metric("Ascents", f"{route['ascents']}")
    
    # Create route visualization
    fig_route = go.Figure()
    
    ROLE_NAME = {12: "Start", 13: "Hand", 14: "Finish", 15: "Foot"}
    ROLE_COLOR = {12: "#00FF00", 13: "#00FFFF", 14: "#FF00FF", 15: "#FFA500"}
    ROLE_SIZE = {12: 14, 13: 10, 14: 14, 15: 10}
    
    # Add board background
    layout_id = int(route['layout_id'])
    if layout_id in bg_by_layout:
        bg = bg_by_layout[layout_id]
        fig_route.add_trace(go.Scattergl(
            x=bg['x'],
            y=bg['y'],
            mode="markers",
            marker=dict(size=3, opacity=0.15, color="lightgray"),
            hoverinfo="skip",
            showlegend=False,
            name="Board"
        ))
    
    # Add holds
    holds = holds_by_uuid.get(st.session_state.selected_uuid)
    if holds is not None:
        valid_holds = holds.dropna(subset=['x', 'y'])
        
        for role_id in [12, 13, 14, 15]:
            role_holds = valid_holds[valid_holds['role'] == role_id]
            if not role_holds.empty:
                fig_route.add_trace(go.Scattergl(
                    x=role_holds['x'],
                    y=role_holds['y'],
                    mode="markers",
                    name=ROLE_NAME[role_id],
                    marker=dict(
                        size=ROLE_SIZE[role_id],
                        color=ROLE_COLOR[role_id],
                        line=dict(width=1.5, color="black")
                    ),
                    hovertemplate="(%{x:.1f}, %{y:.1f})<extra></extra>"
                ))
    
    fig_route.update_layout(
        title=f"{route['name']} - V{route['grade']:.1f}",
        xaxis=dict(
            title="X Position",
            range=[-20, 150],
            scaleanchor="y",
            scaleratio=1
        ),
        yaxis=dict(
            title="Y Position",
            range=[0, 200]
        ),
        height=450,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig_route, use_container_width=True)
    
    if st.button("Clear Selection"):
        st.session_state.selected_uuid = None
        st.rerun()
