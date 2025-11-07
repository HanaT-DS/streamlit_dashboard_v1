import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from utils.data_loader import prepare_main_dataset, get_kpi_metrics
from utils.charts import create_line_chart, create_comparison_chart, create_bar_chart
from utils.helpers import format_currency, format_percentage, calculate_growth_rate
from utils.sidebar import render_sidebar, apply_filters

# ===== CONFIGURATION =====
logo_path = Path(__file__).parent.parent / "assets" / "logo1.png"


st.set_page_config(
    page_title="Overview",
    page_icon=str(logo_path),  # favicon = ton logo
    layout="wide"
)

# Charger le CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ===== CHARGEMENT DES DONNÉES =====
@st.cache_data
def load_data():
    return prepare_main_dataset()

df_full = load_data()

# ===== SIDEBAR AVEC NAVIGATION =====
filters = render_sidebar(df_full)  # 👈 AJOUTÉ
df = apply_filters(df_full, filters)  # 👈 AJOUTÉ (pour l'instant retourne tout)

# Recalculer les KPI avec données filtrées
kpis = get_kpi_metrics(df)

# Initialiser l'état de sélection KPI
if 'selected_kpi' not in st.session_state:
    st.session_state.selected_kpi = 'CA'

# ===== HEADER =====
st.title("Overview")

# ===== SECTION KPI =====
st.subheader("KPI Principaux")

# ===== CALCUL DES PÉRIODES DE COMPARAISON =====
# Période actuelle (filtrée)
current_start = filters['start_date']
current_end = filters['end_date']

# Calcul de la période précédente (même durée)
period_duration = (current_end - current_start).days
previous_start = current_start - pd.Timedelta(days=period_duration + 1)
previous_end = current_start - pd.Timedelta(days=1)

# Données période précédente
df_previous = df_full[
    (df_full['order_date'].dt.date >= previous_start) &
    (df_full['order_date'].dt.date <= previous_end)
]

# KPI période actuelle (déjà calculés)
kpis_current = kpis

# KPI période précédente
kpis_previous = get_kpi_metrics(df_previous) if len(df_previous) > 0 else None

# ===== CALCUL DES DELTAS =====
if kpis_previous:
    delta_ca = calculate_growth_rate(kpis_current['ca_total'], kpis_previous['ca_total'])
    delta_nb_orders = calculate_growth_rate(kpis_current['nb_orders'], kpis_previous['nb_orders'])
    delta_claim_rate = kpis_current['claim_rate'] - kpis_previous['claim_rate']
    delta_delivery_rate = kpis_current['delivery_rate'] - kpis_previous['delivery_rate']
else:
    # Pas de période précédente disponible
    delta_ca = 0
    delta_nb_orders = 0
    delta_claim_rate = 0
    delta_delivery_rate = 0

col1, col2, col3, col4 = st.columns(4)

# ===== KPI 1 : CHIFFRE D'AFFAIRES =====
with col1:
    delta_class = 'positive' if delta_ca >= 0 else 'negative'
    delta_symbol = '↗' if delta_ca >= 0 else '↘'
    
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Chiffre d'Affaires</div>
        <div class="kpi-value">{format_currency(kpis_current['ca_total'])}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_ca):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== KPI 2 : NOMBRE DE COMMANDES =====
with col2:
    delta_class = 'positive' if delta_nb_orders >= 0 else 'negative'
    delta_symbol = '↗' if delta_nb_orders >= 0 else '↘'
    
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Commandes</div>
        <div class="kpi-value">{kpis_current['nb_orders']:,}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_nb_orders):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== KPI 3 : CLAIM RATE =====
with col3:
    # Pour claim rate, une baisse est positive
    delta_class = 'positive' if delta_claim_rate <= 0 else 'negative'
    delta_symbol = '↗' if delta_claim_rate >= 0 else '↘'
    
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Réclamations</div>
        <div class="kpi-value">{kpis_current['claim_rate']:.1f}%</div>
        <div class="kpi-divider"></div>
        <div class="kpi-description">Montant : {format_currency(kpis_current['montant_claims'])}</div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_claim_rate):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== KPI 4 : DELIVERY SUCCESS RATE =====
with col4:
    delta_class = 'positive' if delta_delivery_rate >= 0 else 'negative'
    delta_symbol = '↗' if delta_delivery_rate >= 0 else '↘'
    
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Livraison Réussie</div>
        <div class="kpi-value">{kpis_current['delivery_rate']:.1f}%</div>
        <div class="kpi-divider"></div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_delivery_rate):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===== SECTION GRAPHIQUES INTERACTIFS =====
st.subheader("Analyse Temporelle")

# Préparer les données temporelles quotidiennes
df_daily = df.groupby(df['order_date'].dt.date).agg({
    'total_amount': 'sum',
    'order_id': 'count',
    'is_delivered': 'mean',
    'has_claim': 'mean',
    'claim_amount': 'sum'
}).reset_index()

df_daily.columns = ['date', 'ca_daily', 'nb_orders', 'delivery_rate', 'claim_rate', 'claim_amount']
df_daily['date'] = pd.to_datetime(df_daily['date'])
df_daily['delivery_rate'] = df_daily['delivery_rate'] * 100
df_daily['claim_rate'] = df_daily['claim_rate'] * 100

# ===== SÉLECTEURS =====
col_graph, col_freq = st.columns([3, 1])

with col_graph:
    selected_graph = st.radio(
        "Choisir la métrique à visualiser :",
        [":material/attach_money: Chiffre d'Affaires", 
         ":material/shopping_bag: Nombre de Commandes", 
         ":material/report_problem: Taux de Réclamations", 
         ":material/local_shipping: Taux de Livraison"],
        horizontal=True
    )

