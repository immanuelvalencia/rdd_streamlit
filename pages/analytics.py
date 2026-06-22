import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database as db
import datetime
import tempfile
import os
from fpdf import FPDF

@st.cache_data
def convert_df_to_csv(df):
    export_df = df.copy()
    rename_dict = {
        "project_name": "Project Name",
        "street": "Street",
        "city": "City",
        "province": "Province",
        "region": "Region",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "status": "Processing Status",
        "damage_type": "Damage Type",
        "confidence": "Detection Confidence"
    }
    export_df = export_df.rename(columns=rename_dict)
    desired_cols = [
        "Project Name", "Street", "City", "Province", "Region", 
        "Latitude", "Longitude", "Processing Status", "Damage Type", "Detection Confidence"
    ]
    existing_cols = [c for c in desired_cols if c in export_df.columns]
    export_df = export_df[existing_cols]
    return export_df.to_csv(index=False).encode('utf-8')

@st.cache_data
def convert_breakdown_to_csv(df):
    if df.empty or "damage_type" not in df.columns:
        return b""
    breakdown_tbl = (
        df.groupby(["project_name", "damage_type"])
        .size()
        .reset_index(name="Count")
        .pivot_table(
            index="project_name", columns="damage_type", values="Count", fill_value=0
        )
        .reset_index()
        .rename(columns={"project_name": "Project"})
    )
    return breakdown_tbl.to_csv(index=False).encode('utf-8')

