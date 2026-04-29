import streamlit as st
import os

st.set_page_config(page_title="About RCMED", page_icon="🏢", layout="wide")

# ── ASSET CONSTANTS ──────────────────────────────────────────────────────────
ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

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
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid #800000;
        padding-left: 1rem;
    }
    
    /* Cards */
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
        justify-content: flex-start;
        height: 100%;
        min-height: 250px;
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
        background: #f1f5f9;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
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
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
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
        width: 50px;
        height: 50px;
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
st.markdown("""
<div style="color: #475569; line-height: 1.8; font-size: 1.1rem; max-width: 1000px; margin-bottom: 3rem;">
    RCMED is a technology-driven system designed to automate and enhance road pavement damage detection, 
    classification, and evaluation across the Philippines. By integrating deep learning models with geotagged 
    mobile data collection, the platform provides a more objective and efficient approach to road condition 
    assessment. This project supports faster decision-making for government agencies, ensuring that road maintenance 
    and infrastructure improvements are guided by accurate, real-time data.
</div>
""", unsafe_allow_html=True)

# ── PROJECT COLLABORATION ────────────────────────────────────────────────────
st.markdown('<div class="section-header">Project Collaboration</div>', unsafe_allow_html=True)

cols = st.columns(5)

partners = [
    {"name": "Technological University of the Philippines", "id": "tup", "label": "TUP Logo"},
    {"name": "De La Salle University", "id": "dlsu", "label": "DLSU Logo"},
    {"name": "Bulacan State University", "id": "bulsu", "label": "BulSU Logo"},
    {"name": "Commission on Higher Education", "id": "ched", "label": "CHED Logo"},
    {"name": "Department of Public Works and Highways", "id": "dpwh", "label": "DPWH Logo"}
]

for i, partner in enumerate(partners):
    with cols[i]:
        logo_path = os.path.join(ASSETS_DIR, f"{partner['id']}_logo.png")
        if os.path.exists(logo_path):
            import base64
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            logo_html = f'<div class="logo-container"><img src="data:image/png;base64,{encoded}" class="logo-img"></div>'
        else:
            logo_html = f'<div class="logo-container"><div class="logo-placeholder">{partner["label"]}</div></div>'
            
        st.markdown(f"""
        <div class="collab-card">
            {logo_html}
            <div class="collab-name">{partner['name']}</div>
        </div>
        """, unsafe_allow_html=True)

# ── ABOUT THE COLLABORATOR ───────────────────────────────────────────────────
st.markdown('<div class="section-header">About Me</div>', unsafe_allow_html=True)

profile_path = os.path.join(ASSETS_DIR, "profile.png")
bulsu_logo_path = os.path.join(ASSETS_DIR, "bulsu_logo.png")

if os.path.exists(profile_path):
    import base64
    with open(profile_path, "rb") as f:
        p_encoded = base64.b64encode(f.read()).decode()
    profile_html = f'<img src="data:image/png;base64,{p_encoded}" class="profile-photo">'
else:
    profile_html = '<div class="profile-placeholder">Profile Photo</div>'

if os.path.exists(bulsu_logo_path):
    import base64
    with open(bulsu_logo_path, "rb") as f:
        b_encoded = base64.b64encode(f.read()).decode()
    bulsu_overlay_html = f'<div class="bulsu-logo-overlay"><img src="data:image/png;base64,{b_encoded}" class="logo-img"></div>'
else:
    bulsu_overlay_html = '<div class="bulsu-logo-overlay">BulSU Logo</div>'

st.markdown(f"""
<div class="profile-card">
    <div class="profile-img-container">
        {profile_html}
        {bulsu_overlay_html}
    </div>
    <div class="profile-details">
        <div class="profile-name">Engr. Christopher F. Cunanan, PCpE</div>
        <div class="profile-title">PhD Graduate Student Collaborator, RCMED Project</div>
        <ul class="profile-list">
            <li>BS Computer Engineering, De La Salle-Araneta University</li>
            <li>Master of Engineering major in Computer Engineering, Technological University of the Philippines</li>
            <li>PhD Graduate Student Collaborator, RCMED Project</li>
            <li>From Bulacan State University</li>
            <li>Associate Member, National Research Council of the Philippines (NRCP)</li>
            <li>Former faculty and Engineering Department Head, Lyceum of the Philippines University Manila</li>
            <li>Former faculty and Dean, AMA Computer College Malolos</li>
            <li>Former faculty, De La Salle-Araneta University</li>
            <li>Industry experience in software engineering and testing</li>
            <li>Researcher, mentor, chess master and coach, and technopreneur</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="designer-footer">
    Designed by <span class="swyft">swyft</span>
</div>
""", unsafe_allow_html=True)
