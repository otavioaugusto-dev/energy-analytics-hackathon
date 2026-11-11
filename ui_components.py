"""
Componentes de UI reutilizáveis para o ReEnergia.

Contém funções para renderizar cards, gráficos, tabelas e outros
elementos de interface padronizados.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from calculations import formatar_brl, formatar_numero_br


# Configurações visuais constantes
TEMA_PLOTLY = "plotly_dark"
CORES_SUBSISTEMA = {
    'NORTE': '#1f77b4',
    'NORDESTE': '#ff7f0e',
    'SUDESTE': '#2ca02c',
    'SUL': '#d62728',
    'SE/CO': '#9467bd',
}


def configurar_pagina(titulo: str = "ReEnergia", icone: str = "⚡"):
    """Configura a página do Streamlit com tema consistente."""
    st.set_page_config(
        page_title=f"{titulo} | Marketplace de Energia Renovável",
        page_icon=icone,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS customizado
    st.markdown("""
    <style>
        /* Variáveis de cor do tema ReEnergia */
        :root {
            --primary: #00C896;
            --primary-dark: #00A67C;
            --secondary: #1E3A5F;
            --accent: #FFB400;
            --danger: #E84D4D;
            --bg-card: #161B22;
            --bg-hover: #21262D;
            --border: #30363D;
            --text-primary: #E6EDF3;
            --text-secondary: #8B949E;
        }

        /* Card de métrica customizado */
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: all 0.2s ease;
        }
        .metric-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(0, 200, 150, 0.15);
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }
        .metric-delta {
            font-size: 0.8rem;
            margin-top: 6px;
        }
        .metric-delta.positive { color: var(--primary); }
        .metric-delta.negative { color: var(--danger); }

        /* Container principal */
        .main-container {
            padding-top: 1rem;
        }

        /* Section headers */
        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
        }
        .section-header h2 {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .section-icon {
            font-size: 1.5rem;
        }

        /* Info cards */
        .info-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        .info-card.success {
            border-left: 4px solid var(--primary);
        }
        .info-card.warning {
            border-left: 4px solid var(--accent);
        }
        .info-card.info {
            border-left: 4px solid var(--secondary);
        }
        .info-card.danger {
            border-left: 4px solid var(--danger);
        }
        .info-card-title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }
        .info-card-body {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Sidebar styling */
        .sidebar-header {
            text-align: center;
            padding: 1rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }
        .sidebar-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
            margin: 0;
        }
        .sidebar-subtitle {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            color: var(--text-secondary);
            transition: all 0.2s;
        }
        .stTabs [data-baseweb="tab"]:hover {
            border-color: var(--primary);
            color: var(--text-primary);
        }
        .stTabs [aria-selected="true"] {
            background: var(--primary) !important;
            border-color: var(--primary) !important;
            color: #0D1117 !important;
        }

        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }

        /* Button improvements */
        .stButton > button[kind="primary"] {
            background: var(--primary);
            border: none;
            color: #0D1117;
            font-weight: 600;
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--primary-dark);
        }

        /* Tooltip-like help text */
        .help-text {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-style: italic;
        }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 3rem 2rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text-secondary);
        }
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
    </style>
    """, unsafe_allow_html=True)


def renderizar_sidebar_header():
    """Renderiza cabeçalho da sidebar."""
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <h3 class="sidebar-title">⚡ ReEnergia</h3>
        <p class="sidebar-subtitle">Marketplace de Energia Restrita</p>
    </div>
    """, unsafe_allow_html=True)


def renderizar_seletor_modulo() -> str:
    """Renderiza seletor de módulo na sidebar usando radio."""
    st.sidebar.subheader("📊 Módulos de Análise")

    modulos = {
        "visao_geral": "📈 Visão Geral",
        "restricoes": "🚫 Restrições & Curtailment",
        "mapa": "🗺️ Mapa Geográfico",
        "matchmaker": "🤝 Matchmaker Investimentos",
    }

    # Usar radio estilizado
    escolha = st.sidebar.radio(
        "Selecione o módulo:",
        options=list(modulos.keys()),
        format_func=lambda x: modulos[x],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    return escolha


def renderizar_filtro_subsistema(subsistemas: List[str]) -> List[str]:
    """Renderiza filtro de subsistema na sidebar."""
    st.sidebar.subheader("🔍 Filtros Globais")

    selecao = st.sidebar.multiselect(
        "Subsistema / Submercado:",
        options=subsistemas,
        default=subsistemas,
        help="Filtre os dados por subsistema elétrico brasileiro"
    )

    return selecao


def renderizar_metricas(kpis: Dict[str, Any], colunas: int = 4):
    """
    Renderiza linha de métricas (KPIs) usando st.metric nativo
    com container customizado.
    """
    cols = st.columns(colunas)

    for i, (key, value) in enumerate(kpis.items()):
        with cols[i % colunas]:
            if isinstance(value, dict):
                st.metric(
                    label=value.get('label', key),
                    value=value.get('value', '—'),
                    delta=value.get('delta'),
                    delta_color=value.get('delta_color', 'normal')
                )
            else:
                st.metric(label=key, value=value)


def criar_grafico_linha_temporal(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    titulo: str,
    labels: Dict[str, str] = None,
    template: str = TEMA_PLOTLY
) -> go.Figure:
    """Cria gráfico de linha temporal padronizado."""
    if labels is None:
        labels = {x: x, y: y, color: color}

    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        labels=labels,
        title=titulo,
        template=template,
        color_discrete_map=CORES_SUBSISTEMA
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )

    return fig


