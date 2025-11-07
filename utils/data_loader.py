"""
Module de chargement et préparation des données
"""
import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_all_data():
    """
    Charge tous les fichiers CSV avec gestion d'erreurs
    
    Returns:
        dict: Dictionnaire contenant tous les DataFrames
    """
    data_dir = Path('data')
    
    try:
        # Chargement des fichiers
        orders = pd.read_csv(data_dir / 'orders.csv')
        products = pd.read_csv(data_dir / 'products.csv')
        states_risk = pd.read_csv(data_dir / 'states_risk.csv')
        transport_mode = pd.read_csv(data_dir / 'transport_mode.csv')
        claims = pd.read_csv(data_dir / 'claims.csv')
        customers = pd.read_csv(data_dir / 'customers.csv')
        order_product = pd.read_csv(data_dir / 'order_product.csv')
        order_route_leg = pd.read_csv(data_dir / 'order_route_leg.csv')
        
    except FileNotFoundError as e:
        st.error(f"❌ Fichier manquant : {e}")
        st.info("💡 Assurez-vous que tous les fichiers CSV sont dans le dossier 'data/'")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        st.stop()
    
    # Conversion des dates - Orders
    try:
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        orders['estimated_delivery_date'] = pd.to_datetime(orders['estimated_delivery_date'])
        orders['actual_delivery_date'] = pd.to_datetime(orders['actual_delivery_date'])
    except Exception as e:
        st.warning(f"⚠️ Problème de conversion de dates (orders) : {e}")
    
    # Conversion des dates - Claims
    try:
        if 'claim_date' in claims.columns:
            claims['claim_date'] = pd.to_datetime(claims['claim_date'])
        if 'resolution_date' in claims.columns:
            claims['resolution_date'] = pd.to_datetime(claims['resolution_date'])
    except Exception as e:
        st.warning(f"⚠️ Problème de conversion de dates (claims) : {e}")
    
    # Conversion des dates - Order Route Leg
    try:
        if 'entered_at' in order_route_leg.columns:
            order_route_leg['entered_at'] = pd.to_datetime(order_route_leg['entered_at'])
        if 'exited_at' in order_route_leg.columns:
            order_route_leg['exited_at'] = pd.to_datetime(order_route_leg['exited_at'])
    except Exception as e:
        st.warning(f"⚠️ Problème de conversion de dates (route_leg) : {e}")
    
    # Conversion des dates - Customers
    try:
        if 'registration_date' in customers.columns:
            customers['registration_date'] = pd.to_datetime(customers['registration_date'])
        if 'churn_date' in customers.columns:
            customers['churn_date'] = pd.to_datetime(customers['churn_date'])
    except Exception as e:
        st.warning(f"⚠️ Problème de conversion de dates (customers) : {e}")
    
    return {
        'orders': orders,
        'products': products,
        'states_risk': states_risk,
        'transport_mode': transport_mode,
        'claims': claims,
        'customers': customers,
        'order_product': order_product,
        'order_route_leg': order_route_leg
    }