with col_freq:
    frequency = st.selectbox(
        "Fréquence :",
        ["Quotidien", "Hebdomadaire", "Mensuel", "Annuel"],
        index=0
    )

st.markdown("---")

# ===== AGRÉGATION SELON LA FRÉQUENCE =====
if frequency == "Quotidien":
    df_display = df_daily.copy()
    freq_label = "quotidien"
    date_col = 'date'

elif frequency == "Hebdomadaire":
    df_daily['week'] = df_daily['date'].dt.to_period('W').dt.to_timestamp()
    df_display = df_daily.groupby('week').agg({
        'ca_daily': 'sum',
        'nb_orders': 'sum',
        'delivery_rate': 'mean',
        'claim_rate': 'mean',
        'claim_amount': 'sum'
    }).reset_index()
    df_display.columns = ['date', 'ca_daily', 'nb_orders', 'delivery_rate', 'claim_rate', 'claim_amount']
    freq_label = "hebdomadaire"
    date_col = 'date'

elif frequency == "Mensuel":
    df_daily['month'] = df_daily['date'].dt.to_period('M').dt.to_timestamp()
    df_display = df_daily.groupby('month').agg({
        'ca_daily': 'sum',
        'nb_orders': 'sum',
        'delivery_rate': 'mean',
        'claim_rate': 'mean',
        'claim_amount': 'sum'
    }).reset_index()
    df_display.columns = ['date', 'ca_daily', 'nb_orders', 'delivery_rate', 'claim_rate', 'claim_amount']
    freq_label = "mensuel"
    date_col = 'date'

else:  # Annuel
    df_daily['year'] = df_daily['date'].dt.to_period('Y').dt.to_timestamp()
    df_display = df_daily.groupby('year').agg({
        'ca_daily': 'sum',
        'nb_orders': 'sum',
        'delivery_rate': 'mean',
        'claim_rate': 'mean',
        'claim_amount': 'sum'
    }).reset_index()
    df_display.columns = ['date', 'ca_daily', 'nb_orders', 'delivery_rate', 'claim_rate', 'claim_amount']
    freq_label = "annuel"
    date_col = 'date'

# ===== AFFICHAGE DU GRAPHIQUE =====
if selected_graph == ":material/attach_money: Chiffre d'Affaires":
    fig = create_line_chart(
        df_display, 
        x=date_col, 
        y='ca_daily',
        title="Évolution du Chiffre d'Affaires",
        subtitle=f"Montant {freq_label}"
    )
    st.plotly_chart(fig, use_container_width=True)
    
        # Déterminer un label clair pour la fréquence
    if frequency == "Quotidien":
        unit_label = "jour"
    elif frequency == "Hebdomadaire":
        unit_label = "semaine"
    elif frequency == "Mensuel":
        unit_label = "mois"
    else:
        unit_label = "an"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"CA moyen par {unit_label}", 
                format_currency(df_display['ca_daily'].mean()))
    with col2:
        st.metric(f"CA max ({unit_label})", 
                format_currency(df_display['ca_daily'].max()))
    with col3:
        st.metric(f"CA min ({unit_label})", 
                format_currency(df_display['ca_daily'].min()))


elif selected_graph == ":material/shopping_bag: Nombre de Commandes":
    fig = create_line_chart(
        df_display, 
        x=date_col, 
        y='nb_orders',
        title="Évolution du Nombre de Commandes",
        subtitle=f"Nombre {freq_label}"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Déterminer un label clair pour la fréquence
    if frequency == "Quotidien":
        unit_label = "jour"
    elif frequency == "Hebdomadaire":
        unit_label = "semaine"
    elif frequency == "Mensuel":
        unit_label = "mois"
    else:
        unit_label = "an"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Commandes moyennes par {unit_label}", 
                f"{df_display['nb_orders'].mean():.0f}")
    with col2:
        st.metric(f"Max ({unit_label})", 
                f"{df_display['nb_orders'].max():.0f}")
    with col3:
        st.metric(f"Min ({unit_label})", 
                f"{df_display['nb_orders'].min():.0f}")


elif selected_graph == ":material/report_problem: Taux de Réclamations":
    # Utiliser barres pour les taux
    fig = create_bar_chart(
        df_display,
        x=date_col,
        y='claim_rate',
        title="Évolution du Taux de Réclamations",
        subtitle=f"Moyenne {freq_label} (%)"
    )
    
    # Ajouter ligne objectif à 10%
    fig.add_hline(
        y=10, 
        line_dash="dash", 
        line_color="#f59e0b",
        annotation_text="Objectif <10%",
        annotation_position="right"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Taux Global", f"{kpis_current['claim_rate']:.1f}%")
    with col2:
        st.metric("Montant total des réclamations", format_currency(kpis_current['montant_claims']))
    with col3:
        st.metric("Montant moyen par réclamation", format_currency(kpis_current['montant_claims'] / kpis_current['nb_claims'] if kpis_current['nb_claims'] > 0 else 0))

elif selected_graph == ":material/local_shipping: Taux de Livraison":
    # Utiliser barres pour les taux
    fig = create_bar_chart(
        df_display,
        x=date_col,
        y='delivery_rate',
        title="Évolution du Taux de Livraison Réussie",
        subtitle=f"Moyenne {freq_label}(%)"
    )
    
    # Ajouter ligne objectif à 90%
    fig.add_hline(
        y=90, 
        line_dash="dash", 
        line_color="#10b981",
        annotation_text="Objectif 90%",
        annotation_position="right"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Taux Global", f"{kpis_current['delivery_rate']:.1f}%")
    
st.markdown("---")