def generate_pdf_report(total_projects, total_media, total_damages, density, fig_map, fig_donut, fig_bar, breakdown_tbl):
    temp_dir = tempfile.gettempdir()
    map_path = os.path.join(temp_dir, "temp_map.png")
    donut_path = os.path.join(temp_dir, "temp_donut.png")
    bar_path = os.path.join(temp_dir, "temp_bar.png")
    
    has_map = False
    has_donut = False
    has_bar = False
    
    try:
        if fig_map is not None:
            fig_map.write_image(map_path, format="png", width=800, height=450, scale=2)
            has_map = True
    except Exception:
        pass
        
    try:
        if fig_donut is not None:
            fig_donut.write_image(donut_path, format="png", width=600, height=400, scale=2)
            has_donut = True
    except Exception:
        pass
        
    try:
        if fig_bar is not None:
            fig_bar.write_image(bar_path, format="png", width=600, height=400, scale=2)
            has_bar = True
    except Exception:
        pass
        
    class PDFReport(FPDF):
        def header(self):
            # Maroon brand banner
            self.set_fill_color(128, 0, 0)
            self.rect(0, 0, 210, 25, "F")
            
            # White text
            self.set_text_color(255, 255, 255)
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "Road Damage Detection Dashboard Report", ln=1, align="L")
            self.set_font("Arial", "I", 8)
            self.cell(0, 5, f"Generated on {datetime.date.today().strftime('%B %d, %Y')}", ln=1, align="L")
            self.ln(10)
            
        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()} | Confidential - For Internal Use Only", align="C")
            
    pdf = PDFReport(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_text_color(49, 51, 63)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "Executive Analytics Summary", ln=1)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, 45, 200, 45)
    pdf.ln(5)
    
    # Metrics
    pdf.set_fill_color(240, 242, 246)
    pdf.rect(10, 48, 190, 24, "F")
    
    pdf.set_y(50)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(47.5, 6, "Total Projects", align="C")
    pdf.cell(47.5, 6, "Images Analyzed", align="C")
    pdf.cell(47.5, 6, "Total Distresses", align="C")
    pdf.cell(47.5, 6, "Distress Density", align="C", ln=1)
    
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(128, 0, 0)
    pdf.cell(47.5, 8, str(total_projects), align="C")
    pdf.cell(47.5, 8, str(total_media), align="C")
    pdf.cell(47.5, 8, str(total_damages), align="C")
    pdf.cell(47.5, 8, f"{density:.1f}/img", align="C", ln=1)
    
    pdf.set_text_color(49, 51, 63)
    pdf.ln(10)
    
    # Map
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Damage Location Map", ln=1)
    pdf.ln(2)
    if has_map:
        pdf.image(map_path, x=15, y=pdf.get_y(), w=180, h=100)
        pdf.ln(108)
    else:
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(15, pdf.get_y(), 180, 50, "F")
        pdf.set_y(pdf.get_y() + 15)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "Map visualization is not available in static format.", align="C", ln=1)
        pdf.set_y(pdf.get_y() + 35)
        
    # Charts
    if has_donut or has_bar:
        if pdf.get_y() > 150:
            pdf.add_page()
            
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Distress Charts & Visualizations", ln=1)
        pdf.ln(2)
        
        y_pos = pdf.get_y()
        if has_donut:
            pdf.image(donut_path, x=10, y=y_pos, w=90, h=60)
        if has_bar:
            pdf.image(bar_path, x=110, y=y_pos, w=90, h=60)
        pdf.ln(70)
        
    # Breakdown Table
    if breakdown_tbl is not None and not breakdown_tbl.empty:
        if pdf.get_y() > 180:
            pdf.add_page()
            
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Damage Breakdown by Project", ln=1)
        pdf.ln(4)
        
        cols = list(breakdown_tbl.columns)
        num_cols = len(cols)
        page_width = 190
        proj_col_width = 50
        other_col_width = (page_width - proj_col_width) / max(1, (num_cols - 1))
        
        # Header
        pdf.set_fill_color(128, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 9)
        for i, col in enumerate(cols):
            w = proj_col_width if i == 0 else other_col_width
            pdf.cell(w, 7, str(col), border=1, align="C" if i > 0 else "L", fill=True)
        pdf.ln()
        
        # Body
        pdf.set_text_color(49, 51, 63)
        pdf.set_font("Arial", "", 8.5)
        fill = False
        for _, row in breakdown_tbl.iterrows():
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            for i, col in enumerate(cols):
                val = row[col]
                w = proj_col_width if i == 0 else other_col_width
                pdf.cell(w, 6, str(val), border=1, align="C" if i > 0 else "L", fill=True)
            pdf.ln()
            fill = not fill
            
    for path in [map_path, donut_path, bar_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
            
    return pdf.output(dest='S').encode('latin-1')

st.title("📊 Analytics Dashboard")
st.markdown("Real-time overview of all road damage detection projects.")

# ── Data Load ─────────────────────────────────────────────────────────────────
try:
    analytics_df = db.get_all_analytics()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

if analytics_df.empty or analytics_df["project_id"].isna().all():
    st.warning("No data available. Create projects and upload media first.")
    st.stop()

projects_df = db.get_projects()

# ── Filters ──────────────────────────────────────────────────────────────────
with st.expander("🔽 Filters", expanded=True):
    f_proj, f_dmg = st.columns(2)
    with f_proj:
        proj_options = sorted(analytics_df["project_name"].dropna().unique().tolist())
        sel_projects = st.multiselect(
            "Project", proj_options, placeholder="All projects"
        )
    with f_dmg:
        dtype_options = sorted(analytics_df["damage_type"].dropna().unique().tolist())
        sel_damages = st.multiselect(
            "Damage Type", dtype_options, placeholder="All damage types"
        )

    f_reg, f_prov, f_city = st.columns(3)
    with f_reg:
        region_options = sorted(analytics_df["region"].dropna().unique().tolist()) if "region" in analytics_df.columns else []
        sel_regions = st.multiselect(
            "Region", region_options, placeholder="All regions"
        )
    with f_prov:
        if sel_regions:
            prov_options = []
            for r in sel_regions:
                if r in db.PHILIPPINES_LOCATIONS:
                    prov_options.extend(db.PHILIPPINES_LOCATIONS[r].keys())
            prov_options = sorted(list(set(prov_options)))
        else:
            prov_options = sorted(analytics_df["province"].dropna().unique().tolist()) if "province" in analytics_df.columns else []
        
        sel_provinces = st.multiselect(
            "Province", prov_options, placeholder="All provinces"
        )
    with f_city:
        if sel_provinces:
            city_options = []
            for r in (sel_regions or db.PHILIPPINES_LOCATIONS.keys()):
                if r in db.PHILIPPINES_LOCATIONS:
                    for p in sel_provinces:
                        if p in db.PHILIPPINES_LOCATIONS[r]:
                            city_options.extend(db.PHILIPPINES_LOCATIONS[r][p])
            city_options = sorted(list(set(city_options)))
        elif sel_regions:
            city_options = []
            for r in sel_regions:
                if r in db.PHILIPPINES_LOCATIONS:
                    for p in db.PHILIPPINES_LOCATIONS[r]:
                        city_options.extend(db.PHILIPPINES_LOCATIONS[r][p])
            city_options = sorted(list(set(city_options)))
        else:
            city_options = sorted(analytics_df["city"].dropna().unique().tolist()) if "city" in analytics_df.columns else []

        sel_cities = st.multiselect(
            "City / Municipality", city_options, placeholder="All cities/municipalities"
        )

# Apply filters
filtered_df = analytics_df.copy()
if sel_projects:
    filtered_df = filtered_df[filtered_df["project_name"].isin(sel_projects)]
if sel_regions:
    filtered_df = filtered_df[filtered_df["region"].isin(sel_regions)]
if sel_provinces:
    filtered_df = filtered_df[filtered_df["province"].isin(sel_provinces)]
if sel_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(sel_cities)]
if sel_damages:
    filtered_df = filtered_df[filtered_df["damage_type"].isin(sel_damages)]

