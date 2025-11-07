import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ===== TIMELINE DUAL AXIS =====
def create_dual_axis_timeline(df, date_col='order_date', 
                               metric1='nb_orders', metric1_name='Commandes',
                               metric2='theft_rate', metric2_name='Taux de vol (%)',
                               christmas_col='is_christmas'):
    """
    Timeline avec double axe Y : volume (bars) et taux (line)
    Utile pour : commandes vs taux de vol, livraisons vs réclamations
    """
    fig = go.Figure()
    
    # Barres
    fig.add_trace(go.Bar(
        x=df[date_col],
        y=df[metric1],
        name=metric1_name,
        marker_color='#055e82',
        yaxis='y'
    ))
    
    # Ligne
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[metric2],
        name=metric2_name,
        line=dict(color='#ffd447', width=3),
        yaxis='y2'
    ))
    
    # Zone Noël
    if christmas_col in df.columns:
        christmas_dates = df[df[christmas_col] == True][date_col]
        if len(christmas_dates) > 0:
            fig.add_vrect(
                x0=christmas_dates.min(),
                x1=christmas_dates.max(),
                fillcolor="#fee2e2",
                opacity=0.3,
                layer="below",
                line_width=0,
                annotation_text="Période Noël",
                annotation_position="top left"
            )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis=dict(title=metric1_name, side='left'),
        yaxis2=dict(title=metric2_name, overlaying='y', side='right'),
        hovermode='x unified',
        height=500,
        font=dict(family="Inter")
    )
    
    return fig

# ===== COMPARAISON MODES TRANSPORT =====
def create_transport_comparison(transport_stats, metric='delivery_rate',
                                 christmas_col='is_christmas'):
    """
    Barres groupées : performance par mode (Noël vs Normal)
    Utile pour : comparer road/train/plane/last-mile
    """
    christmas_data = transport_stats[transport_stats[christmas_col] == True]
    normal_data = transport_stats[transport_stats[christmas_col] == False]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Période Normale',
        x=normal_data['transport_type'],
        y=normal_data[metric] * 100,
        marker_color='#055e82',
        text=[f"{v:.1f}%" for v in normal_data[metric] * 100],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Période Noël',
        x=christmas_data['transport_type'],
        y=christmas_data[metric] * 100,
        marker_color='#dc2626',
        text=[f"{v:.1f}%" for v in christmas_data[metric] * 100],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Performance par mode de transport",
        xaxis_title="Mode",
        yaxis_title=metric.replace('_', ' ').title() + " (%)",
        barmode='group',
        height=450,
        yaxis=dict(range=[0, 105]),
        font=dict(family="Inter")
    )
    
    return fig

# ===== SCATTER RISQUE =====
def create_risk_scatter(states_risk_df, x='avg_distance', y='theft_rate',
                        size='nb_orders', color='transport_type'):
    """
    Scatter avec bulles : identifier hotspots risque
    Utile pour : États à risque, modes à problèmes
    """
    fig = px.scatter(
        states_risk_df,
        x=x,
        y=y,
        size=size,
        color=color,
        hover_data=['state_name', 'month'],
        labels={
            x: x.replace('_', ' ').title(),
            y: y.replace('_', ' ').title(),
            color: 'Mode de transport'
        },
        title="Hotspots de risque : distance vs incidents",
        height=500,
        color_discrete_map={
            'road': '#055e82',
            'train': '#2b3d50',
            'plane': '#ffd447',
            'last_mile': '#dc2626'
        }
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(font=dict(family="Inter"))
    
    return fig

# ===== GAUGE KPI =====
def create_gauge(value, title, max_value=100, threshold=80, color="#055e82"):
    """Jauge pour KPI principaux"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18, 'family': 'Inter'}},
        number={'suffix': "%", 'font': {'size': 32, 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, max_value], 'ticksuffix': "%"},
            'bar': {'color': color},
            'steps': [
                {'range': [0, threshold], 'color': "#fee2e2"},
                {'range': [threshold, max_value], 'color': "#d1fae5"}
            ],
            'threshold': {
                'line': {'color': "#dc2626", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ===== HEATMAP ÉTATS =====
def create_state_heatmap(states_df, metric='theft_rate'):
    """
    Heatmap pour visualiser risque par État
    """
    pivot = states_df.pivot_table(
        values=metric,
        index='state_name',
        columns='month',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Reds',
        text=pivot.values,
        texttemplate='%{text:.1f}%',
        textfont={"size": 10},
        colorbar=dict(title="Taux de vol (%)")
    ))
    
    fig.update_layout(
        title=f"Risque par État et Mois",
        xaxis_title="Mois",
        yaxis_title="État",
        height=600,
        font=dict(family="Inter")
    )
    
    return fig

############################################
###########ADVENCED_VIZ.PY##################
#############################################

"""
Visualisations avancées pour le dashboard e-commerce
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ===== HEATMAP INCIDENTS =====
def create_incident_heatmap(df, row_dim='transport_type', col_dim='is_christmas',
                            metric='theft_count', title="Matrice d'Incidents"):
    """
    Heatmap générique pour croiser 2 dimensions
    
    Args:
        df: DataFrame
        row_dim: Dimension en lignes (ex: transport, state)
        col_dim: Dimension en colonnes (ex: is_christmas, month)
        metric: Métrique à agréger (ex: theft_count, vandalism_count)
    """
    pivot = df.pivot_table(
        index=row_dim,
        columns=col_dim,
        values=metric,
        aggfunc='sum',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Reds',
        text=pivot.values,
        texttemplate='%{text:.0f}',
        textfont={"size": 12},
        hovertemplate='%{y}<br>%{x}: %{z:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        height=400,
        xaxis_title=col_dim.replace('_', ' ').title(),
        yaxis_title=row_dim.replace('_', ' ').title(),
        font=dict(family="Inter")
    )
    
    return fig

# ===== RADAR RISQUE =====
def create_risk_radar(risk_dimensions, title="Profil de Risque"):
    """
    Radar chart pour visualiser profil multi-critères
    
    Args:
        risk_dimensions: Dict {'Critère': valeur_0_100}
        title: Titre du graphique
    
    Exemple:
        risk_dimensions = {
            'Vols': 75,
            'Vandalisme': 45,
            'Trafic': 60,
            'Météo': 30
        }
    """
    categories = list(risk_dimensions.keys())
    values = list(risk_dimensions.values())
    
    # Fermer le polygone
    values += values[:1]
    categories += categories[:1]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(5, 94, 130, 0.2)',
        line=dict(color='#055e82', width=2),
        name='Risque'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            )
        ),
        showlegend=False,
        title=title,
        height=400,
        font=dict(family="Inter")
    )
    
    return fig

