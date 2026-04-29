import streamlit as st
import os
import base64

st.set_page_config(page_title="About RCMED", page_icon="🏢", layout="wide")

# ── ASSET CONSTANTS ──────────────────────────────────────────────────────────
ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #4a0404 0%, #800000 100%);
        color: white;
        padding: 4rem 2rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 3rem;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Section Headers */
    .section-header {
        color: #1e293b;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 3rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid #800000;
        padding-left: 1rem;
    }
    
    /* Collab Cards */
    .collab-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        transition: transform 0.2s;
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 280px; /* Fixed height for uniformity */
        margin-bottom: 1rem;
    }
    .collab-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .logo-container {
        width: 100px;
        height: 100px;
        flex-shrink: 0;
        margin: 0 auto 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .logo-img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
    .logo-placeholder {
        width: 80px;
        height: 80px;
        flex-shrink: 0;
        background: #f1f5f9;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        color: #64748b;
        font-weight: 600;
        font-size: 0.7rem;
        border: 2px dashed #cbd5e1;
        text-align: center;
        padding: 0.5rem;
    }
    .collab-name {
        color: #334155;
        font-weight: 600;
        line-height: 1.4;
        font-size: 0.95rem;
    }

    /* Team Cards */
    .team-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #e2e8f0;
        height: 240px; /* Fixed height for uniformity */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
        margin-bottom: 1rem;
    }

    .team-card:hover { transform: translateY(-3px); }
    
    .team-photo-container {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        margin-bottom: 1rem;
        overflow: hidden;
        border: 3px solid #800000;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8fafc;
    }
    .team-photo { width: 100%; height: 100%; object-fit: cover; }
    
    .team-name { font-weight: 700; color: #1e293b; font-size: 1.05rem; margin-bottom: 0.25rem; }
    .team-role { font-size: 0.85rem; color: #64748b; line-height: 1.3; font-weight: 500; }
    
    /* Profile Section */
    .profile-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: row;
        gap: 2rem;
        align-items: flex-start;
        border: 1px solid #e2e8f0;
    }
    @media (max-width: 768px) {
        .profile-card {
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
    }
    .profile-img-container {
        flex-shrink: 0;
        position: relative;
    }
    .profile-photo {
        width: 180px;
        height: 180px;
        border-radius: 1rem;
        object-fit: cover;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .profile-placeholder {
        width: 180px;
        height: 180px;
        background: #f8fafc;
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px dashed #cbd5e1;
        color: #94a3b8;
    }
    .bulsu-logo-overlay {
        position: absolute;
        bottom: -10px;
        right: -10px;
        width: 55px;
        height: 55px;
        background: white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        font-weight: bold;
        color: #800000;
        border: 1px solid #e2e8f0;
        text-align: center;
        overflow: hidden;
    }
    .profile-details {
        flex-grow: 1;
    }
    .profile-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .profile-title {
        color: #800000;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .profile-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .profile-list li {
        margin-bottom: 0.5rem;
        color: #475569;
        padding-left: 1.5rem;
        position: relative;
    }
    .profile-list li::before {
        content: "•";
        color: #800000;
        font-weight: bold;
        position: absolute;
        left: 0;
    }
    
    /* Footer */
    .designer-footer {
        margin-top: 5rem;
        padding: 2rem;
        text-align: center;
        border-top: 1px solid #f1f5f9;
        color: #94a3b8;
        font-size: 0.75rem;
    }
    .swyft {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)

# ── HERO SECTION ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="hero-title">RCMED</div>
    <div class="hero-subtitle">
        Road Condition Monitoring and Evaluation Device for Philippine Road Pavements
    </div>
    <p style="margin-top: 1.5rem; opacity: 0.8; font-weight: 500;">
        A Collaboration between TUP, DLSU, BulSU, CHED, and DPWH
    </p>
</div>
""", unsafe_allow_html=True)

# ── ABOUT THE PROJECT ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">About the Project</div>', unsafe_allow_html=True)
st.write("""
    RCMED is a technology-driven system designed to automate and enhance road pavement damage detection, 
    classification, and evaluation across the Philippines. By integrating deep learning models with geotagged 
    mobile data collection, the platform provides a more objective and efficient approach to road condition 
    assessment. This project supports faster decision-making for government agencies, ensuring that road maintenance 
    and infrastructure improvements are guided by accurate, real-time data.
""")

# ── PROJECT COLLABORATION ────────────────────────────────────────────────────
st.markdown('<div class="section-header">Project Collaboration</div>', unsafe_allow_html=True)

cols_p = st.columns(5)
partners = [
    {"name": "Technological University of the Philippines", "id": "tup", "label": "TUP Logo"},
    {"name": "De La Salle University", "id": "dlsu", "label": "DLSU Logo"},
    {"name": "Bulacan State University", "id": "bulsu", "label": "BulSU Logo"},
    {"name": "Commission on Higher Education", "id": "ched", "label": "CHED Logo"},
    {"name": "Department of Public Works and Highways", "id": "dpwh", "label": "DPWH Logo"}
]

for i, partner in enumerate(partners):
    with cols_p[i]:
        b64 = get_base64_image(os.path.join(ASSETS_DIR, f"{partner['id']}_logo.png"))
        logo_html = f'<div class="logo-container"><img src="data:image/png;base64,{b64}" class="logo-img"></div>' if b64 else f'<div class="logo-container"><div class="logo-placeholder">{partner["label"]}</div></div>'
        st.markdown(f"""
        <div class="collab-card">
            {logo_html}
            <div class="collab-name">{partner['name']}</div>
        </div>
        """, unsafe_allow_html=True)

# ── PROJECT TEAM ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Project Team</div>', unsafe_allow_html=True)

project_team = [
    {"name": "Dr. Ryan Reyes", "role": "Project Leader", "id": "ryan_reyes"},
    {"name": "Engr. Christopher Cunanan", "role": "PhD Graduate Student Collaborator", "id": "christopher_cunanan"},
    {"name": "Engr. Jessica Velasco", "role": "Project Member", "id": "jessica_velasco"},
    {"name": "Dr. Lean Karlo Tolentino", "role": "Project Member", "id": "lean_karlo"},
    {"name": "Engr. Mark Melgrito", "role": "Project Member", "id": "mark_melgrito"},
    {"name": "Dr. Ira Estropia", "role": "Project Member", "id": "ira_estropia"},
    {"name": "Engr. Immanuel Valencia", "role": "Project Member", "id": "immanuel_valencia"}
]

rows = [project_team[i:i+4] for i in range(0, len(project_team), 4)]
for row in rows:
    cols = st.columns(4)
    for i, member in enumerate(row):
        with cols[i]:
            b64 = get_base64_image(os.path.join(ASSETS_DIR, f"{member['id']}.png"))
            photo_html = f'<img src="data:image/png;base64,{b64}" class="team-photo">' if b64 else '<div style="color:#cbd5e1; font-size:2rem;">👤</div>'
            st.markdown(f"""
            <div class="team-card">
                <div class="team-photo-container">{photo_html}</div>
                <div class="team-name">{member['name']}</div>
                <div class="team-role">{member['role']}</div>
            </div>
            """, unsafe_allow_html=True)

# ── TECHNICAL TEAM ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Technical Team</div>', unsafe_allow_html=True)

tech_team = [
    {"name": "Engr. Joseph Den Amores", "role": "Developer", "id": "joseph_amores"},
    {"name": "Engr. Charles Darwin Maddela", "role": "Developer", "id": "chad_madella"},
    {"name": "Engr. Victor Sebastian Bondoc", "role": "Developer", "id": "victor_sebastian"},
    {"name": "Engr. Julius Nikolai Bernardo", "role": "Developer", "id": "julius_bernardo"},
    {"name": "Ms. Maria Kristinna Alina", "role": "Project Manager", "id": "kristina_alina"}
]

rows_tech = [tech_team[i:i+4] for i in range(0, len(tech_team), 4)]
for row in rows_tech:
    cols = st.columns(4)
    for i, member in enumerate(row):
        with cols[i]:
            b64 = get_base64_image(os.path.join(ASSETS_DIR, f"{member['id']}.png"))
            photo_html = f'<img src="data:image/png;base64,{b64}" class="team-photo">' if b64 else '<div style="color:#cbd5e1; font-size:2rem;">👤</div>'
            st.markdown(f"""
            <div class="team-card">
                <div class="team-photo-container">{photo_html}</div>
                <div class="team-name">{member['name']}</div>
                <div class="team-role">{member['role']}</div>
            </div>
            """, unsafe_allow_html=True)

# ── ABOUT ME ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">About Me</div>', unsafe_allow_html=True)

p_b64 = get_base64_image(os.path.join(ASSETS_DIR, "profile.png"))
profile_html = f'<img src="data:image/png;base64,{p_b64}" class="profile-photo">' if p_b64 else '<div class="profile-placeholder">Profile Photo</div>'

b_b64 = get_base64_image(os.path.join(ASSETS_DIR, "bulsu_logo.png"))
bulsu_overlay_html = f'<div class="bulsu-logo-overlay"><img src="data:image/png;base64,{b_b64}" class="logo-img"></div>' if b_b64 else '<div class="bulsu-logo-overlay">BulSU Logo</div>'

st.markdown(f"""
<div class="profile-card">
    <div class="profile-img-container">{profile_html}{bulsu_overlay_html}</div>
    <div class="profile-details">
        <div class="profile-name">Engr. Christopher F. Cunanan, PCpE</div>
        <div class="profile-title">PhD Graduate Student Collaborator, RCMED Project</div>
        <ul class="profile-list">
            <li>Assistant Professor at Bulacan State University</li>
            <li>PhD Graduate Student and Collaborator of the RCMED Project</li>
            <li>Associate Member of the National Research Council of the Philippines (NRCP)</li>
            <li>Earned his BS in Computer Engineering from De La Salle-Araneta University</li>
            <li>Earned his Master of Engineering major in Computer Engineering from the Technological University of the Philippines</li>
            <li>Former Faculty Member and Engineering Department Head at Lyceum of the Philippines University Manila</li>
            <li>Former Faculty Member and Dean at AMA Computer College Malolos</li>
            <li>Former Faculty Member at De La Salle-Araneta University</li>
            <li>Has industry experience in software engineering and testing</li>
            <li>Active researcher, mentor, chess master and coach, and technopreneur</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown('<div class="designer-footer">Designed by <span class="swyft">swyft</span></div>', unsafe_allow_html=True)