# Calculate metrics for export and display
total_projects = filtered_df["project_id"].nunique()
total_media = filtered_df["media_id"].nunique()
detections_df = filtered_df.dropna(subset=["damage_type"])
total_damages = len(detections_df)
density = (total_damages / total_media) if total_media > 0 else 0.0

# ── Prep Map Data & Figure (Early Instantiation) ──────────────────────────────
map_df = (
    filtered_df.dropna(subset=["latitude", "longitude"])
    .groupby(
        [
            "project_id",
            "project_name",
            "latitude",
            "longitude",
            "city",
            "province",
            "region",
            "street",
        ],
        dropna=False,
    )
    .agg(
        total_images=("media_id", "nunique"),
        total_detections=("damage_type", "count"),
    )
    .reset_index()
)

fig_map = None
if not map_df.empty:
    damage_breakdown = (
        filtered_df.dropna(subset=["damage_type", "latitude", "longitude"])
        .groupby(["project_id", "damage_type"])
        .size()
        .reset_index(name="count")
    )

    def build_hover(proj_id):
        sub = damage_breakdown[damage_breakdown["project_id"] == proj_id]
        if sub.empty:
            return "No detections"
        lines = [f"  • {row['damage_type']}: {row['count']}" for _, row in sub.iterrows()]
        return "<br>".join(lines)

    map_df["damage_breakdown"] = map_df["project_id"].apply(build_hover)
    map_df["location"] = map_df.apply(
        lambda r: ", ".join(
            [str(p).strip() for p in [r.get("street", ""), r.get("city", ""), r.get("province", ""), r.get("region", "")] if pd.notnull(p) and str(p).strip() and str(p).strip() != "N/A"]
        ),
        axis=1,
    )

    map_df["hover_text"] = map_df.apply(
        lambda r: (
            f"<b>{r['project_name']}</b><br>"
            f"📍 {r['location']}<br>"
            f"🖼️ Images: {r['total_images']}<br>"
            f"⚠️ Detections: {r['total_detections']}<br>"
            f"<br><b>Damage Breakdown:</b><br>{r['damage_breakdown']}"
        ),
        axis=1,
    )

    map_df["marker_size"] = (map_df["total_detections"].clip(lower=1) * 1.5 + 12).clip(
        upper=40
    )

    fig_map = go.Figure()
    fig_map.add_trace(
        go.Scattermap(
            lat=map_df["latitude"],
            lon=map_df["longitude"],
            mode="markers",
            marker=go.scattermap.Marker(
                size=map_df["marker_size"],
                color=map_df["total_detections"],
                colorscale="YlOrRd",
                colorbar=dict(title="Detections", thickness=12),
                opacity=0.85,
            ),
            text=map_df["hover_text"],
            hovertemplate="%{text}<extra></extra>",
            name="Projects",
        )
    )

    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

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

# ── Prep Charts & Breakdown Table (Early Instantiation) ──────────────────────
fig_donut = None
fig_bar = None
breakdown_tbl = None