# ===== WATERFALL ÉCONOMIQUE =====
def create_economic_waterfall(economic_impact):
    """
    Graphique cascade pour décomposer l'impact économique
    
    Args:
        economic_impact: Dict avec clés:
            - 'potential': Revenu potentiel
            - 'lost_revenue': Pertes (vols)
            - 'claims': Coûts réclamations
            - 'refunds': Remboursements
            - 'actual': Revenu réel
    """
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Revenu Potentiel", "Pertes Vols", "Coûts Réclamations", 
           "Remboursements", "Revenu Net"],
        textposition="outside",
        text=[
            f"€{economic_impact['potential']/1000:.0f}K",
            f"-€{economic_impact['lost_revenue']/1000:.0f}K",
            f"-€{economic_impact['claims']/1000:.0f}K",
            f"-€{economic_impact['refunds']/1000:.0f}K",
            f"€{economic_impact['actual']/1000:.0f}K"
        ],
        y=[
            economic_impact['potential'],
            -economic_impact['lost_revenue'],
            -economic_impact['claims'],
            -economic_impact['refunds'],
            economic_impact['actual']
        ],
        connector={"line": {"color": "#2b3d50"}},
        decreasing={"marker": {"color": "#dc2626"}},
        increasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#055e82"}}
    ))
    
    fig.update_layout(
        title="Impact Économique - Décomposition",
        yaxis_title="Montant (€)",
        height=450,
        showlegend=False,
        font=dict(family="Inter")
    )
    
    return fig

# ===== JAUGE PERFORMANCE =====
def create_performance_gauge(value, metric_name="Performance", 
                             target=90, unit="%"):
    """
    Jauge avec seuils de performance (Bon/Attention/Critique)
    
    Args:
        value: Valeur actuelle
        metric_name: Nom de la métrique
        target: Cible à atteindre
        unit: Unité d'affichage
    """
    # Déterminer statut
    if value >= target:
        color = "#10b981"
        status = "Bon"
    elif value >= target - 10:
        color = "#fbbf24"
        status = "Attention"
    else:
        color = "#dc2626"
        status = "Critique"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={
            'text': f"<b>{metric_name}</b><br><span style='font-size:0.8em; color:gray'>{status}</span>"
        },
        delta={'reference': target, 'suffix': f' {unit}'},
        number={'suffix': unit, 'font': {'size': 40, 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.75},
            'steps': [
                {'range': [0, target-15], 'color': '#fee2e2'},
                {'range': [target-15, target-5], 'color': '#fef3c7'},
                {'range': [target-5, 100], 'color': '#d1fae5'}
            ],
            'threshold': {
                'line': {'color': "#dc2626", 'width': 4},
                'thickness': 0.75,
                'value': target
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family="Inter")
    )
    
    return fig

# ===== COMPARAISON MULTI-RADAR =====
def create_multi_radar(data_dict, title="Comparaison Multi-critères"):
    """
    Radar avec plusieurs entités à comparer
    
    Args:
        data_dict: Dict de dicts
            {
                'Road': {'Coût': 70, 'Délai': 60, 'CO2': 50, 'Risque': 80},
                'Train': {'Coût': 50, 'Délai': 70, 'CO2': 30, 'Risque': 90}
            }
    """
    fig = go.Figure()
    
    colors = ['#055e82', '#ffd447', '#2b3d50', '#10b981']
    
    for i, (entity, metrics) in enumerate(data_dict.items()):
        categories = list(metrics.keys()) + [list(metrics.keys())[0]]
        values = list(metrics.values()) + [list(metrics.values())[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=entity,
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=title,
        height=500,
        font=dict(family="Inter")
    )
    
    return fig