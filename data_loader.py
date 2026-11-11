"""
Módulo de carregamento e cache de dados para o ReEnergia.

Responsável por carregar os datasets processados (Parquet) e fornecer
acesso otimizado via cache do Streamlit.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional


@st.cache_data(show_spinner="Carregando dados de geração e restrição...")
def carregar_dados_processados() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carrega os datasets agregados diários (geração 2023, restrição 2026).

    Returns:
        Tuple de (df_geracao_diaria, df_restricao_diaria)

    Raises:
        FileNotFoundError: Se os arquivos Parquet não existirem
    """
    caminho_geracao = Path("data/dash_geracao_diaria.parquet")
    caminho_restricao = Path("data/dash_restricao_diaria.parquet")

    if not caminho_geracao.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_geracao}. "
            "Execute o pipeline de dados (prepare_dashboard.py) primeiro."
        )
    if not caminho_restricao.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_restricao}. "
            "Execute o pipeline de dados (prepare_dashboard.py) primeiro."
        )

    df_ger = pd.read_parquet(caminho_geracao)
    df_rest = pd.read_parquet(caminho_restricao)

    # Garantir datetime
    df_ger['data'] = pd.to_datetime(df_ger['data'])
    df_rest['data'] = pd.to_datetime(df_rest['data'])

    return df_ger, df_rest


@st.cache_data(show_spinner="Obtendo lista de subsistemas...")
def obter_subsistemas_disponiveis(
    df_ger: pd.DataFrame,
    df_rest: pd.DataFrame
) -> List[str]:
    """Retorna lista ordenada de subsistemas únicos presentes nos datasets."""
    subs_ger = set(df_ger['nom_subsistema'].dropna().unique())
    subs_rest = set(df_rest['nom_subsistema'].dropna().unique())
    return sorted(subs_ger.union(subs_rest))


@st.cache_data(show_spinner="Filtrando dados por subsistema...")
def filtrar_por_subsistema(
    df_ger: pd.DataFrame,
    df_rest: pd.DataFrame,
    subsistemas_selecionados: List[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filtra ambos os dataframes pelos subsistemas selecionados."""
    if not subsistemas_selecionados:
        return df_ger.copy(), df_rest.copy()

    df_ger_filtrado = df_ger[df_ger['nom_subsistema'].isin(subsistemas_selecionados)].copy()
    df_rest_filtrado = df_rest[df_rest['nom_subsistema'].isin(subsistemas_selecionados)].copy()

    return df_ger_filtrado, df_rest_filtrado


@st.cache_data(show_spinner="Preparando dados para mapa...")
def preparar_dados_mapa(df_rest: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dados de restrição para visualização no mapa.
    Remove usinas sem coordenadas válidas.
    """
    df_mapa = df_rest.dropna(subset=['latitude', 'longitude']).copy()

    # Filtrar coordenadas fora do Brasil (sanity check)
    lat_ok = df_mapa['latitude'].between(-35, 6)
    lon_ok = df_mapa['longitude'].between(-75, -30)
    df_mapa = df_mapa[lat_ok & lon_ok].copy()

    return df_mapa


def obter_periodo_dados(df_ger: pd.DataFrame, df_rest: pd.DataFrame) -> dict:
    """Retorna informações sobre o período coberto pelos datasets."""
    return {
        'geracao_inicio': df_ger['data'].min(),
        'geracao_fim': df_ger['data'].max(),
        'restricao_inicio': df_rest['data'].min(),
        'restricao_fim': df_rest['data'].max(),
        'n_usinas_geracao': df_ger['nom_usina'].nunique(),
        'n_usinas_restricao': df_rest['nom_usina'].nunique(),
    }