# pages/reclamations.py
import streamlit as st
import pandas as pd
from pathlib import Path

from utils.data_loader import prepare_main_dataset, load_all_data
from utils.helpers import calculate_growth_rate
from utils.sidebar import render_sidebar, apply_filters

# ========= CONFIGURATION =========
logo_path = Path(__file__).parent.parent / "assets" / "logo1.png"
st.set_page_config(
    page_title="Réclamations & Satisfaction",
    page_icon=str(logo_path),
    layout="wide"
)

# CSS (même thème que tes autres pages)
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ========= CHARGEMENT DES DONNÉES =========
@st.cache_data
def load_data():
    data = load_all_data()
    df_orders = prepare_main_dataset()
    df_customers = data.get('customers', pd.DataFrame()).copy()
    df_claims_full = data.get('claims', pd.DataFrame()).copy()

    # conversions robustes
    if not df_claims_full.empty:
        for col in ('claim_date', 'resolution_date'):
            if col in df_claims_full.columns:
                df_claims_full[col] = pd.to_datetime(df_claims_full[col], errors='coerce')
    if not df_customers.empty:
        for col in ('registration_date', 'churn_date'):
            if col in df_customers.columns:
                df_customers[col] = pd.to_datetime(df_customers[col], errors='coerce')

    return df_orders, df_customers, df_claims_full

df_full, df_customers, df_claims_full = load_data()

# ========= SIDEBAR & FILTRES =========
filters = render_sidebar(df_full)      # -> {start_date, end_date, transport_filter, state_filter}
df = apply_filters(df_full, filters)   # DataFrame commandes filtré

# ========= KPI: FONCTION DE CALCUL =========
def compute_claims_kpis(
    df_orders_filt: pd.DataFrame,
    df_customers_all: pd.DataFrame,
    start_date, end_date
) -> dict:
    """
    - Taux de réclamation = (# commandes avec has_claim) / (# commandes filtrées) × 100
    - Nb clients (périmètre) = clients uniques ayant passé commande dans df_orders_filt
    - Taux de churn (période) = (# clients de ce périmètre avec churn_date ∈ [start_date, end_date]) / (# clients du périmètre) × 100
    - Clients actifs (période) = clients du périmètre qui n'ont PAS churn pendant la période
    """
    dff = df_orders_filt.copy()

    # 1) Taux de réclamation
    n_orders = len(dff)
    has_claim = dff['has_claim'] if 'has_claim' in dff.columns else pd.Series(False, index=dff.index)
    n_orders_with_claims = int(has_claim.sum())
    claim_rate = (n_orders_with_claims / n_orders * 100) if n_orders > 0 else 0.0

    # 2) Ensemble des clients du périmètre
    customers_in_scope = set(dff['customer_id'].dropna().unique()) if 'customer_id' in dff.columns else set()
    n_clients = len(customers_in_scope)

    # 3) Churn pendant la période
    if n_clients > 0 and not df_customers_all.empty and 'churn_date' in df_customers_all.columns:
        cust_scope = df_customers_all[df_customers_all['customer_id'].isin(customers_in_scope)].copy()
        churned_in_period = int(
            cust_scope.loc[
                cust_scope['churn_date'].notna() &
                (cust_scope['churn_date'].dt.date >= start_date) &
                (cust_scope['churn_date'].dt.date <= end_date),
                'customer_id'
            ].nunique()
        )
    else:
        churned_in_period = 0

    churn_rate = (churned_in_period / n_clients * 100) if n_clients > 0 else 0.0

    # 4) Clients actifs (période) = clients du périmètre non churnés pendant la période
    active_customers_period = max(n_clients - churned_in_period, 0)

    return {
        'claim_rate': round(claim_rate, 2),
        'orders_with_claims': n_orders_with_claims,
        'unique_customers': n_clients,
        'churn_rate': round(churn_rate, 2),
        'churned_customers': churned_in_period,
        'active_customers_period': active_customers_period
    }

# ========= KPI PÉRIODE COURANTE =========
current_start, current_end = filters['start_date'], filters['end_date']
kpis_current = compute_claims_kpis(
    df_orders_filt=df,
    df_customers_all=df_customers,
    start_date=current_start,
    end_date=current_end
)

