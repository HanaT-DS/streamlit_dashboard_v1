"""
Sidebar réutilisable pour toutes les pages du dashboard
"""
import streamlit as st
import pandas as pd
from pathlib import Path

def render_sidebar(df):
    """
    Crée la sidebar avec logo et navigation
    
    Args:
        df: DataFrame principal (résultat de prepare_main_dataset())
    
    Returns:
        dict: Dictionnaire vide (pour compatibilité)
    """
    logo_path = Path(__file__).parent.parent / "assets" / "logo1.png"
    
    with st.sidebar:
        # === Logo en haut ===
        if logo_path.exists():
            st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
            st.image(str(logo_path))
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<hr/>", unsafe_allow_html=True)
        
        # ===== 🧭 SECTION NAVIGATION =====
        st.markdown("### Navigation")
        
        # Liens vers les pages
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Home", use_container_width=True, icon=":material/home:"):
                st.switch_page("test1.py")
        with col2:
            if st.button("Overview",  icon=":material/dashboard:",use_container_width=True):
                st.switch_page("pages/overview.py")
        
        # Autres pages (à décommenter quand vous les créerez)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Transport", use_container_width=True,icon=":material/delivery_truck_speed:"):
                st.switch_page("pages/transport.py")
        with col2:
            if st.button("Claims", use_container_width=True,icon=":material/warning:"):
                st.switch_page("pages/reclamations.py")
        
        st.markdown('<hr>', unsafe_allow_html=True)


        # Initialiser session_state si nécessaire
        if 'start_date' not in st.session_state:
            st.session_state.start_date = df['order_date'].min().date()
        if 'end_date' not in st.session_state:
            st.session_state.end_date = df['order_date'].max().date()

        min_date = df['order_date'].min().date()
        max_date = df['order_date'].max().date()

        # Slider
        date_range = st.slider(
            ":material/date_range: Période d'analyse",
            min_value=min_date,
            max_value=max_date,
            value=(st.session_state.start_date, st.session_state.end_date),
            format="YYYY-MM-DD"
        )

        # Mettre à jour session_state depuis le slider
        st.session_state.start_date = date_range[0]
        st.session_state.end_date = date_range[1]

        # Date inputs synchronisés
        col1, col2 = st.columns(2)
        with col1:
            start_input = st.date_input(
                "Date début",
                value=st.session_state.start_date,
                min_value=min_date,
                max_value=max_date
            )
        with col2:
            end_input = st.date_input(
                "Date fin",
                value=st.session_state.end_date,
                min_value=min_date,
                max_value=max_date
            )

        # Mettre à jour session_state depuis les inputs
        if start_input != st.session_state.start_date or end_input != st.session_state.end_date:
            st.session_state.start_date = start_input
            st.session_state.end_date = end_input
            st.rerun()

        # Utiliser les dates du session_state pour les filtres
        date_range = (st.session_state.start_date, st.session_state.end_date)

        st.markdown('<hr>', unsafe_allow_html=True)

        
        # Filtre 3 : Modes de transport
        transport_filter = st.multiselect(
            ":material/local_shipping: Modes de transport",
            options=sorted(df['transport_type'].dropna().unique().tolist()),
            default=df['transport_type'].dropna().unique().tolist()
        )
        
        # Filtre 4 : États
        state_filter = st.multiselect(
            ":material/map_search: États",
            options=sorted(df['state_code'].dropna().unique().tolist()),
            default=[]
        )
        
        st.markdown('<hr>', unsafe_allow_html=True)
            
        # Bouton Reset
        if st.button("Réinitialiser les filtres", use_container_width=True, icon=":material/restart_alt:"):
            # Réinitialiser les dates aux valeurs min/max
            st.session_state.start_date = df['order_date'].min().date()
            st.session_state.end_date = df['order_date'].max().date()
            
            # Réinitialiser les autres filtres via query params (pour forcer le reset des multiselect)
            st.query_params.clear()
            
            # Recharger la page
            st.rerun()
        
        st.markdown('<hr>', unsafe_allow_html=True)

        # a revoir uploader et downloader
        st.file_uploader("Importer un fichier CSV", type=["csv"])
        st.download_button("Télécharger un modèle CSV", data=df.to_csv(index=False), file_name="modele.csv")
        
        
        # Footer
        st.caption("Dashboard v1.0 | © 2025")
    
    # Retourner les filtres sous forme de dictionnaire
    return {
        'start_date': st.session_state.start_date,  
        'end_date': st.session_state.end_date,      
        'transport_filter': transport_filter,
        'state_filter': state_filter
    }


def apply_filters(df, filters):
    """
    Applique les filtres au DataFrame
    
    Args:
        df: DataFrame à filtrer
        filters: Dict retourné par render_sidebar()
    
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    # Filtre par date
    df_filtered = df[
        (df['order_date'].dt.date >= filters['start_date']) &  
        (df['order_date'].dt.date <= filters['end_date'])      
    ]

    
    # Filtre par mode de transport
    if filters['transport_filter']:
        df_filtered = df_filtered[df_filtered['transport_type'].isin(filters['transport_filter'])]
    
    # Filtre par état
    if filters['state_filter']:
        df_filtered = df_filtered[df_filtered['state_code'].isin(filters['state_filter'])]
    
    return df_filtered

    
        
        