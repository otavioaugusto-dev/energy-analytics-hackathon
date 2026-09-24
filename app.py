import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(
    page_title="Analytics & Matchmaker | ONS & CCEE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada
st.markdown("""
    <style>
        .metric-card {
            background-color: #0e1117;
            border: 1px solid #262730;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stMetric {
            background-color: #161b22;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
    </style>
""", unsafe_allow_html=True)

# Carregamento de Dados Otimizado (Cache)
@st.cache_data
def load_data():
    df_ger = pd.read_parquet("data/dash_geracao_diaria.parquet")
    df_rest = pd.read_parquet("data/dash_restricao_diaria.parquet")
    
    # Garantir datetime
    df_ger['data'] = pd.to_datetime(df_ger['data'])
    df_rest['data'] = pd.to_datetime(df_rest['data'])
    
    return df_ger, df_rest

try:
    df_geracao, df_restricao = load_data()
except Exception as e:
    st.error(f"Erro ao carregar os arquivos Parquet de `data/`. Verifique se o Sprint 2 foi executado. Detalhes: {e}")
    st.stop()

# Lista global de subsistemas
subsistemas_disponiveis = sorted(list(
    set(df_geracao['nom_subsistema'].dropna()).union(set(df_restricao['nom_subsistema'].dropna()))
))

# ==================== SIDEBAR / FILTROS ====================
st.sidebar.title("⚡ Painel de Controle")
st.sidebar.subheader("Filtros Globais")

# Seleção de Visão
visao_selecionada = st.sidebar.radio(
    "Selecione o Módulo de Análise:",
    [
        "📊 Visão Geral de Geração (2023)",
        "🚫 Análise de Restrições & Losses (2026)",
        "🗺️ Mapeamento Geográfico",
        "🤝 Matchmaker de Investimentos"
    ]
)

# Filtro de Subsistema (para visões de dados)
subsistema_filtro = st.sidebar.multiselect(
    "Subsistema / Submercado:", 
    subsistemas_disponiveis, 
    default=subsistemas_disponiveis
)

# Aplicar Filtro de Subsistema
df_ger_filtered = df_geracao[df_geracao['nom_subsistema'].isin(subsistema_filtro)] if subsistema_filtro else df_geracao
df_rest_filtered = df_restricao[df_restricao['nom_subsistema'].isin(subsistema_filtro)] if subsistema_filtro else df_restricao

st.sidebar.markdown("---")
st.sidebar.caption("Hackathon Energy Analytics v1.0")


# ==================== VISÃO 1: GERAÇÃO (2023) ====================
if visao_selecionada == "📊 Visão Geral de Geração (2023)":
    st.title("📊 Monitoramento de Geração Verificada (ONS)")
    st.caption("Análise consolidada por dia e subsistema ao longo de 2023")

    # KPIs
    tot_mwh = df_ger_filtered['mwh_gerado'].sum()
    usinas_ativas = df_ger_filtered['nom_usina'].nunique()
    media_diaria = df_ger_filtered.groupby('data')['mwh_gerado'].sum().mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Geração Total (MWh)", f"{tot_mwh:,.2f}".replace(",", "."))
    col2.metric("Média Diária Gerada (MWh)", f"{media_diaria:,.2f}".replace(",", "."))
    col3.metric("Usinas Monitoradas", usinas_ativas)

    st.markdown("---")

    # Gráfico 1: Evolução da Geração Diária por Subsistema
    st.subheader("Evolução Temporal da Geração (MWh)")
    df_trend = df_ger_filtered.groupby(['data', 'nom_subsistema'])['mwh_gerado'].sum().reset_index()
    
    fig_gen = px.line(
        df_trend,
        x='data',
        y='mwh_gerado',
        color='nom_subsistema',
        labels={'mwh_gerado': 'Geração (MWh)', 'data': 'Data', 'nom_subsistema': 'Subsistema'},
        title="Geração Total Diária por Subsistema (2023)",
        template="plotly_dark"
    )
    fig_gen.update_layout(hovermode="x unified")
    st.plotly_chart(fig_gen, use_container_width=True)

    # Gráfico 2: Top 10 Usinas
    st.subheader("Top 10 Usinas por Volume Gerado")
    top_usinas = df_ger_filtered.groupby('nom_usina')['mwh_gerado'].sum().nlargest(10).reset_index()
    fig_top = px.bar(
        top_usinas,
        x='mwh_gerado',
        y='nom_usina',
        orientation='h',
        labels={'mwh_gerado': 'Geração (MWh)', 'nom_usina': 'Usina'},
        color='mwh_gerado',
        color_continuous_scale='Viridis',
        template="plotly_dark"
    )
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)