@st.cache_data
def prepare_main_dataset():
    """
    Prépare le dataset principal avec toutes les jointures et colonnes dérivées
    
    Returns:
        pd.DataFrame: Dataset principal enrichi
    """
    data = load_all_data()
    
    # Dataset principal : orders + transport + customers
    df = data['orders'].copy()
    df = df.merge(data['transport_mode'], on='transport_id', how='left')
    df = df.merge(data['customers'], on='customer_id', how='left')
    
    # Ajouter les claims
    df = df.merge(
        data['claims'][['order_id', 'claim_type', 'claim_status', 'claim_amount', 
                       'refunded_amount', 'resolution_time_days']], 
        on='order_id', 
        how='left'
    )
    
    # Ajouter info produits (agrégées par commande)
    order_products = data['order_product'].merge(
        data['products'], 
        on='product_id', 
        how='left'
    )
    
    product_agg = order_products.groupby('order_id').agg({
        'line_total': 'sum',
        'quantity': 'sum',
        'return_flag': 'any',
        'refund_amount': 'sum',
        'fragility_class': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',
        'theft_attractiveness_score': 'mean',
        'christmas_popularity_multiplier': 'mean'
    }).reset_index()
    
    product_agg.columns = ['order_id', 'product_line_total', 'total_quantity', 
                          'has_return', 'product_refund_amount', 'main_fragility_class',
                          'avg_theft_attractiveness', 'avg_christmas_multiplier']
    
    df = df.merge(product_agg, on='order_id', how='left')
    
    # Ajouter info route (incidents totaux par commande)
    route_agg = data['order_route_leg'].groupby('order_id').agg({
        'vandalism_incidents': 'sum',
        'theft_incident_flag': 'any',
        'distance_km': 'sum',
        'leg_duration_hours': 'sum',
        'state_code': 'count'  # Nombre d'états traversés
    }).reset_index()
    
    route_agg.columns = ['order_id', 'total_vandalism', 'has_theft_incident', 
                        'total_distance_km', 'total_duration_hours', 'nb_states_crossed']
    
    df = df.merge(route_agg, on='order_id', how='left')
    
   
    # ===== GESTION DES VALEURS MANQUANTES =====
    df['claim_amount'] = df['claim_amount'].fillna(0)
    df['refunded_amount'] = df['refunded_amount'].fillna(0)
    df['product_refund_amount'] = df['product_refund_amount'].fillna(0)
    df['total_vandalism'] = df['total_vandalism'].fillna(0)
    df['has_theft_incident'] = df['has_theft_incident'].fillna(False)
    df['total_distance_km'] = df['total_distance_km'].fillna(0)
    df['total_duration_hours'] = df['total_duration_hours'].fillna(0)
    df['nb_states_crossed'] = df['nb_states_crossed'].fillna(0)
    df['resolution_time_days'] = df['resolution_time_days'].fillna(0)
    
    # ===== COLONNES DÉRIVÉES =====
    
    # Indicateurs booléens
    df['is_christmas'] = df['seasonal_period'] == 'Christmas'
    df['is_delivered'] = df['delivery_status'].str.lower() == 'delivered'
    df['has_claim'] = df['claim_flag'] == True
    df['is_paid'] = df['payment_status'] == 'Paid'
    
    # Dates
    df['order_year'] = df['order_date'].dt.year
    df['order_month'] = df['order_date'].dt.month
    df['order_week'] = df['order_date'].dt.isocalendar().week
    df['order_day'] = df['order_date'].dt.day
    df['order_weekday'] = df['order_date'].dt.dayofweek
    df['order_quarter'] = df['order_date'].dt.quarter
    
    # Délai de livraison
    df['delivery_delay_days'] = (
        df['actual_delivery_date'] - df['estimated_delivery_date']
    ).dt.days
    df['is_late'] = df['delivery_delay_days'] > 0
    
    # Catégories de valeur de commande
    df['order_value_category'] = pd.cut(
        df['total_amount'],
        bins=[0, 50, 100, 200, 500, float('inf')],
        labels=['<50€', '50-100€', '100-200€', '200-500€', '>500€']
    )
    
    # Vitesse moyenne de livraison (km/h)
    df['avg_speed_kmh'] = df['total_distance_km'] / df['total_duration_hours'].replace(0, 1)
    
    # Coût de transport estimé
    df['transport_cost_estimate'] = df['total_distance_km'] * df['cost_per_km']
    
    # Émissions CO2 estimées
    df['co2_emission_estimate'] = df['total_distance_km'] * df['co2_emission_per_km']
    
    # Pertes totales
    df['total_loss'] = df['claim_amount']
    
    # Indicateur de risque global
    df['has_any_incident'] = (df['has_theft_incident']) | (df['total_vandalism'] > 0)
    
    # Catégorie de risque de vol
    df['theft_risk_category'] = pd.cut(
        df['avg_theft_attractiveness'],
        bins=[0, 3, 6, 8, 10],
        labels=['Faible', 'Moyen', 'Élevé', 'Très Élevé'],
        include_lowest=True
    )
    
    return df