# ========= PÉRIODE PRÉCÉDENTE (mêmes filtres transport/états) =========
period_days = (current_end - current_start).days
prev_start = current_start - pd.Timedelta(days=period_days + 1)
prev_end   = current_start - pd.Timedelta(days=1)

df_prev = df_full[
    (df_full['order_date'].dt.date >= prev_start) &
    (df_full['order_date'].dt.date <= prev_end)
]
df_prev = apply_filters(df_prev, {
    'start_date': prev_start,
    'end_date': prev_end,
    'transport_filter': filters['transport_filter'],
    'state_filter': filters['state_filter']
})

kpis_previous = compute_claims_kpis(
    df_orders_filt=df_prev,
    df_customers_all=df_customers,
    start_date=prev_start,
    end_date=prev_end
) if len(df_prev) > 0 else None

# ========= DELTAS =========
if kpis_previous:
    # baisse = positif pour ces deux taux
    delta_claim = kpis_current['claim_rate'] - kpis_previous['claim_rate']
    delta_churn = kpis_current['churn_rate'] - kpis_previous['churn_rate']
    # ✅ évolution Clients actifs (période) vs période précédente
    delta_active = calculate_growth_rate(
        kpis_current['active_customers_period'],
        kpis_previous['active_customers_period']
    )
else:
    delta_claim = delta_churn = 0
    delta_active = 0

# ========= HEADER =========
st.title("Réclamations & Satisfaction Client")
st.markdown("---")

# ========= KPI CARDS =========
st.subheader("KPI Principaux")
col1, col2, col3 = st.columns(3)

# KPI 1 : Taux de Réclamations
with col1:
    delta_class = 'positive' if delta_claim <= 0 else 'negative'
    delta_symbol = '↗' if delta_claim >= 0 else '↘'
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Taux de Réclamations</div>
        <div class="kpi-value">{kpis_current['claim_rate']:.1f}%</div>
        <div class="kpi-divider"></div>
        <div class="kpi-description">{kpis_current['orders_with_claims']:,} commandes réclamées</div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_claim):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# KPI 2 : Taux de Churn
with col2:
    delta_class = 'positive' if delta_churn <= 0 else 'negative'
    delta_symbol = '↗' if delta_churn >= 0 else '↘'
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Taux de Churn</div>
        <div class="kpi-value">{kpis_current['churn_rate']:.1f}%</div>
        <div class="kpi-divider"></div>
        <div class="kpi-description">{kpis_current['churned_customers']:,} clients perdus</div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_churn):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# KPI 3 : Clients Actifs (période) + delta
with col3:
    delta_class = 'positive' if delta_active >= 0 else 'negative'
    delta_symbol = '↗' if delta_active >= 0 else '↘'
    st.markdown(f"""
    <div class="kpi-card-gradient">
        <div class="kpi-label">Clients Actifs</div>
        <div class="kpi-value">{kpis_current['active_customers_period']:,}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-delta {delta_class}">
            {delta_symbol} {abs(delta_active):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


#################################"
# ##############################


# Import de la fonction pie chart depuis charts
from utils.charts import create_pie_chart

# À placer une seule fois, au-dessus des graphes
filtered_order_ids = df['order_id'].unique()
df_claims = df_claims_full[
    (df_claims_full['order_id'].isin(filtered_order_ids)) &
    (df_claims_full['claim_date'].dt.date.between(filters['start_date'], filters['end_date']))
].copy()

st.subheader("Répartition des Réclamations par Type")

claims_type = (
    df_claims.assign(claim_type=df_claims.get('claim_type').fillna('Unknown') if 'claim_type' in df_claims.columns else 'Unknown')
             .groupby('claim_type')
             .size()
             .reset_index(name='count')
             .sort_values('count', ascending=False)
)

if len(claims_type) > 0:
    # Utiliser create_pie_chart au lieu de px.pie
    fig_donut = create_pie_chart(
        claims_type,
        names='claim_type',
        values='count',
        
        hole=0.5
    )
    
    st.plotly_chart(fig_donut, use_container_width=True)
    
    # Métriques complémentaires (optionnel)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Types Différents", len(claims_type))
    with col2:
        st.metric("Total Réclamations", claims_type['count'].sum())
    with col3:
        most_common = claims_type.iloc[0]
        st.metric("Type Principal", f"{most_common['claim_type']}", f"{most_common['count']} cas")
else:
    st.info("📭 Aucune réclamation sur la période sélectionnée.")