if total_damages > 0:
    damage_counts = detections_df["damage_type"].value_counts().reset_index()
    damage_counts.columns = ["Distress Type", "Count"]

    fig_donut = px.pie(
        damage_counts,
        values="Count",
        names="Distress Type",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    project_damage_counts = (
        detections_df.groupby("project_name")
        .size()
        .reset_index(name="Total Distresses")
    )
    fig_bar = px.bar(
        project_damage_counts,
        x="project_name",
        y="Total Distresses",
        color="project_name",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_bar.update_layout(
        margin=dict(t=0, b=0, l=0, r=0), showlegend=False, xaxis_title=None
    )

    breakdown_tbl = (
        detections_df.groupby(["project_name", "damage_type"])
        .size()
        .reset_index(name="Count")
        .pivot_table(
            index="project_name", columns="damage_type", values="Count", fill_value=0
        )
        .reset_index()
        .rename(columns={"project_name": "Project"})
    )

# ── Manage PDF Export Cached State ────────────────────────────────────────────
filter_state_key = f"{sel_projects}_{sel_regions}_{sel_provinces}_{sel_cities}_{sel_damages}"
if st.session_state.get("last_filter_state_key") != filter_state_key:
    st.session_state.pdf_report_bytes = None
    st.session_state.last_filter_state_key = filter_state_key

# ── Export Action Bar ─────────────────────────────────────────────────────────
export_col1, export_col2 = st.columns([2, 1])
with export_col1:
    st.markdown(
        f"💡 *Showing **{total_projects}** projects, **{total_media}** images, and **{total_damages}** distresses based on filters.*"
    )
with export_col2:
    with st.popover("📤 Export Data Options", use_container_width=True):
        st.markdown("### 📊 Export Dashboard Data")
        st.write("Download the filtered records based on your active selections.")
        
        csv_detailed = convert_df_to_csv(filtered_df)
        st.download_button(
            label="📥 Download Detailed CSV",
            data=csv_detailed,
            file_name="rdd_detailed_analytics.csv",
            mime="text/csv",
            use_container_width=True,
        )
        
        if total_damages > 0:
            csv_breakdown = convert_breakdown_to_csv(detections_df)
            st.download_button(
                label="📥 Download Breakdown CSV",
                data=csv_breakdown,
                file_name="rdd_project_breakdown.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button(
                label="📥 Download Breakdown CSV",
                disabled=True,
                use_container_width=True,
                help="No distresses available to summarize."
            )
            
        st.markdown("---")
        st.markdown("### 📄 PDF Document Export")
        
        if st.session_state.pdf_report_bytes is None:
            if st.button("Generate PDF Report", use_container_width=True):
                with st.spinner("Compiling PDF report (rendering charts)..."):
                    try:
                        pdf_data = generate_pdf_report(
                            total_projects, total_media, total_damages, density,
                            fig_map, fig_donut, fig_bar, breakdown_tbl
                        )
                        st.session_state.pdf_report_bytes = pdf_data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {e}")
        else:
            st.download_button(
                label="📥 Download PDF Report",
                data=st.session_state.pdf_report_bytes,
                file_name="rdd_analytics_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            if st.button("🔄 Regenerate PDF", use_container_width=True):
                st.session_state.pdf_report_bytes = None
                st.rerun()

st.divider()

# ── Metrics ──────────────────────────────────────────────────────────────────
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

if not map_df.empty and fig_map is not None:
    map_event = st.plotly_chart(
        fig_map, width="stretch", on_select="rerun", selection_mode="points"
    )

    # Handle pin click navigation
    if map_event and "selection" in map_event and map_event["selection"]["points"]:
        point = map_event["selection"]["points"][0]
        point_idx = point.get("point_index")
        if point_idx is not None and point_idx < len(map_df):
            target_proj_id = map_df.iloc[point_idx]["project_id"]
            # Store in query params and session state for the project details page
            st.query_params["id"] = target_proj_id
            st.session_state.target_project = target_proj_id
            st.switch_page("pages/project_details.py")
else:
    st.info(
        "No projects with coordinates found. Add latitude/longitude to your projects to see pins on the map."
    )

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
if total_damages > 0:
    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        st.subheader("Distress Classification")
        st.plotly_chart(fig_donut, width="stretch")

    with chart_col2:
        st.subheader("Distresses per Project")
        st.plotly_chart(fig_bar, width="stretch")

    # ── Damage breakdown table per project ────────────────────────────────────
    st.subheader("Damage Breakdown by Project")
    st.dataframe(breakdown_tbl, width="stretch", hide_index=True)

else:
    st.info("No distresses detected in the selected projects.")
