import streamlit as st
from pathlib import Path
from datetime import datetime

# ===== CONFIGURATION =====
logo_path = Path(__file__).parent / "assets" / "logo1.png"

st.set_page_config(
    page_title="Dashboard LogistixUp",
    page_icon=str(logo_path) if logo_path.exists() else "📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Charger le CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# ===== BACKGROUND SPÉCIFIQUE PAGE HOME =====
st.markdown("""
    <style>
        /* Masquer sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Background dégradé élégant */
        .stApp {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 30%, #dbeafe 70%, #f8fafc 100%);
        }
        
        /* Pattern subtil de points */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: radial-gradient(circle, rgba(5, 94, 130, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            pointer-events: none;
            z-index: -1;
        }
    </style>
""", unsafe_allow_html=True)

# ===== HEADER AVEC LOGO CENTRÉ =====
col1, col2, col3 = st.columns([1, 2, 1])

with col2:   
    # Titres centrés
    st.markdown("<h1 style='text-align: center; '>LogistixUp Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #6b7280;'>Plateforme d'analyse et de suivi des performances logistiques</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===== MESSAGE DE BIENVENUE =====
current_hour = datetime.now().hour
if current_hour < 12:
    greeting = "Bonjour"
    emoji = "☀️"
elif current_hour < 18:
    greeting = "Bon après-midi"
    emoji = "🌤️"
else:
    greeting = "Bonsoir"
    emoji = "🌙"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div style='text-align: center; padding: 40px; background: linear-gradient(135deg, #055e82 0%, #0a7ea4 100%); 
         border-radius: 15px; margin: 20px 0;'>
        <h2 style='color: white; margin: 0; font-size: 32px;'>{emoji} {greeting}, Utilisateur !</h2>
        <p style='color: #ffd447; font-size: 20px; margin-top: 15px;'>
            Bienvenue sur votre tableau de bord
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===== BOUTONS DE NAVIGATION (CENTRÉS + VERTICAUX) =====

# Créer 3 colonnes pour centrer
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Bouton 1
    if st.button("Overview", key="goto_overview", icon=":material/dashboard:", use_container_width=True):
        st.switch_page("pages/overview.py")
    
    # Bouton 2
    if st.button("Transport", key="goto_transport",icon=":material/delivery_truck_speed:" ,use_container_width=True):
        st.switch_page("pages/transport.py")
    
    # Bouton 3
    if st.button("Claims", key="goto_reclamations",icon=":material/warning:", use_container_width=True):
        st.switch_page("pages/reclamations.py")
# ===== FOOTER =====
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 14px; margin-top: 50px;'>
    Dashboard v1.0 | © 2025 | Propulsé par Streamlit
</div>
""", unsafe_allow_html=True)