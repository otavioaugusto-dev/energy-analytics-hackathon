"""
ReEnergia - Marketplace de Energia Renovável Restrita

Dashboard interativo para análise de curtailment (restrição de geração)
e matchmaking entre geradores com excedente e consumidores de alta demanda.

Desenvolvido para o Hackathon ProEnergia.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importar módulos locais
from data_loader import (
    carregar_dados_processados,
    obter_subsistemas_disponiveis,
    filtrar_por_subsistema,
    preparar_dados_mapa,
    obter_periodo_dados,
)
from calculations import (
    PerfilInvestidor,
    processar_match,
    formatar_brl,
    formatar_numero_br,
    calcular_kpis_geracao,
    calcular_kpis_restricao,
    preparar_dados_exportacao,
    calcular_horas_mes,
    FATOR_EMISSAO_CO2_TON_POR_MWH,
)
from ui_components import (
    configurar_pagina,
    renderizar_sidebar_header,
    renderizar_seletor_modulo,
    renderizar_filtro_subsistema,
    renderizar_section_header,
    criar_grafico_linha_temporal,
    criar_grafico_barras_horizontal,
    criar_grafico_area,
    criar_grafico_barras_agrupadas,
    criar_grafico_mapa,
    renderizar_tabela_formatada,
    renderizar_info_card,
    renderizar_empty_state,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
configurar_pagina()


# ============================================================
# CARREGAMENTO DE DADOS (COM CACHE E TRATAMENTO DE ERRO)
# ============================================================
@st.cache_data(show_spinner="Inicializando ReEnergia...")
def inicializar_dados():
    """Carrega e prepara todos os dados necessários."""
    try:
        df_ger, df_rest = carregar_dados_processados()
        subsistemas = obter_subsistemas_disponiveis(df_ger, df_rest)
        periodo_info = obter_periodo_dados(df_ger, df_rest)
        return df_ger, df_rest, subsistemas, periodo_info, None
    except FileNotFoundError as e:
        return None, None, [], {}, str(e)
    except Exception as e:
        return None, None, [], {}, f"Erro inesperado ao carregar dados: {e}"


df_geracao, df_restricao, subsistemas_disponiveis, periodo_info, erro_carregamento = inicializar_dados()

if erro_carregamento:
    st.error(f"❌ {erro_carregamento}")
    st.info("💡 Execute `python prepare_dashboard.py` para gerar os arquivos Parquet necessários.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================
renderizar_sidebar_header()

# Seletor de módulo
modulo_selecionado = renderizar_seletor_modulo()

# Filtro de subsistema (aplicável a visões de dados)
st.sidebar.subheader("🔍 Filtros Globais")
subsistema_filtro = st.sidebar.multiselect(
    "Subsistema / Submercado:",
    options=subsistemas_disponiveis,
    default=subsistemas_disponiveis,
    help="Filtre os dados por subsistema elétrico brasileiro",
    key="filtro_subsistema_global"
)

# Aplicar filtro
df_ger_filtrado, df_rest_filtrado = filtrar_por_subsistema(
    df_geracao, df_restricao, subsistema_filtro
)

# Info do período na sidebar
st.sidebar.markdown("---")
with st.sidebar.expander("📅 Período dos Dados", expanded=False):
    st.caption(f"**Geração (ONS 2023):** {periodo_info['geracao_inicio'].strftime('%d/%m/%Y')} a {periodo_info['geracao_fim'].strftime('%d/%m/%Y')}")
    st.caption(f"**Restrição (ONS 2026):** {periodo_info['restricao_inicio'].strftime('%d/%m/%Y')} a {periodo_info['restricao_fim'].strftime('%d/%m/%Y')}")
    st.caption(f"Usinas geração: {periodo_info['n_usinas_geracao']} | Usinas restrição: {periodo_info['n_usinas_restricao']}")

st.sidebar.markdown("---")
st.sidebar.caption("ReEnergia v2.0 — Hackathon ProEnergia")


# ============================================================
# ROTEAMENTO DE MÓDULOS
# ============================================================

# ----------------------------------------------------------
# MÓDULO 1: VISÃO GERAL DE GERAÇÃO (2023)
# ----------------------------------------------------------
if modulo_selecionado == "visao_geral":
    st.title("📈 Visão Geral de Geração Verificada")
    st.caption("Análise consolidada da geração por dia e subsistema — Dados ONS 2023")

    if df_ger_filtrado.empty:
        renderizar_empty_state(
            "📊",
            "Nenhum dado de geração",
            "Selecione ao menos um subsistema no filtro lateral."
        )
    else:
        # KPIs
        kpis = calcular_kpis_geracao(df_ger_filtrado)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Geração Total",
                formatar_numero_br(kpis['total_mwh'], 0) + " MWh",
                help="Soma de toda geração verificada no período filtrado"
            )
        with col2:
            st.metric(
                "Média Diária",
                formatar_numero_br(kpis['media_diaria_mwh'], 0) + " MWh",
                help="Média da geração diária total no período"
            )
        with col3:
            st.metric(
                "Usinas Monitoradas",
                formatar_numero_br(kpis['n_usinas'], 0),
                help="Número de usinas únicas com dados no período"
            )
        with col4:
            st.metric(
                "Pico Máximo",
                formatar_numero_br(kpis['geracao_max_mw'], 0) + " MW",
                help="Maior geração horária registrada (MW médio na hora)"
            )

        st.markdown("---")

        # Gráfico 1: Evolução temporal
        renderizar_section_header("📅", "Evolução Temporal da Geração Diária")

        df_trend = df_ger_filtrado.groupby(['data', 'nom_subsistema'])['mwh_gerado'].sum().reset_index()

        fig_gen = criar_grafico_linha_temporal(
            df_trend,
            x='data',
            y='mwh_gerado',
            color='nom_subsistema',
            titulo="Geração Total Diária por Subsistema (2023)",
            labels={'mwh_gerado': 'Geração (MWh)', 'data': 'Data', 'nom_subsistema': 'Subsistema'}
        )
        st.plotly_chart(fig_gen, use_container_width=True)

        # Gráfico 2: Top 10 Usinas
        renderizar_section_header("🏭", "Top 10 Usinas por Volume Gerado")

        top_usinas = (
            df_ger_filtrado.groupby('nom_usina')['mwh_gerado']
            .sum()
            .nlargest(10)
            .reset_index()
        )

        fig_top = criar_grafico_barras_horizontal(
            top_usinas,
            x='mwh_gerado',
            y='nom_usina',
            titulo="Top 10 Usinas — Geração Total Acumulada (2023)",
            labels={'mwh_gerado': 'Geração (MWh)', 'nom_usina': 'Usina'},
            color='mwh_gerado'
        )
        st.plotly_chart(fig_top, use_container_width=True)

        # Gráfico 3: Distribuição por tipo de geração
        renderizar_section_header("⚡", "Geração por Tipo de Fonte")

        if 'tipo_geracao' in df_ger_filtrado.columns and df_ger_filtrado['tipo_geracao'].notna().any():
            df_tipo = (
                df_ger_filtrado.groupby('tipo_geracao')['mwh_gerado']
                .sum()
                .reset_index()
                .sort_values('mwh_gerado', ascending=False)
            )

            fig_tipo = px.pie(
                df_tipo,
                values='mwh_gerado',
                names='tipo_geracao',
                title="Participação por Tipo de Geração",
                template="plotly_dark",
                hole=0.4
            )
            fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
            fig_tipo.update_layout(showlegend=True)
            st.plotly_chart(fig_tipo, use_container_width=True)
        else:
            st.info("Dados de tipo de geração não disponíveis para o filtro selecionado.")


# ----------------------------------------------------------
# MÓDULO 2: ANÁLISE DE RESTRIÇÕES & CURTAILMENT (2026)
# ----------------------------------------------------------
elif modulo_selecionado == "restricoes":
    st.title("🚫 Análise de Restrições Operacionais & Curtailment")
    st.caption("Cruzamento financeiro entre MWh cortados (constrained-off) e PLD — Dados ONS/CCEE 2026")

    if df_rest_filtrado.empty:
        renderizar_empty_state(
            "🚫",
            "Nenhum dado de restrição",
            "Selecione ao menos um subsistema no filtro lateral."
        )
    else:
        # KPIs
        kpis = calcular_kpis_restricao(df_rest_filtrado)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Energia Restrita Total",
                formatar_numero_br(kpis['total_mwh_restrito'], 0) + " MWh",
                help="Soma de toda energia cortada por restrição de transmissão"
            )
        with col2:
            st.metric(
                "Custo Estimado Total",
                formatar_brl(kpis['custo_total_rs']),
                help="Custo de oportunidade: MWh restrito × PLD horário"
            )
        with col3:
            st.metric(
                "PLD Médio",
                formatar_brl(kpis['pld_medio']) + " /MWh",
                help="Preço de Liquidação das Diferenças médio ponderado"
            )
        with col4:
            st.metric(
                "% Médio de Restrição",
                f"{kpis['pct_medio_restricao']:.1f}%",
                help="Média de (Restrito / Potencial) × 100 por usina/dia"
            )

        st.markdown("---")

        # Layout em duas colunas
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            renderizar_section_header("📊", "Geração Verificada vs Restrição Diária")

            df_rest_daily = (
                df_rest_filtrado.groupby('data')[['mwh_verificado', 'mwh_restrito']]
                .sum()
                .reset_index()
            )

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=df_rest_daily['data'],
                y=df_rest_daily['mwh_verificado'],
                name='Verificado (MWh)',
                marker_color='#2ca02c',
                hovertemplate='Data: %{x}<br>Verificado: %{y:,.2f} MWh<extra></extra>'
            ))
            fig_comp.add_trace(go.Bar(
                x=df_rest_daily['data'],
                y=df_rest_daily['mwh_restrito'],
                name='Restrito (MWh)',
                marker_color='#d62728',
                hovertemplate='Data: %{x}<br>Restrito: %{y:,.2f} MWh<extra></extra>'
            ))
            fig_comp.update_layout(
                barmode='stack',
                template="plotly_dark",
                title="Volume Restrito x Verificado Diário",
                hovermode="x unified",
                margin=dict(l=40, r=20, t=60, b=40),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_comp.update_xaxes(showgrid=False, zeroline=False)
            fig_comp.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)', zeroline=False
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with col_g2:
            renderizar_section_header("💰", "Custo Diário das Restrições")

            df_cost_daily = (
                df_rest_filtrado.groupby('data')['custo_restricao_rs']
                .sum()
                .reset_index()
            )

            fig_cost = criar_grafico_area(
                df_cost_daily,
                x='data',
                y='custo_restricao_rs',
                titulo="Impacto Financeiro Diário (Constrained-off)",
                labels={'custo_restricao_rs': 'Custo (R$)', 'data': 'Data'},
                cor='#ff7f0e'
            )
            st.plotly_chart(fig_cost, use_container_width=True)

        # Gráfico 3: % Restrição por usina
        renderizar_section_header("📈", "Percentual de Restrição por Usina")

        df_pct = (
            df_rest_filtrado.groupby('nom_usina')[['mwh_restrito', 'mwh_potencial']]
            .sum()
            .reset_index()
        )
        df_pct['pct_restricao'] = (df_pct['mwh_restrito'] / df_pct['mwh_potencial'] * 100).round(1)
        df_pct = df_pct.sort_values('pct_restricao', ascending=True).tail(15)

        fig_pct = criar_grafico_barras_horizontal(
            df_pct,
            x='pct_restricao',
            y='nom_usina',
            titulo="Top 15 Usinas — Maior % de Restrição",
            labels={'pct_restricao': '% Restrição', 'nom_usina': 'Usina'},
            color='pct_restricao',
            color_scale='Reds'
        )
        st.plotly_chart(fig_pct, use_container_width=True)

        # Tabela detalhada
        renderizar_section_header("📋", "Detalhamento por Usina e Dia")

        colunas_tabela = {
            'mwh_verificado': 'numero',
            'mwh_restrito': 'numero',
            'custo_restricao_rs': 'brl',
            'pld_medio': 'brl',
            'pct_restricao': 'pct',
        }

        df_tabela = df_rest_filtrado[[
            'data', 'nom_subsistema', 'nom_usina',
            'mwh_verificado', 'mwh_restrito',
            'custo_restricao_rs', 'pld_medio', 'pct_restricao'
        ]].sort_values('custo_restricao_rs', ascending=False)

        renderizar_tabela_formatada(df_tabela, colunas_tabela, altura=450)


# ----------------------------------------------------------
# MÓDULO 3: MAPA GEOGRÁFICO
# ----------------------------------------------------------
elif modulo_selecionado == "mapa":
    st.title("🗺️ Mapeamento Geográfico das Restrições")
    st.caption("Geolocalização interativa das usinas com restrição operacional registrada")

    df_mapa = preparar_dados_mapa(df_rest_filtrado)

    if df_mapa.empty:
        renderizar_empty_state(
            "📍",
            "Nenhuma usina com coordenadas válidas",
            "As usinas no filtro selecionado não possuem latitude/longitude cadastradas no ANEEL SIGA."
        )
    else:
        # Métricas do mapa
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Usinas no Mapa", len(df_mapa))
        with col2:
            st.metric("MWh Restrito Total", formatar_numero_br(df_mapa['mwh_restrito'].sum(), 0) + " MWh")
        with col3:
            st.metric("Custo Total", formatar_brl(df_mapa['custo_restricao_rs'].sum()))

        st.markdown("---")

        # Mapa
        fig_map = criar_grafico_mapa(
            df_mapa,
            titulo="Usinas com Restrição (Tamanho = MWh Restrito | Cor = Custo R$)"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Tabela resumo
        renderizar_section_header("📋", "Usinas Geolocalizadas")

        df_mapa_resumo = df_mapa.groupby('nom_usina').agg({
            'nom_subsistema': 'first',
            'latitude': 'first',
            'longitude': 'first',
            'mwh_restrito': 'sum',
            'custo_restricao_rs': 'sum',
            'tipo_geracao': 'first',
            'potencia_kw': 'first',
        }).reset_index().sort_values('custo_restricao_rs', ascending=False)

        colunas_mapa = {
            'mwh_restrito': 'mwh',
            'custo_restricao_rs': 'brl',
            'potencia_kw': 'numero',
        }

        renderizar_tabela_formatada(
            df_mapa_resumo[['nom_usina', 'nom_subsistema', 'tipo_geracao',
                           'potencia_kw', 'mwh_restrito', 'custo_restricao_rs',
                           'latitude', 'longitude']],
            colunas_mapa,
            altura=400
        )


# ----------------------------------------------------------
# MÓDULO 4: MATCHMAKER DE INVESTIMENTOS
# ----------------------------------------------------------
else:  # matchmaker
    st.title("🤝 Matchmaker: Investidor × Gerador")
    st.caption(
        "Conecte sua demanda industrial (Data Centers, H₂ Verde, Indústria Eletrointensiva) "
        "a excedentes de geração renovável com desconto sobre o mercado tradicional."
    )

    # Verificar se há dados de restrição
    if df_rest_filtrado.empty:
        renderizar_empty_state(
            "🤝",
            "Dados insuficientes para Matchmaker",
            "Não há dados de restrição disponíveis para o subsistema selecionado. "
            "Ajuste o filtro na barra lateral."
        )
    else:
        # ------------------------------------------------------
        # FORMULÁRIO DO INVESTIDOR
        # ------------------------------------------------------
        with st.container(border=True):
            renderizar_section_header("📋", "Perfil do Investidor / Projeto")

            c_i1, c_i2, c_i3 = st.columns(3)

            with c_i1:
                tipo_projeto = st.selectbox(
                    "Tipo de Empreendimento:",
                    ["Data Center / AI Cluster", "Planta de Hidrogênio Verde",
                     "Indústria Eletrointensiva", "Outro"],
                    help="Perfil de consumo influencia na análise de compatibilidade"
                )
                regiao_pref = st.selectbox(
                    "Subsistema Preferencial:",
                    subsistemas_disponiveis,
                    index=0 if subsistemas_disponiveis else 0,
                    help="Região onde o empreendimento será instalado"
                )

            with c_i2:
                carga_mw = st.number_input(
                    "Carga Necessária (MW):",
                    min_value=1.0,
                    max_value=500.0,
                    value=35.0,
                    step=5.0,
                    help="Potência média demandada pelo empreendimento"
                )
                perfil_operacao = st.selectbox(
                    "Perfil de Operação / Turno:",
                    ["24/7 (Ininterrupto)", "Noturno (18h às 06h)", "Diurno (06h às 18h)"],
                    help="Define as horas mensais de consumo para cálculo de MWh"
                )

            with c_i3:
                tarifa_baseline = st.number_input(
                    "Tarifa Baseline Atual (R$/MWh):",
                    min_value=100.0,
                    max_value=800.0,
                    value=380.0,
                    step=10.0,
                    help="Preço de referência do mercado livre tradicional ou cativo"
                )
                desconto_alvo = st.slider(
                    "Desconto Alvo no Excedente (%):",
                    min_value=10,
                    max_value=60,
                    value=30,
                    help="Percentual de desconto sobre a tarifa baseline"
                )

            btn_processar = st.button(
                "🔍 Processar Match e Calcular Economia",
                use_container_width=True,
                type="primary"
            )

        # ------------------------------------------------------
        # PROCESSAMENTO DO MATCH
        # ------------------------------------------------------
        if btn_processar:
            with st.spinner("Processando match e calculando viabilidade..."):
                perfil = PerfilInvestidor(
                    tipo_projeto=tipo_projeto,
                    subsistema_preferido=regiao_pref,
                    carga_mw=carga_mw,
                    perfil_operacao=perfil_operacao,
                    tarifa_baseline=tarifa_baseline,
                    desconto_alvo_pct=desconto_alvo
                )

                resultado = processar_match(df_restricao, perfil)

            if resultado is None:
                st.warning(
                    f"⚠️ Não foram encontradas restrições registradas no subsistema "
                    f"**{regiao_pref}** no período analisado, ou nenhuma usina possui "
                    f"excedente (restrição > 0) disponível."
                )
            else:
                st.success("✅ Match processado com sucesso!")
                st.markdown("---")

                # --------------------------------------------------
                # DESTAQUE BILATERAL (Investidor + Gerador)
                # --------------------------------------------------
                renderizar_section_header("💡", "Oportunidade de Match Encontrada")

                c_inv, c_ger = st.columns(2)

                with c_inv:
                    renderizar_info_card(
                        "🏢 Vantagem para o Investidor (Offtaker)",
                        f"Economia Anual projetada de **{formatar_brl(resultado.economia_anual)}** "
                        f"frente ao mercado tradicional ({desconto_alvo}% de desconto). "
                        f"Demanda mensal: **{formatar_numero_br(resultado.demanda_mensal_mwh, 0)} MWh** "
                        f"a **{formatar_brl(resultado.preco_oferta_mwh)}/MWh**.",
                        tipo="success"
                    )

                with c_ger:
                    renderizar_info_card(
                        "🌬️ Vantagem para a Usina (Gerador)",
                        f"Nova Receita Anual de **{formatar_brl(resultado.receita_gerador_anual)}** "
                        f"destrava energia que seria desperdiçada (Curtailment). "
                        f"Ticket mensal médio: **{formatar_brl(resultado.custo_match_mensal)}**.",
                        tipo="info"
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # --------------------------------------------------
                # KPIs TÉCNICOS
                # --------------------------------------------------
                renderizar_section_header("📊", "Indicadores Principais")

                k1, k2, k3, k4 = st.columns(4)

                with k1:
                    st.metric(
                        "Demanda Mensal",
                        formatar_numero_br(resultado.demanda_mensal_mwh, 0) + " MWh",
                        help=f"Carga {carga_mw} MW × {calcular_horas_mes(perfil_operacao)}h/mês"
                    )

                with k2:
                    st.metric(
                        "Preço Acordado",
                        formatar_brl(resultado.preco_oferta_mwh) + " /MWh",
                        delta=f"-{desconto_alvo}% vs Baseline",
                        delta_color="inverse"
                    )

                with k3:
                    st.metric(
                        "Ticket Mensal da Usina",
                        formatar_brl(resultado.custo_match_mensal),
                        help="Receita mensal estimada para o gerador"
                    )

                with k4:
                    st.metric(
                        "Economia Mensal (Comprador)",
                        formatar_brl(resultado.economia_mensal),
                        delta=f"{formatar_brl(resultado.economia_anual)}/ano",
                        delta_color="normal"
                    )

                # --------------------------------------------------
                # ANÁLISE DE SENSIBILIDADE
                # --------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                renderizar_section_header("📈", "Análise de Sensibilidade (Estresse de Cenários)")

                c_ot, c_ba, c_es = st.columns(3)

                with c_ot:
                    st.metric(
                        "Cenário Agressivo",
                        formatar_brl(resultado.cenario_agressivo),
                        delta="+20% vs Base",
                        delta_color="normal"
                    )
                    st.caption("Volatilidade favorável (+20%)")

                with c_ba:
                    st.metric(
                        "Cenário Base",
                        formatar_brl(resultado.cenario_base),
                        delta="Projetado",
                        delta_color="off"
                    )
                    st.caption("Cenário projetado padrão")

                with c_es:
                    st.metric(
                        "Cenário Conservador",
                        formatar_brl(resultado.cenario_conservador),
                        delta="-20% vs Base",
                        delta_color="inverse"
                    )
                    st.caption("Volatilidade adversa (-20%)")

                # --------------------------------------------------
                # COMPARATIVO VISUAL DE CUSTOS
                # --------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                renderizar_section_header("💰", "Comparativo do Custo de Suprimento Energético")

                fig_comp = criar_grafico_barras_agrupadas(
                    categorias=['Custo Mensal (R$)'],
                    valores_a=[resultado.custo_baseline_mensal],
                    valores_b=[resultado.custo_match_mensal],
                    nome_a='Custo Baseline (Mercado Tradicional)',
                    nome_b='Custo via Excedente (Matchmaker)',
                    titulo="Custo Mensal: Mercado Tradicional vs Matchmaker",
                    cor_a='#EF553B',
                    cor_b='#00CC96'
                )
                st.plotly_chart(fig_comp, use_container_width=True)

                # --------------------------------------------------
                # GERADORES CANDIDATOS
                # --------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                renderizar_section_header("⚡", "Geradores Candidatos com Excedente Operacional")

                colunas_usinas = {
                    'mwh_disponivel': 'mwh',
                    'pld_medio': 'brl',
                    'atendimento_demanda_pct': 'pct',
                }

                df_usinas_display = resultado.usinas_oferta[[
                    'nom_usina', 'mwh_disponivel', 'pld_medio',
                    'atendimento_demanda_pct', 'horas_com_restricao',
                    'custo_total_restricao'
                ]].head(10).copy()

                df_usinas_display = df_usinas_display.rename(columns={
                    'mwh_disponivel': 'MWh Disponível (Mês)',
                    'pld_medio': 'PLD Médio (R$/MWh)',
                    'atendimento_demanda_pct': '% Atendimento Carga',
                    'horas_com_restricao': 'Horas c/ Restrição',
                    'custo_total_restricao': 'Custo Restrição Total (R$)'
                })

                renderizar_tabela_formatada(
                    df_usinas_display,
                    {
                        'MWh Disponível (Mês)': 'mwh',
                        'PLD Médio (R$/MWh)': 'brl',
                        '% Atendimento Carga': 'pct',
                        'Custo Restrição Total (R$)': 'brl',
                    },
                    altura=350
                )

                # --------------------------------------------------
                # IMPACTO ESG
                # --------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                renderizar_info_card(
                    "🌱 Impacto ESG Estimado",
                    f"Utilizando a energia renovável restrita deste match, seu empreendimento "
                    f"evita a emissão de **{formatar_numero_br(resultado.co2_evitado_ton_ano, 1)} "
                    f"toneladas de CO₂** por ano. "
                    f"(Fator de emissão: {FATOR_EMISSAO_CO2_TON_POR_MWH} tCO₂/MWh — média brasileira)",
                    tipo="success"
                )

                # --------------------------------------------------
                # EXPORTAÇÃO TERM SHEET
                # --------------------------------------------------
                st.markdown("---")
                renderizar_section_header("📄", "Exportar Term Sheet Comercial")

                df_export = preparar_dados_exportacao(resultado, perfil)

                csv_data = df_export.to_csv(index=False, sep=';').encode('utf-8')

                st.download_button(
                    label="📥 Baixar Relatório de Match & Viabilidade (CSV)",
                    data=csv_data,
                    file_name=(
                        f"termsheet_reenergia_"
                        f"{tipo_projeto.replace(' ', '_').replace('/', '-')}_"
                        f"{regiao_pref}.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    type="primary",
                    help="Arquivo CSV com detalhes do match, usinas candidatas e projeções financeiras"
                )

                with st.expander("👁️ Visualizar dados do Term Sheet", expanded=False):
                    st.dataframe(df_export, use_container_width=True, hide_index=True)


# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8B949E; font-size: 0.85rem; padding: 1rem;">
    ⚡ <strong>ReEnergia</strong> — Transformando curtailment em oportunidade<br>
    Hackathon ProEnergia | Dados: ONS, CCEE, ANEEL SIGA
</div>
""", unsafe_allow_html=True)