import streamlit as st
import pandas as pd
from pathlib import Path

# === imports existants de ton projet ===
from utils.data_loader import prepare_main_dataset
from utils.sidebar import render_sidebar, apply_filters

# ============== CONFIG PAGE ==============
logo_path = Path(__file__).parent.parent / "assets" / "logo1.png"
st.set_page_config(
    page_title="Transport & Livraison",
    page_icon=str(logo_path),
    layout="wide"
)

# (optionnel) CSS global si tu as le fichier
try:
    with open('assets/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ============== CHARGEMENT DONNÉES ==============
@st.cache_data
def load_data():
    return prepare_main_dataset()

df_full = load_data()

# ============== SIDEBAR & FILTRES ==============
filters = render_sidebar(df_full)       # <-- ta sidebar existante
df = apply_filters(df_full, filters)    # <-- DataFrame filtré

# ============== FONCTION KPI ==============
def kpi_transport(df: pd.DataFrame) -> dict:
    n = len(df)
    if n == 0:
        return {
            "nb_commandes": 0,
            "nb_livrees": 0,
            "nb_vols": 0,
            "taux_livraison_reussie": 0.0,
            "taux_vol": 0.0
        }

    delivered = df['is_delivered'].fillna(False) if 'is_delivered' in df.columns else pd.Series(False, index=df.index)

    # ✅ Vol = uniquement incidents d'itinéraire
    theft_flag = df['has_theft_incident'].fillna(False) if 'has_theft_incident' in df.columns else pd.Series(False, index=df.index)

    return {
        "nb_commandes": n,
        "nb_livrees": int(delivered.sum()),
        "nb_vols": int(theft_flag.sum()),
        "taux_livraison_reussie": round(delivered.mean() * 100, 2),
        "taux_vol": round(theft_flag.mean() * 100, 2),
    }

# ============== KPI (SUR PÉRIMÈTRE FILTRÉ) ==============
st.title("Transport & Livraison")
st.markdown("---")

st.subheader("KPI Principaux")  # 👈 Section KPI

kpis = kpi_transport(df)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Commandes</div>
        <div class="kpi-value">{:,}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-description">Livrées : {livrees:,} • Vols : {vols:,}</div>
    </div>
    """.format(kpis['nb_commandes'], livrees=kpis['nb_livrees'], vols=kpis['nb_vols']), unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Livraison Réussie</div>
        <div class="kpi-value">{kpis['taux_livraison_reussie']}%</div>
        <div class="kpi-divider"></div>
        
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Taux de Vol</div>
        <div class="kpi-value">{kpis['taux_vol']}%</div>
        <div class="kpi-divider"></div>
        
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

##################################
##################################

# ================== GRAPHIQUES (charte interne) ==================
from utils.charts import (
    create_line_chart, create_bar_chart, create_area_chart, create_comparison_chart
)
from utils.visualizations import (
    create_dual_axis_timeline, create_performance_gauge,
    create_incident_heatmap, create_state_heatmap, create_risk_scatter
)

st.subheader("Analyse visuelle")

# --- Prépas robustes ---
if 'order_date' in df.columns:
    df['_month'] = pd.to_datetime(df['order_date']).dt.to_period('M').dt.to_timestamp()
else:
    df['_month'] = pd.NaT

# Agrégations mensuelles vols / commandes
if '_month' in df.columns and 'has_theft_incident' in df.columns:
    monthly = (
        df.groupby('_month')
          .agg(orders=('order_id', 'count'),
               thefts=('has_theft_incident', 'sum'))
          .reset_index()
    )
    if len(monthly):
        monthly['theft_rate'] = (monthly['thefts'] / monthly['orders'] * 100).round(2)
else:
    monthly = pd.DataFrame(columns=['_month', 'orders', 'thefts', 'theft_rate'])

# Agrégations transport
if 'transport_type' in df.columns and 'has_theft_incident' in df.columns:
    by_transport = (
        df.groupby('transport_type')
          .agg(orders=('order_id', 'count'),
               thefts=('has_theft_incident', 'sum'))
          .reset_index()
    )
    if len(by_transport):
        by_transport['theft_rate'] = (by_transport['thefts'] / by_transport['orders'] * 100).round(2)
else:
    by_transport = pd.DataFrame(columns=['transport_type', 'orders', 'thefts', 'theft_rate'])

# Agrégations état
state_col = 'state_code' if 'state_code' in df.columns else None
if state_col and 'has_theft_incident' in df.columns:
    by_state = (
        df.groupby(state_col)
          .agg(orders=('order_id', 'count'),
               thefts=('has_theft_incident', 'sum'))
          .reset_index()
    )
    if len(by_state):
        by_state['theft_rate'] = (by_state['thefts'] / by_state['orders'] * 100).round(2)
else:
    by_state = pd.DataFrame(columns=[state_col or 'state', 'orders', 'thefts', 'theft_rate'])

# ================== TABS ==================
tab1, tab2, tab3= st.tabs([
    ":material/calendar_month: Évolution Temporelle",
    ":material/train: Par Mode de Transport" ,
    ":material/location_on: Analyse Géographique"
    
])

# ---------- TAB 1 : Vols dans le temps ----------
with tab1:
    c1, c2 = st.columns([3, 1])
    
    if len(monthly):
        st.subheader("Commandes vs Incidents de Vol (Évolution mensuelle)")  
        # Timeline double axe : commandes (barres) vs taux de vol (ligne)
        fig_dual = create_dual_axis_timeline(
            monthly.rename(columns={'_month': 'order_date'}),
            date_col='order_date',
            metric1='orders', metric1_name='Commandes',
            metric2='theft_rate', metric2_name='Taux de vol (%)',
   
            christmas_col='is_christmas' # s’affichera si colonne présente
              
        )

        # --- Hover enrichi ---
        # On suppose que fig_dual a deux traces : [0]=barres commandes, [1]=ligne taux de vol
        if len(fig_dual.data) >= 1:
            fig_dual.data[0].update(
                hovertemplate="<b>%{x|%Y-%m}</b><br>"
                              "Commandes: %{y:,}<extra></extra>"
            )
        if len(fig_dual.data) >= 2:
            # ajouter vols si monthly contient 'thefts'
            if 'thefts' in monthly.columns:
                custom = monthly[['thefts']].to_numpy()
                fig_dual.data[1].update(
                    hovertemplate="<b>%{x|%Y-%m}</b><br>"
                                  "Taux de vol: %{y:.2f}%<br>"
                                  "Vols: %{customdata[0]:,}<extra></extra>",
                    customdata=custom
                )
            else:
                fig_dual.data[1].update(
                    hovertemplate="<b>%{x|%Y-%m}</b><br>"
                                  "Taux de vol: %{y:.2f}%<extra></extra>"
                )

        # --- Uniformiser la police avec tes autres graphs ---
        fig_dual.update_layout(
            font=dict(family="Arial, sans-serif", size=12, color="#2B3D50")
        )

        st.plotly_chart(fig_dual, use_container_width=True)

    else:
        st.info("Pas de données sur la période sélectionnée.")


# ---------- TAB 2 : Par mode de transport ----------
# ================== PAR MODE DE TRANSPORT (section unique, hover enrichi) ==================
# Assure-toi d'avoir déjà: import pandas as pd
from utils.charts import create_bar_chart, create_comparison_chart

# --- Définition utilitaire (hors onglet !) ---
def build_by_transport(df: pd.DataFrame) -> pd.DataFrame:
    required = {'transport_type', 'order_id', 'has_theft_incident'}
    if not required.issubset(df.columns) or len(df) == 0:
        return pd.DataFrame(columns=[
            'transport_type','orders','thefts','delivery_rate','non_delivery_rate','theft_rate'
        ])

    out = (
        df.groupby('transport_type')
          .agg(
              orders=('order_id', 'count'),
              thefts=('has_theft_incident', 'sum'),
              delivery_rate=('is_delivered', 'mean') if 'is_delivered' in df.columns
                            else ('order_id', lambda x: 0.0)
          )
          .reset_index()
    )

    # Taux en %
    if 'delivery_rate' not in out.columns:
        out['delivery_rate'] = 0.0

    out['theft_rate'] = (out['thefts'] / out['orders'] * 100).round(2)
    out['non_delivery_rate'] = ((1 - out['delivery_rate']) * 100).round(2)
    out['delivery_rate'] = (out['delivery_rate'] * 100).round(2)

    return out


# --- Rendu dans l'onglet Transport ---
with tab2:
    # ⚠️ IMPORTANT : utiliser le df FILTRÉ (déjà obtenu via apply_filters)
    by_transport = build_by_transport(df)

    if not by_transport.empty:
        

        # A) Barres : Taux de vol par mode (hover: taux + commandes + vols)
        _bt = by_transport.sort_values('theft_rate', ascending=False).copy()
        _bt['orders_display'] = _bt['orders']
        _bt['thefts_display'] = _bt['thefts']

        fig_vol = create_bar_chart(
            _bt,
            x='transport_type',
            y='theft_rate',
            title="Taux de vol (%) par mode de transport"
            
        )
        fig_vol.update_traces(
            hovertemplate="<b>%{x}</b><br>"
                          "Taux de vol: %{y:.2f}%<br>"
                          "Commandes: %{customdata[0]}<br>"
                          "Vols: %{customdata[1]}<extra></extra>",
            customdata=_bt[['orders_display','thefts_display']].to_numpy()
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        st.markdown("---")

        # B) Comparaison : Non-livré (%) vs Vol (%) (hover spécifique)
        cmp_df = by_transport.rename(columns={'transport_type': 'Mode'}).copy()
        fig_cmp = create_comparison_chart(
            cmp_df,
            categories='Mode',
            metrics=['non_delivery_rate', 'theft_rate'],
            title="Non-livré (%) vs Vol (%) par mode"
            
        )
        custom = cmp_df[['orders','thefts']].to_numpy()
        if len(fig_cmp.data) >= 1:
            fig_cmp.data[0].update(
                hovertemplate="<b>%{x}</b><br>"
                              "Non-livré: %{y:.2f}%<br>"
                              "Commandes: %{customdata[0]}<extra></extra>",
                customdata=custom
            )
        if len(fig_cmp.data) >= 2:
            fig_cmp.data[1].update(
                hovertemplate="<b>%{x}</b><br>"
                              "Taux de vol: %{y:.2f}%<br>"
                              "Vols: %{customdata[1]}<extra></extra>",
                customdata=custom
            )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # C) Tableau dynamique (lié aux filtres)
        st.dataframe(
            by_transport[['transport_type','orders','delivery_rate','non_delivery_rate','theft_rate']]
              .sort_values('theft_rate', ascending=False)
              .rename(columns={
                  'transport_type': 'Transport',
                  'orders': 'Commandes',
                  'delivery_rate': 'Livraison (%)',
                  'non_delivery_rate': 'Non-livré (%)',
                  'theft_rate': 'Vol (%)'
              }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune donnée transport sur le périmètre sélectionné.")


# ---------- TAB 3 : Par État ----------
with tab3:
    if len(by_state):
        # Top 10 par taux
        top_states = by_state.sort_values('theft_rate', ascending=False).head(10)

        # préparer colonnes supplémentaires pour le hover
        top_states_display = top_states.copy()
        top_states_display['theft_rate (%)'] = top_states_display['theft_rate']
        top_states_display['commandes'] = top_states_display['orders']
        top_states_display['vols'] = top_states_display['thefts']

        fig_state_rate = create_bar_chart(
            top_states_display,
            x=state_col,
            y='theft_rate',
            title="Top 10 États par taux de vol (%)",

            horizontal=False
        )

        # enrichir le hover avec taux (%) + commandes + vols
        fig_state_rate.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                          "Taux de vol: %{y:.2f}%<br>" +
                          "Commandes: %{customdata[0]}<br>" +
                          "Vols: %{customdata[1]}<extra></extra>",
            customdata=top_states_display[['commandes','vols']].to_numpy()
        )

        st.plotly_chart(fig_state_rate, use_container_width=True)

    else:
        st.info("Aucune donnée État sur ce périmètre.")

