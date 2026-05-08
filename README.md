# 🛣️ Road Damage Detection (RDD) Dashboard

A professional, full-stack AI-powered platform for managing, detecting, and analyzing road distresses. Built with **Streamlit**, **Supabase**, and **YOLO**, this application provides a complete workflow from image upload to geospatial analytics.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLO-v11%20|%20v8--seg-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)

---

## 🌟 Key Features

### 📊 Analytics Dashboard
- **Interactive Damage Map**: Geospatial visualization of all projects using Plotly. Clickable pins redirect to project details.
- **Visual Metrics**: Real-time charts for distress classification (Alligator Cracks, Potholes, etc.) and project-wise distribution.
- **Global Filters**: Filter the entire dashboard by Project, Region, or specific Damage Type.

### 📂 Project Management
- **Card-Based Directory**: Elegant project overview with thumbnails and metadata.
- **Geographic Tagging**: Integrated Folium map for pinning precise project locations during creation.
- **Access Control**: Projects are linked to user accounts via Supabase Auth.

### 📷 Media Gallery & AI Processing
- **Dual AI Engine**: Choose between **YOLOv11 (Detection)** and **YOLOv8-seg (Segmentation)**.
- **Batch Selection**: Select multiple images to process or download.
- **Cache-Busting UI**: Smart image reloading ensures you always see the latest AI results.
- **Export**: One-click ZIP generation for downloading annotated datasets.

### 🔐 Secure Authentication
- Full Sign-In/Sign-Up flow powered by **Supabase Auth**.
- Persistent user sessions and profile management.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | Python, Supabase (Database & Storage) |
| **Computer Vision** | Ultralytics (YOLOv11, YOLOv8-seg), OpenCV |
| **Visualizations** | Plotly, Folium |
| **Storage** | Supabase Buckets (Raw & Annotated images) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- A Supabase Project (URL and API Key)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/rdd-streamlit.git
cd rdd-streamlit

# Install dependencies
pip install -r requirements.txt
```

### 3. Model Weights
Place your trained YOLO weights in the following directories:
- `models/yolov11/weights/best.pt`
- `models/yolov8seg/weights/best.pt`

### 4. Configuration
Create a `.streamlit/secrets.toml` file with your credentials:
```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-service-role-key"
```

### 5. Run the Application
```bash
streamlit run app.py
```

---

## 📂 Project Structure
```text
├── ai/                     # AI Inference & Processing Logic
├── models/                 # YOLO Model Weights & Configurations
├── pages/                  # Streamlit Multi-page Application
│   ├── analytics.py        # Main Dashboard & Map
│   ├── projects.py         # Project Directory
│   ├── project_details.py  # Gallery & AI Processor UI
│   └── ...
├── database.py             # Supabase Wrapper & CRUD Operations
└── app.py                  # Application Entry Point
```

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Designed by Swyft*