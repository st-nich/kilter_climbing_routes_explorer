
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle
from io import BytesIO

st.set_page_config(page_title="🧗 Climbing Route Explorer", layout="wide")

@st.cache_data
def load_data():
    """Load the lightweight data package"""
    with open('streamlit_data.zip', 'rb') as f:
        import zipfile
        with zipfile.ZipFile(f) as z:
            with z.open('routes.pkl') as f:
                df = pd.read_pickle(f)
            with z.open('holds.pkl') as f:
                holds_data = pickle.load(f)
            with z.open('board_geometry.pkl') as f:
                board_geometry = pickle.load(f)
    return df, holds_data, board_geometry

df, holds_data, board_geometry = load_data()

st.title("🧗 Climbing Route Explorer")

# Search box
st.subheader("🔍 Search Routes")
search_query = st.text_input("Start typing to see suggestions...", "")

# Filter controls
col1, col2 = st.columns(2)
with col1:
    min_grade, max_grade = st.slider(
        "Grade Range",
        float(df['grade'].min()),
        float(df['grade'].max()),
        (float(df['grade'].min()), float(df['grade'].max()))
    )
with col2:
    min_ascents = st.slider(
        "Minimum Ascents",
        0,
        int(df['ascents'].max()),
        0
    )

# Apply filters
df_filtered = df[
    (df['grade'] >= min_grade) &
    (df['grade'] <= max_grade) &
    (df['ascents'] >= min_ascents)
].copy()

# Search functionality
selected_route = None
if search_query:
    matches = df_filtered[df_filtered['name'].str.contains(search_query, case=False, na=False)]
    if len(matches) > 0:
        st.info(f"🎯 Selected: {matches.iloc[0]['name']} (V{matches.iloc[0]['grade']}) - highlighted in red on plot below")
        selected_route = matches.iloc[0]['uuid']

st.write(f"Showing {len(df_filtered)} of {len(df)} routes")

# Create display dataframe with colors
df_display = df_filtered.copy()
if selected_route:
    df_display['color'] = df_display['uuid'].apply(lambda x: 'red' if x == selected_route else 'gray')
    df_display['size'] = df_display['uuid'].apply(lambda x: 10 if x == selected_route else 5)
else:
    df_display['color'] = df_display['grade']
    df_display['size'] = 5

# Embedding plot with improved mobile config
if selected_route and selected_route in df_display['uuid'].values:
    fig = go.Figure()
    
    # Plot non-selected points
    df_gray = df_display[df_display['uuid'] != selected_route]
    fig.add_trace(go.Scatter(
        x=df_gray['emb_x'],
        y=df_gray['emb_y'],
        mode='markers',
        marker=dict(color='lightgray', size=5, opacity=0.5),
        hovertemplate='<b>%{customdata[0]}</b><br>Grade: %{customdata[1]}<br>Quality: %{customdata[2]:.1f}<br>Ascents: %{customdata[3]}<extra></extra>',
        customdata=df_gray[['name', 'grade', 'quality', 'ascents']].values,
        showlegend=False
    ))
    
    # Plot selected point
    df_red = df_display[df_display['uuid'] == selected_route]
    fig.add_trace(go.Scatter(
        x=df_red['emb_x'],
        y=df_red['emb_y'],
        mode='markers',
        marker=dict(color='red', size=10),
        hovertemplate='<b>%{customdata[0]}</b><br>Grade: %{customdata[1]}<br>Quality: %{customdata[2]:.1f}<br>Ascents: %{customdata[3]}<extra></extra>',
        customdata=df_red[['name', 'grade', 'quality', 'ascents']].values,
        showlegend=False
    ))
    
    fig.update_layout(
        title='Climbing Routes Embedding Space (Click a point to view route)',
        dragmode='pan',
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        height=600
    )
    
    # Minimal mobile-friendly toolbar - keep zoom, pan, and reset
    fig.update_layout(
        modebar_remove=['select', 'lasso2d', 'toImage']
    )
    
else:
    fig = px.scatter(
        df_display,
        x='emb_x',
        y='emb_y',
        color='grade',
        hover_data={'name': True, 'grade': True, 'quality': True, 'ascents': True,
                    'emb_x': False, 'emb_y': False},
        color_continuous_scale='Viridis',
        title='Climbing Routes Embedding Space (Click a point to view route)'
    )
    
    # Simplify controls for mobile - keep zoom, pan, and reset
    fig.update_layout(
        dragmode='pan',
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        height=600
    )
    
    # Minimal mobile-friendly toolbar - keep zoom, pan, and reset
    fig.update_layout(
        modebar_remove=['select', 'lasso2d', 'toImage']
    )

st.plotly_chart(fig, use_container_width=True)

# Route details
if selected_route and selected_route in holds_data:
    route_info = df_filtered[df_filtered['uuid'] == selected_route].iloc[0]
    
    # Compact single-line title
    st.markdown(f"📍 **{route_info['name']}** - Grade: V{route_info['grade']} | Quality: {route_info['quality']:.1f}★ | Ascents: {route_info['ascents']}")
    
    # Route visualization
    holds = holds_data[selected_route]
    layout_id = int(route_info['layout_id']) if pd.notna(route_info['layout_id']) else None
    
    if layout_id and layout_id in board_geometry:
        bg = board_geometry[layout_id]
        
        # Create route plot - NO TOOLBAR AT ALL
        route_fig = go.Figure()
        
        # Board holes (background)
        route_fig.add_trace(go.Scatter(
            x=bg['x'], y=bg['y'],
            mode='markers',
            marker=dict(color='lightgray', size=3, opacity=0.3),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Route holds (colored by role)
        role_colors = {
            'start': 'green',
            'hand': 'cyan', 
            'finish': 'magenta',
            'foot': 'orange'
        }
        
        for role, color in role_colors.items():
            role_mask = [r == role for r in holds['role']]
            if any(role_mask):
                role_x = [x for x, m in zip(holds['x'], role_mask) if m]
                role_y = [y for y, m in zip(holds['y'], role_mask) if m]
                route_fig.add_trace(go.Scatter(
                    x=role_x, y=role_y,
                    mode='markers',
                    marker=dict(color=color, size=12),
                    name=role.capitalize(),
                    showlegend=True
                ))
        
        route_fig.update_layout(
            title=None,
            xaxis=dict(title='X Position', scaleanchor='y'),
            yaxis=dict(title='Y Position'),
            height=400,
            showlegend=True,
            dragmode='pan'
        )
        
        # Minimal toolbar for route plot - keep zoom and reset only
        route_fig.update_layout(
            modebar_remove=['select', 'lasso2d', 'toImage']
        )
        
        st.plotly_chart(route_fig, use_container_width=True)
