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
from pathlib import Path

# ============================================================================
# FILE CONFIGURATION - Update these paths to match your setup
# ============================================================================
# For local development, update these paths:
ZIP_PATH = 'gnn_results.zip'  # Change to '/path/to/your/gnn_results.zip'
DB_PATH = 'kilter.db'          # Change to '/path/to/your/kilter.db'

# Or if using Google Drive paths:
# ZIP_PATH = '/content/drive/MyDrive/climbs/gnn_results.zip'
# DB_PATH = '/content/drive/MyDrive/climbs/kilter.db'
# ============================================================================

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
    /* Style search result buttons */
    div[data-testid="column"] button {
        height: auto;
        white-space: pre-wrap;
        padding: 0.75rem;
        font-size: 0.9rem;
    }
    /* Make buttons look like cards */
    div[data-testid="column"] button:hover {
        border-color: #4CAF50;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(data_path='streamlit_data.zip'):
    """Load pre-processed lightweight data package"""
    import os
    
    # Check if file exists
    if not os.path.exists(data_path):
        st.error(f"❌ Cannot find {data_path}")
        st.info("""
        Please upload streamlit_data.zip to your GitHub repository.
        
        To create this file:
        1. Run prepare_streamlit_data.py in your Colab
        2. Download the generated streamlit_data.zip
        3. Upload it to your GitHub repo
        """)
        st.stop()
    
    print(f"Loading data from {data_path}...")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract ZIP
        with zipfile.ZipFile(data_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Load pre-processed data
        df = pd.read_pickle(f'{temp_dir}/routes.pkl')
        
        with open(f'{temp_dir}/holds.pkl', 'rb') as f:
            holds_by_uuid = pickle.load(f)
        
        with open(f'{temp_dir}/board_geometry.pkl', 'rb') as f:
            bg_by_layout = pickle.load(f)
        
        print(f"✓ Loaded {len(df)} routes successfully!")
        
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

# Search bar in main area (more prominent)
st.markdown("### 🔍 Search Routes")
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input(
        "Type route name to filter", 
        "", 
        placeholder="Start typing to see suggestions...",
        label_visibility="collapsed"
    )
with col2:
    if st.button("Clear All", use_container_width=True):
        st.session_state.selected_uuid = None
        st.rerun()

# Show matching routes as clickable options if searching
if search_query and len(search_query) >= 2:
    matches = df[df['name'].str.contains(search_query, case=False, na=False)].head(20)
    if len(matches) > 0:
        st.success(f"✅ {len(matches)} matches found")
        
        # Create clickable buttons for each match
        cols_per_row = 2  # Two columns for mobile
        for i in range(0, len(matches), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (idx, row) in enumerate(matches.iloc[i:i+cols_per_row].iterrows()):
                with cols[j]:
                    button_label = f"🧗 {row['name']}\nV{row['grade']:.1f} | ★{row['quality']:.1f}"
                    if st.button(
                        button_label,
                        key=f"match_{row['uuid']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_uuid = row['uuid']
                        st.rerun()
        
        st.divider()
    else:
        st.info("No routes found matching your search")

# Sidebar filters
with st.sidebar:
    st.header("📊 Filters")
    
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

# Apply filters (grade and ascents only - NOT search)
filtered_df = df[
    (df['grade'] >= grade_range[0]) &
    (df['grade'] <= grade_range[1]) &
    (df['ascents'] >= ascent_range[0]) &
    (df['ascents'] <= ascent_range[1])
]

st.write(f"Showing {len(filtered_df)} of {len(df)} routes")

# Show selected route info if one is selected
if st.session_state.selected_uuid:
    selected_route = df[df['uuid'] == st.session_state.selected_uuid]
    if not selected_route.empty:
        route = selected_route.iloc[0]
        st.info(f"🎯 **Selected:** {route['name']} (V{route['grade']:.1f}) - highlighted in red on plot below")

st.divider()

# Create embedding plot
fig_embed = go.Figure()

# Determine colors and sizes based on selection
if st.session_state.selected_uuid:
    colors = ['red' if uuid == st.session_state.selected_uuid else 'lightgray'
              for uuid in filtered_df['uuid']]
    sizes = [15 if uuid == st.session_state.selected_uuid else 5 
             for uuid in filtered_df['uuid']]
    showscale = False
    colorscale = None
else:
    colors = filtered_df['grade']
    sizes = 5
    showscale = True
    colorscale = "Viridis"

fig_embed.add_trace(go.Scattergl(
    x=filtered_df['emb_x'],
    y=filtered_df['emb_y'],
    mode="markers",
    marker=dict(
        size=sizes,
        color=colors,
        colorscale=colorscale,
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

# Simplify toolbar - keep essential zoom/pan tools
fig_embed.update_layout(
    modebar_remove=['select', 'lasso2d']
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
    st.markdown(f"### 📍 {route['name']} - V{route['grade']:.1f} | ★{route['quality']:.1f} | {route['ascents']} ascents")
    
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
        # holds is now a dict with 'x', 'y', 'role' lists
        for role_id in [12, 13, 14, 15]:
            # Find indices where role matches
            role_indices = [i for i, r in enumerate(holds['role']) if r == role_id]
            if role_indices:
                role_x = [holds['x'][i] for i in role_indices]
                role_y = [holds['y'][i] for i in role_indices]
                
                fig_route.add_trace(go.Scattergl(
                    x=role_x,
                    y=role_y,
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
    
    # Remove all toolbar controls from route plot
    fig_route.update_layout(
        modebar_remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 
                       'autoScale2d', 'resetScale2d', 'toImage', 'zoom2d']
    )
    
    st.plotly_chart(fig_route, use_container_width=True)
    
    if st.button("Clear Selection"):
        st.session_state.selected_uuid = None
        st.rerun()
