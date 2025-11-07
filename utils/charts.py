"""
Visualisations professionnelles adaptées à la charte graphique
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ===== PALETTE DE COULEURS (VOTRE CHARTE) =====
COLORS = {
    'primary': '#055e82',      # Accent bleu canard
    'secondary': '#ffd447',    # Jaune
    'text': '#2b3d50',         # Texte principal
    'success': '#10b981',      # Vert
    'warning': '#f59e0b',      # Orange
    'error': '#ef4444',        # Rouge
    'gray': ['#fafafa', '#f3f4f6', '#e5e7eb', '#d1d5db', '#9ca3af', '#6b7280'],
    'chart_palette': ['#055e82', '#ffd447', '#2b3d50', '#10b981', '#f59e0b', '#ef4444']
}

# ===== LAYOUT PAR DÉFAUT (THÈME CLAIR) =====
DEFAULT_LAYOUT = {
    'paper_bgcolor': '#ffffff',
    'plot_bgcolor': '#fafafa',
    'font': {
        'family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        'size': 13,
        'color': '#6b7280'
    },
    'margin': {'l': 60, 'r': 40, 't': 80, 'b': 60},
    'hovermode': 'x unified',
    'hoverlabel': {
        'bgcolor': '#2b3d50',
        'font': {'size': 13, 'color': '#ffffff'},
        'bordercolor': '#055e82'
    },
    'xaxis': {
        'gridcolor': '#e5e7eb',
        'linecolor': '#d1d5db',
        'zerolinecolor': '#d1d5db',
        'tickfont': {'size': 12, 'color': '#6b7280'},
        'title': {'font': {'size': 13, 'color': '#2b3d50'}}
    },
    'yaxis': {
        'gridcolor': '#e5e7eb',
        'linecolor': '#d1d5db',
        'zerolinecolor': '#d1d5db',
        'tickfont': {'size': 12, 'color': '#6b7280'},
        'title': {'font': {'size': 13, 'color': '#2b3d50'}}
    }
}

def hex_to_rgba(hex_color, alpha=0.25):
    """Convertit hex en rgba"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'

# ===== GRAPHIQUE EN LIGNE =====
def create_line_chart(df, x, y, title="", subtitle="", color_col=None, show_markers=True):
    """
    Graphique en ligne propre
    
    Args:
        df: DataFrame
        x: Colonne axe X (dates)
        y: Colonne(s) axe Y (string ou liste)
        title: Titre
        subtitle: Sous-titre
        color_col: Colonne pour grouper par couleur
        show_markers: Afficher les points
    """
    fig = go.Figure()
    
    y_cols = [y] if isinstance(y, str) else y
    
    for idx, y_col in enumerate(y_cols):
        if color_col and color_col in df.columns:
            for color_idx, (group_name, group_df) in enumerate(df.groupby(color_col)):
                fig.add_trace(go.Scatter(
                    x=group_df[x],
                    y=group_df[y_col],
                    name=str(group_name),
                    mode='lines+markers' if show_markers else 'lines',
                    line={
                        'color': COLORS['chart_palette'][color_idx % len(COLORS['chart_palette'])],
                        'width': 2.5
                    },
                    marker={'size': 6 if show_markers else 0},
                    hovertemplate='%{y:,.2f}<extra></extra>'
                ))
        else:
            fig.add_trace(go.Scatter(
                x=df[x],
                y=df[y_col],
                name=y_col if len(y_cols) > 1 else '',
                mode='lines+markers' if show_markers else 'lines',
                line={
                    'color': COLORS['chart_palette'][idx],
                    'width': 2.5
                },
                marker={'size': 6 if show_markers else 0},
                hovertemplate='%{y:,.2f}<extra></extra>'
            ))
    
    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            'text': f"<b>{title}</b><br><sub>{subtitle}</sub>" if subtitle else f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#2b3d50'},
            'x': 0,
            'xanchor': 'left'
        },
        showlegend=bool(color_col or len(y_cols) > 1),
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'left',
            'x': 0
        },
        height=450
    )
    
    return fig

# ===== GRAPHIQUE EN BARRES =====
def create_bar_chart(df, x, y, title="", subtitle="", color=None, horizontal=False):
    """
    Graphique en barres
    
    Args:
        df: DataFrame
        x: Catégories
        y: Valeurs
        title: Titre
        subtitle: Sous-titre
        color: Couleur fixe ou colonne pour mapping
        horizontal: Barres horizontales
    """
    if color and color in df.columns:
        color_values = df[color]
    else:
        color_values = [COLORS['primary']] * len(df)
    
    if horizontal:
        fig = go.Figure(go.Bar(
            y=df[x],
            x=df[y],
            orientation='h',
            marker={'color': color_values, 'line': {'width': 0}},
            hovertemplate='%{x:,.0f}<extra></extra>'
        ))
    else:
        fig = go.Figure(go.Bar(
            x=df[x],
            y=df[y],
            marker={'color': color_values, 'line': {'width': 0}},
            hovertemplate='%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            'text': f"<b>{title}</b><br><sub>{subtitle}</sub>" if subtitle else f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#2b3d50'},
            'x': 0,
            'xanchor': 'left'
        },
        showlegend=False,
        height=450,
        bargap=0.15
    )
    
    return fig