@st.cache_data
def get_kpi_metrics(df):
    """
    Calcule les KPI principaux du dashboard
    
    Args:
        df: DataFrame principal (résultat de prepare_main_dataset())
    
    Returns:
        dict: Dictionnaire de KPI
    """
    # Filtrer sur les commandes livrées pour le CA
    delivered = df[df['is_delivered'] == True]
    
    kpis = {
        # CA et volume
        'ca_total': df['total_amount'].sum(),
        'nb_orders': len(df),
        'nb_delivered': len(delivered),
        'aov': df['total_amount'].mean(),
        
        # Taux de performance
        'delivery_rate': (df['is_delivered'].mean() * 100),
        'claim_rate': (df['has_claim'].mean() * 100),
        'late_delivery_rate': (df['is_late'].mean() * 100) if 'is_late' in df.columns else 0,
        
        # Pertes et incidents
        'nb_claims': df['has_claim'].sum(),
        'montant_claims': df['claim_amount'].sum(),
        'total_losses': df['total_loss'].sum(),
        'nb_theft_incidents': df['has_theft_incident'].sum(),
        'nb_vandalism_incidents': df['total_vandalism'].sum(),
        
        # Transport
        'avg_distance': df['total_distance_km'].mean(),
        'avg_duration': df['total_duration_hours'].mean(),
        'total_co2': df['co2_emission_estimate'].sum(),
        'avg_transport_cost': df['transport_cost_estimate'].mean(),
        
        # Clients
        'nb_customers': df['customer_id'].nunique(),
        'nb_premium': df[df['subscription_type'] == 'Premium']['customer_id'].nunique() if 'subscription_type' in df.columns else 0,
       
    }
    
    return kpis



# page reclamation:


@st.cache_data
def get_claims_kpi_metrics(df_orders, df_customers, df_claims, start_date, end_date):
    """
    Calcule les KPI pour la page Réclamations & Satisfaction Client
    
    Args:
        df_orders: DataFrame des commandes (DÉJÀ filtré par order_date)
        df_customers: DataFrame des clients (complet)
        df_claims: DataFrame des réclamations (DÉJÀ filtré par claim_date)
        start_date: Date de début (date ou Timestamp)
        end_date: Date de fin (date ou Timestamp)
    
    Returns:
        dict: Dictionnaire contenant les 3 KPI + métriques complémentaires
    """
    # Convertir les dates
    df_customers = df_customers.copy()
    df_customers['churn_date'] = pd.to_datetime(df_customers['churn_date'], errors='coerce')
    df_customers['registration_date'] = pd.to_datetime(df_customers['registration_date'])
    
    # === KPI 1 : Taux de Réclamations (DURANT la période) ===
    total_orders = len(df_orders)
    
    # Compter les commandes ayant au moins 1 réclamation DANS la période
    orders_with_claims_in_period = df_claims['order_id'].nunique()
    
    claim_rate = (orders_with_claims_in_period / total_orders * 100) if total_orders > 0 else 0
    
    # === BASE DE CALCUL : Clients actifs au début de la période ===
    active_at_start = df_customers[
        (df_customers['registration_date'] <= pd.to_datetime(start_date)) &
        (
            (df_customers['churn_status'] != 'Churned') | 
            (df_customers['churn_date'] > pd.to_datetime(start_date))
        )
    ]
    
    total_customers_at_start = len(active_at_start)
    
    # === KPI 2 : Taux de Churn (clients qui ont churné DURANT la période) ===
    churned_in_period = df_customers[
        (df_customers['churn_status'] == 'Churned') &
        (df_customers['churn_date'] >= pd.to_datetime(start_date)) &
        (df_customers['churn_date'] <= pd.to_datetime(end_date))
    ]
    
    nb_churned_in_period = len(churned_in_period)
    churn_rate = (nb_churned_in_period / total_customers_at_start * 100) if total_customers_at_start > 0 else 0
    
    # === KPI 3 : Clients Actifs (au début de la période) ===
    active_customers = total_customers_at_start  # ✅ MÊME BASE QUE LE CHURN !
    
    # === Métriques complémentaires ===
    total_claims = len(df_claims)
    avg_resolution_time = df_claims['resolution_time_days'].mean() if total_claims > 0 else 0
    total_claim_amount = df_claims['claim_amount'].sum()
    total_refunded = df_claims['refunded_amount'].sum()
    
    return {
        # KPI principaux
        'claim_rate': claim_rate,
        'churn_rate': churn_rate,
        'active_customers': active_customers,
        
        # Métriques complémentaires
        'total_orders': total_orders,
        'orders_with_claims': orders_with_claims_in_period,
        'total_customers': total_customers_at_start,
        'churned_customers': nb_churned_in_period,
        'total_claims': total_claims,
        'avg_resolution_time': avg_resolution_time,
        'total_claim_amount': total_claim_amount,
        'total_refunded': total_refunded
    }