def criar_grafico_barras_horizontal(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    labels: Dict[str, str] = None,
    color: str = None,
    color_scale: str = 'Viridis',
    template: str = TEMA_PLOTLY
) -> go.Figure:
    """Cria gráfico de barras horizontal padronizado (Top N)."""
    if labels is None:
        labels = {x: x, y: y}

    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation='h',
        labels=labels,
        title=titulo,
        color=color,
        color_continuous_scale=color_scale,
        template=template
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )

    return fig


def criar_grafico_area(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    labels: Dict[str, str] = None,
    cor: str = '#00C896',
    template: str = TEMA_PLOTLY
) -> go.Figure:
    """Cria gráfico de área padronizado."""
    if labels is None:
        labels = {x: x, y: y}

    fig = px.area(
        df,
        x=x,
        y=y,
        labels=labels,
        title=titulo,
        template=template,
        color_discrete_sequence=[cor]
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )

    return fig


def criar_grafico_barras_agrupadas(
    categorias: List[str],
    valores_a: List[float],
    valores_b: List[float],
    nome_a: str,
    nome_b: str,
    titulo: str,
    cor_a: str = '#EF553B',
    cor_b: str = '#00CC96',
    template: str = TEMA_PLOTLY
) -> go.Figure:
    """Cria gráfico de barras agrupadas para comparação."""
    fig = go.Figure(data=[
        go.Bar(name=nome_a, x=categorias, y=valores_a, marker_color=cor_a),
        go.Bar(name=nome_b, x=categorias, y=valores_b, marker_color=cor_b)
    ])

    fig.update_layout(
        barmode='group',
        template=template,
        title=titulo,
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=False
    )

    return fig


def criar_grafico_mapa(
    df: pd.DataFrame,
    lat: str = "latitude",
    lon: str = "longitude",
    hover_name: str = "nom_usina",
    hover_data: List[str] = None,
    size: str = "mwh_restrito",
    color: str = "custo_restricao_rs",
    titulo: str = "Usinas com Restrição",
    template: str = TEMA_PLOTLY
) -> go.Figure:
    """Cria gráfico de mapa de dispersão (scatter_map)."""
    if hover_data is None:
        hover_data = ["nom_subsistema", "mwh_restrito", "custo_restricao_rs"]

    fig = px.scatter_map(
        df,
        lat=lat,
        lon=lon,
        hover_name=hover_name,
        hover_data=hover_data,
        size=size,
        color=color,
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=30,
        zoom=3,
        map_style="carto-darkmatter",
        title=titulo
    )

    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        template=template
    )

    return fig


def renderizar_tabela_formatada(
    df: pd.DataFrame,
    colunas_formatadas: Dict[str, str] = None,
    altura: int = 400
):
    """
    Renderiza tabela formatada com estilo brasileiro.

    Args:
        df: DataFrame a renderizar
        colunas_formatadas: Dict {coluna: formato}
            Formatos: 'brl', 'numero', 'pct', 'mwh'
        altura: Altura da tabela em pixels
    """
    if df.empty:
        st.info("Nenhum dado disponível para exibição.")
        return

    df_display = df.copy()

    if colunas_formatadas:
        for col, fmt in colunas_formatadas.items():
            if col in df_display.columns:
                if fmt == 'brl':
                    df_display[col] = df_display[col].apply(
                        lambda x: formatar_brl(x) if pd.notna(x) else "—"
                    )
                elif fmt == 'numero':
                    df_display[col] = df_display[col].apply(
                        lambda x: formatar_numero_br(x, 2) if pd.notna(x) else "—"
                    )
                elif fmt == 'pct':
                    df_display[col] = df_display[col].apply(
                        lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
                    )
                elif fmt == 'mwh':
                    df_display[col] = df_display[col].apply(
                        lambda x: f"{formatar_numero_br(x, 2)} MWh" if pd.notna(x) else "—"
                    )

    st.dataframe(
        df_display,
        use_container_width=True,
        height=altura,
        hide_index=True
    )


def renderizar_info_card(
    titulo: str,
    conteudo: str,
    tipo: str = "info"
):
    """
    Renderiza card informativo estilizado.

    Tipos: 'success', 'warning', 'info', 'danger'
    """
    icones = {
        'success': '✅',
        'warning': '⚠️',
        'info': 'ℹ️',
        'danger': '❌'
    }

    icone = icones.get(tipo, 'ℹ️')

    st.markdown(f"""
    <div class="info-card {tipo}">
        <div class="info-card-title">{icone} {titulo}</div>
        <div class="info-card-body">{conteudo}</div>
    </div>
    """, unsafe_allow_html=True)


def renderizar_empty_state(
    icone: str,
    titulo: str,
    mensagem: str
):
    """Renderiza estado vazio padronizado."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icone}</div>
        <h3 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">{titulo}</h3>
        <p style="margin: 0;">{mensagem}</p>
    </div>
    """, unsafe_allow_html=True)


def renderizar_kpi_card(
    label: str,
    valor: str,
    delta: str = None,
    delta_positivo: bool = True
):
    """Renderiza card de KPI customizado (alternativa ao st.metric)."""
    delta_html = ""
    if delta:
        classe = "positive" if delta_positivo else "negative"
        delta_html = f'<div class="metric-delta {classe}">{delta}</div>'

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{valor}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def renderizar_section_header(icone: str, titulo: str):
    """Renderiza cabeçalho de seção padronizado."""
    st.markdown(f"""
    <div class="section-header">
        <span class="section-icon">{icone}</span>
        <h2>{titulo}</h2>
    </div>
    """, unsafe_allow_html=True)