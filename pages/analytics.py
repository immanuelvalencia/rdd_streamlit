import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database as db

st.title("📊 Analytics Dashboard")
st.markdown("Real-time overview of all road damage detection projects.")

# ── Data Load ─────────────────────────────────────────────────────────────────
try:
    analytics_df = db.get_all_analytics()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

if analytics_df.empty or analytics_df['project_id'].isna().all():
    st.warning("No data available. Create projects and upload media first.")
    st.stop()

projects_df = db.get_projects()

# ── Filters ──────────────────────────────────────────────────────────────────
with st.expander("🔽 Filters", expanded=True):
    f1, f2, f3 = st.columns(3)

    with f1:
        proj_options = sorted(analytics_df['project_name'].dropna().unique().tolist())
        sel_projects = st.multiselect(
            "Project", proj_options,
            placeholder="All projects"
        )

    with f2:
        region_options = sorted(analytics_df['region'].dropna().unique().tolist()) if 'region' in analytics_df.columns else []
        sel_regions = st.multiselect(
            "Region", region_options,
            placeholder="All regions"
        )

    with f3:
        dtype_options = sorted(analytics_df['damage_type'].dropna().unique().tolist())
        sel_damages = st.multiselect(
            "Damage Type", dtype_options,
            placeholder="All damage types"
        )

# Apply filters
filtered_df = analytics_df.copy()
if sel_projects:
    filtered_df = filtered_df[filtered_df['project_name'].isin(sel_projects)]
if sel_regions:
    filtered_df = filtered_df[filtered_df['region'].isin(sel_regions)]
if sel_damages:
    filtered_df = filtered_df[filtered_df['damage_type'].isin(sel_damages)]

st.divider()

# ── Metrics ──────────────────────────────────────────────────────────────────
total_projects = filtered_df['project_id'].nunique()
total_media    = filtered_df['media_id'].nunique()
detections_df  = filtered_df.dropna(subset=['damage_type'])
total_damages  = len(detections_df)
density        = (total_damages / total_media) if total_media > 0 else 0.0

m1, m2, m3, m4 = st.columns(4)
with m1:
    with st.container(border=True):
        st.metric("Total Projects", total_projects)
with m2:
    with st.container(border=True):
        st.metric("Images Analyzed", total_media)
with m3:
    with st.container(border=True):
        st.metric("Total Distresses", total_damages)
with m4:
    with st.container(border=True):
        st.metric("Distress Density", f"{density:.1f} per img")

st.divider()

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader("🗺️ Damage Location Map")

# Build per-project summary for pins (need at least lat/lon)
map_df = (
    filtered_df
    .dropna(subset=['latitude', 'longitude'])
    .groupby(
        ['project_id', 'project_name', 'latitude', 'longitude', 'city', 'region', 'street'],
        dropna=False
    )
    .agg(
        total_images=('media_id', 'nunique'),
        total_detections=('damage_type', 'count'),
    )
    .reset_index()
)

# Build damage breakdown per project for hover text
damage_breakdown = (
    filtered_df.dropna(subset=['damage_type', 'latitude', 'longitude'])
    .groupby(['project_id', 'damage_type'])
    .size()
    .reset_index(name='count')
)

def build_hover(proj_id):
    sub = damage_breakdown[damage_breakdown['project_id'] == proj_id]
    if sub.empty:
        return "No detections"
    lines = [f"  • {row['damage_type']}: {row['count']}" for _, row in sub.iterrows()]
    return "<br>".join(lines)

if not map_df.empty:
    map_df['damage_breakdown'] = map_df['project_id'].apply(build_hover)
    map_df['location'] = map_df.apply(
        lambda r: ", ".join(filter(None, [r.get('street', ''), r.get('city', ''), r.get('region', '')])),
        axis=1
    )

    map_df['hover_text'] = map_df.apply(
        lambda r: (
            f"<b>{r['project_name']}</b><br>"
            f"📍 {r['location']}<br>"
            f"🖼️ Images: {r['total_images']}<br>"
            f"⚠️ Detections: {r['total_detections']}<br>"
            f"<br><b>Damage Breakdown:</b><br>{r['damage_breakdown']}"
        ),
        axis=1
    )

    # Scale pin size by total detections, min 12
    map_df['marker_size'] = (map_df['total_detections'].clip(lower=1) * 1.5 + 12).clip(upper=40)

    fig_map = go.Figure()

    fig_map.add_trace(go.Scattermap(
        lat=map_df['latitude'],
        lon=map_df['longitude'],
        mode='markers',
        marker=go.scattermap.Marker(
            size=map_df['marker_size'],
            color=map_df['total_detections'],
            colorscale='YlOrRd',
            colorbar=dict(title="Detections", thickness=12),
            opacity=0.85,
        ),
        text=map_df['hover_text'],
        hovertemplate="%{text}<extra></extra>",
        name="Projects",
    ))

    # Auto-center on the data
    center_lat = map_df['latitude'].mean()
    center_lon = map_df['longitude'].mean()

    fig_map.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=10,
        ),
        height=520,
        margin=dict(t=0, b=0, l=0, r=0),
        hoverlabel=dict(
            bgcolor="#1e1e2e",
            bordercolor="#6c6c8a",
            font=dict(color="white", size=13),
        ),
    )

    map_event = st.plotly_chart(fig_map, width="stretch", on_select="rerun", selection_mode="points")

    # Handle pin click navigation
    if map_event and "selection" in map_event and map_event["selection"]["points"]:
        point = map_event["selection"]["points"][0]
        point_idx = point.get("point_index")
        if point_idx is not None and point_idx < len(map_df):
            target_proj_id = map_df.iloc[point_idx]['project_id']
            # Store in query params and session state for the project details page
            st.query_params["id"] = target_proj_id
            st.session_state.target_project = target_proj_id
            st.switch_page("pages/project_details.py")
else:
    st.info("No projects with coordinates found. Add latitude/longitude to your projects to see pins on the map.")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
if total_damages > 0:
    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        st.subheader("Distress Classification")
        damage_counts = detections_df['damage_type'].value_counts().reset_index()
        damage_counts.columns = ['Distress Type', 'Count']

        fig_donut = px.pie(
            damage_counts,
            values='Count',
            names='Distress Type',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, width="stretch")

    with chart_col2:
        st.subheader("Distresses per Project")
        project_damage_counts = (
            detections_df.groupby('project_name').size().reset_index(name='Total Distresses')
        )
        fig_bar = px.bar(
            project_damage_counts,
            x='project_name',
            y='Total Distresses',
            color='project_name',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_bar.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False,
            xaxis_title=None
        )
        st.plotly_chart(fig_bar, width="stretch")

    # ── Damage breakdown table per project ────────────────────────────────────
    st.subheader("Damage Breakdown by Project")
    breakdown_tbl = (
        detections_df.groupby(['project_name', 'damage_type'])
        .size()
        .reset_index(name='Count')
        .pivot_table(index='project_name', columns='damage_type', values='Count', fill_value=0)
        .reset_index()
        .rename(columns={'project_name': 'Project'})
    )
    st.dataframe(breakdown_tbl, width="stretch", hide_index=True)

else:
    st.info("No distresses detected in the selected projects.")
