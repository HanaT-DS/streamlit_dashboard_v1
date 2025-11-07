import pandas as pd
import streamlit as st

# === FORMATAGE ===
def format_currency(value, decimals=0):
    if value >= 1e6:
        return f"{value/1e6:.{decimals}f}M$"
    elif value >= 1e3:
        return f"{value/1e3:.{decimals}f}K$"
    return f"{value:.{decimals}f}$"

def format_percentage(value, decimals=1):
    return f"{value:.{decimals}f}%"

def format_number(value, decimals=0):
    if decimals == 0:
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.{decimals}f}".replace(",", " ")

# === CALCULS ===
def safe_divide(numerator, denominator, default=0):
    return numerator / denominator if denominator != 0 else default

def calculate_growth_rate(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

# === TÉLÉCHARGEMENT ===
def add_download_button(df, filename="export.csv", label="📥 Télécharger CSV"):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv'
    )

# === FILTRAGE ===
def filter_by_date_range(df, start_date, end_date, date_column='date'):
    mask = (df[date_column] >= pd.to_datetime(start_date)) & \
           (df[date_column] <= pd.to_datetime(end_date))
    return df[mask]

# Si vous avez des métriques avec comparaison période précédente
def calculate_delta(current, previous):
    """Retourne la variation en valeur absolue et %"""
    delta_abs = current - previous
    delta_pct = (delta_abs / previous * 100) if previous != 0 else 0
    return delta_abs, delta_pct