# ===== AIRES EMPILÉES =====
def create_area_chart(df, x, y, title="", subtitle="", stacked=False):
    """Aires empilées ou simples"""
    fig = go.Figure()
    
    y_cols = [y] if isinstance(y, str) else y
    
    for idx, y_col in enumerate(y_cols):
        color = COLORS['chart_palette'][idx % len(COLORS['chart_palette'])]
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y_col],
            name=y_col,
            mode='lines',
            line={'width': 0},
            fillcolor=hex_to_rgba(color, 0.3),
            fill='tonexty' if stacked and idx > 0 else 'tozeroy',
            stackgroup='one' if stacked else None,
            hovertemplate='%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            'text': f"<b>{title}</b><br><sub>{subtitle}</sub>" if subtitle else f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#2b3d50'},
            'x': 0,
            'xanchor': 'left'
        },
        showlegend=len(y_cols) > 1,
        height=450
    )
    
    return fig

# ===== BARRES GROUPÉES =====
def create_comparison_chart(df, categories, metrics, title="", subtitle=""):
    """Barres groupées pour comparer plusieurs métriques"""
    fig = go.Figure()
    
    for idx, metric in enumerate(metrics):
        fig.add_trace(go.Bar(
            name=metric,
            x=df[categories],
            y=df[metric],
            marker={'color': COLORS['chart_palette'][idx % len(COLORS['chart_palette'])]},
            hovertemplate='%{y:,.1f}<extra></extra>'
        ))
    
    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            'text': f"<b>{title}</b><br><sub>{subtitle}</sub>" if subtitle else f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#2b3d50'},
            'x': 0,
            'xanchor': 'left'
        },
        barmode='group',
        showlegend=True,
        height=450,
        bargap=0.15
    )
    
    return fig

# ===== STYLE POUR DATAFRAME (À UTILISER AVEC st.dataframe) =====
def get_dataframe_style():
    """
    Retourne un dictionnaire de style pour st.dataframe
    
    Utilisation:
        st.dataframe(df.style.set_properties(**get_dataframe_style()))
    """
    return {
        'background-color': '#fafafa',
        'color': '#2b3d50',
        'border-color': '#e5e7eb',
        'font-family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        'font-size': '13px'
    }

def style_dataframe(df, highlight_max=None, highlight_min=None):
    """
    Style un DataFrame avec la charte graphique
    
    Args:
        df: DataFrame à styler
        highlight_max: Liste de colonnes où surligner le max en vert
        highlight_min: Liste de colonnes où surligner le min en rouge
    
    Returns:
        Styled DataFrame
    
    Utilisation:
        st.dataframe(style_dataframe(df, highlight_max=['CA', 'Orders']))
    """
    styled = df.style
    
    # Style de base
    styled = styled.set_properties(**{
        'background-color': '#ffffff',
        'color': '#2b3d50',
        'border': '1px solid #e5e7eb',
        'font-family': 'Inter, sans-serif',
        'font-size': '13px',
        'text-align': 'left',
        'padding': '8px'
    })
    
    # Style header
    styled = styled.set_table_styles([
        {
            'selector': 'th',
            'props': [
                ('background-color', '#055e82'),
                ('color', '#ffffff'),
                ('font-weight', 'bold'),
                ('text-align', 'left'),
                ('padding', '10px'),
                ('border', '1px solid #044a63')
            ]
        },
        {
            'selector': 'tr:hover',
            'props': [
                ('background-color', '#f3f4f6')
            ]
        }
    ])
    
    # Surligner max en vert
    if highlight_max:
        for col in highlight_max:
            if col in df.columns:
                styled = styled.highlight_max(subset=[col], color='#d1fae5')
    
    # Surligner min en rouge
    if highlight_min:
        for col in highlight_min:
            if col in df.columns:
                styled = styled.highlight_min(subset=[col], color='#fee2e2')
    
    return styled

############################################""
# ===== GRAPHIQUE EN CAMEMBERT (PIE CHART) =====
def create_pie_chart(df, names, values, title="", subtitle="", hole=0):
    """
    Graphique en camembert (pie chart) ou donut
    
    Args:
        df: DataFrame
        names: Colonne contenant les labels
        values: Colonne contenant les valeurs
        title: Titre
        subtitle: Sous-titre
        hole: Taille du trou central (0=pie, 0.4=donut)
    
    Returns:
        Figure Plotly
    
    Exemple:
        fig = create_pie_chart(df, names='transport_type', values='orders', 
                               title="Répartition par Mode", hole=0.4)
    """
    fig = go.Figure(data=[go.Pie(
        labels=df[names],
        values=df[values],
        hole=hole,
        marker={
            'colors': COLORS['chart_palette'],
            'line': {'color': '#ffffff', 'width': 2}
        },
        textposition='inside',
        textinfo='label+percent',
        textfont={'size': 13, 'color': '#ffffff', 'family': 'Inter'},
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>',
        pull=[0.05] * len(df)  # Légère séparation des parts
    )])
    
    fig.update_layout(
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font={
            'family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            'size': 13,
            'color': '#6b7280'
        },
        title={
            'text': f"<b>{title}</b><br><sub>{subtitle}</sub>" if subtitle else f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#2b3d50'},
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        legend={
            'orientation': 'v',
            'yanchor': 'middle',
            'y': 0.5,
            'xanchor': 'left',
            'x': 1.05,
            'bgcolor': 'rgba(255, 255, 255, 0.8)',
            'bordercolor': '#e5e7eb',
            'borderwidth': 1
        },
        margin={'l': 40, 'r': 180, 't': 80, 'b': 40},
        height=450,
        hoverlabel={
            'bgcolor': '#2b3d50',
            'font': {'size': 13, 'color': '#ffffff'},
            'bordercolor': '#055e82'
        }
    )
    
    # Ajouter texte central pour donut
    if hole > 0:
        total = df[values].sum()
        fig.add_annotation(
            text=f"<b>Total</b><br>{total:,.0f}",
            x=0.5, y=0.5,
            font={'size': 16, 'color': '#2b3d50', 'family': 'Inter'},
            showarrow=False
        )
    
    return fig