# ==================== VISÃO 2: RESTRIÇÕES & CUSTOS ====================
elif visao_selecionada == "🚫 Análise de Restrições & Losses (2026)":
    st.title("🚫 Restrições Operacionais & Impacto Financeiro (Constrained-off)")
    st.caption("Análise de corte de geração e cruzamento com PLD CCEE")

    # KPIs
    tot_mwh_restrito = df_rest_filtered['mwh_restrito'].sum()
    custo_total = df_rest_filtered['custo_restricao_rs'].sum()
    pld_medio = df_rest_filtered['pld_medio'].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Energia Restrita (MWh)", f"{tot_mwh_restrito:,.2f}".replace(",", "."))
    c2.metric("Custo Estimado da Restrição (R$)", f"R$ {custo_total:,.2f}".replace(",", "."))
    c3.metric("PLD Médio Registrado (R$/MWh)", f"R$ {pld_medio:.2f}")

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Geração Verificada vs Restrição Diária")
        df_rest_daily = df_rest_filtered.groupby('data')[['mwh_verificado', 'mwh_restrito']].sum().reset_index()
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_rest_daily['data'], y=df_rest_daily['mwh_verificado'], name='Verificado (MWh)', marker_color='#2ca02c'))
        fig_comp.add_trace(go.Bar(x=df_rest_daily['data'], y=df_rest_daily['mwh_restrito'], name='Restrito (MWh)', marker_color='#d62728'))
        fig_comp.update_layout(barmode='stack', template="plotly_dark", title="Volume Restrito x Verificado")
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_g2:
        st.subheader("Custo Diário das Restrições (R$)")
        df_cost_daily = df_rest_filtered.groupby('data')['custo_restricao_rs'].sum().reset_index()
        fig_cost = px.area(
            df_cost_daily,
            x='data',
            y='custo_restricao_rs',
            labels={'custo_restricao_rs': 'Custo (R$)', 'data': 'Data'},
            title="Impacto Financeiro Diário (Constrained-off)",
            template="plotly_dark",
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    # Tabela detalhada
    st.subheader("Detalhamento por Usina e Motivo")
    st.dataframe(
        df_rest_filtered[['data', 'nom_subsistema', 'nom_usina', 'mwh_verificado', 'mwh_restrito', 'custo_restricao_rs', 'pld_medio']]
        .sort_values(by='custo_restricao_rs', ascending=False)
        .style.format({
            'mwh_verificado': '{:,.2f}',
            'mwh_restrito': '{:,.2f}',
            'custo_restricao_rs': 'R$ {:,.2f}',
            'pld_medio': 'R$ {:,.2f}'
        }),
        use_container_width=True
    )


# ==================== VISÃO 3: MAPA GEOGRÁFICO ====================
elif visao_selecionada == "🗺️ Mapeamento Geográfico":
    st.title("🗺️ Localização e Distribuição Geográfica")
    st.caption("Geolocalização dos ativos monitorados e com restrições registradas")

    df_map = df_rest_filtered.dropna(subset=['latitude', 'longitude'])

    if len(df_map) == 0:
        st.warning("Nenhuma usina no filtro selecionado possui coordenadas geográficas válidas cadastradas no ANEEL SIGA.")
    else:
        fig_map = px.scatter_map(
            df_map,
            lat="latitude",
            lon="longitude",
            hover_name="nom_usina",
            hover_data=["nom_subsistema", "mwh_restrito", "custo_restricao_rs"],
            size="mwh_restrito",
            color="custo_restricao_rs",
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=30,
            zoom=3,
            map_style="carto-darkmatter",
            title="Usinas com Restrição (Tamanho = MWh Restrito | Cor = Custo R$)"
        )
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)


