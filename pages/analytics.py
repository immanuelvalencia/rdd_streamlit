import streamlit as st
import plotly.express as px
import database as db

st.title("📊 Analytics")
st.markdown("Overview of all road damage detection projects.")

try:
    analytics_df = db.get_all_analytics()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

if analytics_df.empty or analytics_df['project_id'].isna().all():
    st.warning("No data available for analytics. Create projects and upload media first.")
    st.stop()

projects_df = db.get_projects()

# --- Filters ---
st.subheader("Filters")
proj_options = projects_df['name'].tolist()
selected_filters = st.multiselect("Filter by Projects:", proj_options, default=None, placeholder="Select projects to filter, or leave blank for all")

if selected_filters:
    filtered_df = analytics_df[analytics_df['project_name'].isin(selected_filters)]
else:
    filtered_df = analytics_df

# --- Compute Top-Level Metrics ---
total_projects = filtered_df['project_id'].nunique()
total_media = filtered_df['media_id'].nunique()

detections_df = filtered_df.dropna(subset=['damage_type'])
total_damages = len(detections_df)
avg_confidence = detections_df['confidence'].mean() if total_damages > 0 else 0.0

st.divider()

# --- Top Level Metrics UI ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.metric("Total Projects", total_projects)
with col2:
    with st.container(border=True):
        st.metric("Total Media", total_media)
with col3:
    with st.container(border=True):
        st.metric("Total Damages", total_damages)
with col4:
    with st.container(border=True):
        st.metric("Avg Confidence", f"{avg_confidence*100:.1f}%" if total_damages > 0 else "N/A")

st.divider()

# --- Visualizations ---
if total_damages > 0:
    chart_col1, chart_col2 = st.columns(2, gap="large")
    
    with chart_col1:
        st.subheader("Damages by Type")
        damage_counts = detections_df['damage_type'].value_counts().reset_index()
        damage_counts.columns = ['Damage Type', 'Count']
        
        # Plotly Donut Chart
        fig_donut = px.pie(
            damage_counts, 
            values='Count', 
            names='Damage Type', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig_donut, width="stretch")

    with chart_col2:
        st.subheader("Damages per Project")
        project_damage_counts = detections_df.groupby('project_name').size().reset_index(name='Total Damages')
        
        # Plotly Bar Chart
        fig_bar = px.bar(
            project_damage_counts, 
            x='project_name', 
            y='Total Damages',
            color='project_name',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False, xaxis_title=None)
        st.plotly_chart(fig_bar, width="stretch")
else:
    st.info("No damages detected in the selected projects.")