# ==================== VISÃO 4: MATCHMAKER DE INVESTIMENTOS ====================
else:
    st.title("🤝 Matchmaker de Energia: Investidor x Gerador")
    st.caption("Conecte sua demanda industrial/datacenter a excedentes de geração com desconto em relação ao mercado tradicional.")

    # 1. FORMULÁRIO DO INVESTIDOR
    with st.container(border=True):
        st.subheader("📋 Perfil do Investidor / Projeto")
        
        c_i1, c_i2, c_i3 = st.columns(3)
        with c_i1:
            tipo_projeto = st.selectbox(
                "Tipo de Empreendimento:",
                ["Data Center / AI Cluster", "Planta de Hidrogênio Verde", "Indústria Eletrointensiva", "Outro"]
            )
            regiao_pref = st.selectbox("Subsistema Preferencial:", subsistemas_disponiveis, index=0)
            
        with c_i2:
            carga_mw = st.number_input("Carga Necessária (MW):", min_value=1.0, max_value=500.0, value=35.0, step=5.0)
            turno = st.selectbox("Perfil de Operação / Turno:", ["24/7 (Ininterrupto)", "Noturno (18h às 06h)", "Diurno (06h às 18h)"])
            
        with c_i3:
            tarifa_baseline = st.number_input("Tarifa Baseline Atual (R$/MWh):", min_value=100.0, max_value=800.0, value=380.0, help="Preço de referência do mercado livre tradicional ou cativo")
            fator_desconto = st.slider("Desconto Alvo no Excedente (%):", min_value=10, max_value=60, value=30)

        btn_buscar = st.button("🔍 Processar Match e Calcular Economia", use_container_width=True, type="primary")

    # 2. LÓGICA DE MATCHING E CÁLCULO DE ECONOMIA
    if btn_buscar:
        horas_mes = 720 if "24/7" in turno else 360
        demanda_mensal_mwh = carga_mw * horas_mes
        
        df_match = df_restricao[df_restricao['nom_subsistema'] == regiao_pref].copy()
        
        if df_match.empty:
            st.warning(f"Não foram encontradas restrições registradas no subsistema {regiao_pref} no período analisado.")
        else:
            usinas_oferta = df_match.groupby(['nom_usina']).agg(
                mwh_disponivel=('mwh_restrito', 'sum'),
                pld_medio=('pld_medio', 'mean')
            ).reset_index()

            preco_oferta_mwh = tarifa_baseline * (1 - (fator_desconto / 100))
            
            custo_baseline_mensal = demanda_mensal_mwh * tarifa_baseline
            custo_match_mensal = demanda_mensal_mwh * preco_oferta_mwh
            economia_mensal = custo_baseline_mensal - custo_match_mensal
            economia_anual = economia_mensal * 12
            co2_evitado = (demanda_mensal_mwh * 12) * 0.04

            st.markdown("---")
            st.subheader("💡 Oportunidade de Match Encontrada")

            # KPIs principais
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Demanda Mensal", f"{demanda_mensal_mwh:,.0f} MWh".replace(",", "."))
            k2.metric("Preço Proposto", f"R$ {preco_oferta_mwh:.2f} / MWh")
            k3.metric("Economia Mensal Estimada", f"R$ {economia_mensal:,.2f}".replace(",", "."))
            k4.metric("Economia Anual (ROI)", f"R$ {economia_anual:,.2f}".replace(",", "."), delta=f"-{fator_desconto}% vs Baseline")

            # 🆕 NOVO RECURSO 1: ANÁLISE DE SENSIBILIDADE
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📈 Análise de Sensibilidade (Estresse de Cenários)")
            c_ot, c_ba, c_es = st.columns(3)
            c_ot.metric("Cenário Agressivo (+20% Volatilidade)", f"R$ {economia_anual * 1.2:,.2f}".replace(",", "."), delta="+20% Economia")
            c_ba.metric("Cenário Base (Projetado)", f"R$ {economia_anual:,.2f}".replace(",", "."))
            c_es.metric("Cenário Conservador (-20% Volatilidade)", f"R$ {economia_anual * 0.8:,.2f}".replace(",", "."), delta="-20% Economia")

            # Comparativo Visual
            st.markdown("<br>", unsafe_allow_html=True)
            fig_comp = go.Figure(data=[
                go.Bar(name='Custo Baseline (Tradicional)', x=['Gasto Mensal (R$)'], y=[custo_baseline_mensal], marker_color='#ef553b'),
                go.Bar(name='Custo via Excedente (Matchmaker)', x=['Gasto Mensal (R$)'], y=[custo_match_mensal], marker_color='#00cc96')
            ])
            fig_comp.update_layout(barmode='group', template="plotly_dark", title="Comparativo do Custo de Suprimento Energético Mensal")
            st.plotly_chart(fig_comp, use_container_width=True)

            # Usinas Compatíveis
            st.subheader("⚡ Geradores Candidatos com Excedente Operacional")
            
            usinas_oferta['atendimento_demanda_%'] = (usinas_oferta['mwh_disponivel'] / demanda_mensal_mwh) * 100
            usinas_oferta['atendimento_demanda_%'] = usinas_oferta['atendimento_demanda_%'].clip(upper=100)
            
            st.dataframe(
                usinas_oferta[['nom_usina', 'mwh_disponivel', 'pld_medio', 'atendimento_demanda_%']]
                .sort_values(by='mwh_disponivel', ascending=False)
                .head(10)
                .style.format({
                    'mwh_disponivel': '{:,.2f} MWh',
                    'pld_medio': 'R$ {:,.2f}',
                    'atendimento_demanda_%': '{:.1f}% da carga'
                }),
                use_container_width=True
            )
            
            st.info(f"🌱 **Impacto ESG Estimado:** Utilizando a energia renovável restrita deste match, seu empreendimento evita a emissão de **{co2_evitado:,.1f} toneladas de CO₂** por ano.")

            # 🆕 NOVO RECURSO 2: BOTÃO DE EXPORTAÇÃO CSV
            st.markdown("---")
            st.subheader("📄 Exportar Term Sheet Comercial")
            
            df_export = usinas_oferta[['nom_usina', 'mwh_disponivel', 'pld_medio', 'atendimento_demanda_%']].copy()
            df_export['tarifa_proposta_mwh'] = preco_oferta_mwh
            df_export['economia_mensal_estimada'] = economia_mensal
            
            csv_data = df_export.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Baixar Relatório de Match & Viabilidade (CSV)",
                data=csv_data,
                file_name=f"relatorio_match_{tipo_projeto.replace(' ', '_')}_{regiao_pref}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )