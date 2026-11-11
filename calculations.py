"""
Módulo de cálculos e regras de negócio para o ReEnergia.

Contém a lógica do Matchmaker, cálculos financeiros, análises de sensibilidade
e métricas de ESG/CO2.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


# Constantes de negócio
FATOR_EMISSAO_CO2_TON_POR_MWH = 0.04  # tCO2/MWh - fator médio brasileiro


@dataclass
class PerfilInvestidor:
    """Perfil do investidor/projeto para o matchmaker."""
    tipo_projeto: str
    subsistema_preferido: str
    carga_mw: float
    perfil_operacao: str  # "24/7", "Noturno", "Diurno"
    tarifa_baseline: float
    desconto_alvo_pct: int


@dataclass
class ResultadoMatch:
    """Resultado do processamento de match."""
    demanda_mensal_mwh: float
    preco_oferta_mwh: float
    custo_baseline_mensal: float
    custo_match_mensal: float
    economia_mensal: float
    economia_anual: float
    co2_evitado_ton_ano: float
    receita_gerador_anual: float
    usinas_oferta: pd.DataFrame
    cenario_agressivo: float
    cenario_base: float
    cenario_conservador: float


def calcular_horas_mes(perfil_operacao: str) -> int:
    """
    Calcula horas mensais baseadas no perfil de operação.

    Args:
        perfil_operacao: "24/7 (Ininterrupto)", "Noturno (18h às 06h)", "Diurno (06h às 18h)"

    Returns:
        Horas por mês
    """
    if "24/7" in perfil_operacao or "Ininterrupto" in perfil_operacao:
        return 720  # 30 dias * 24h
    elif "Noturno" in perfil_operacao:
        return 360  # 30 dias * 12h
    elif "Diurno" in perfil_operacao:
        return 360  # 30 dias * 12h
    return 720


def processar_match(
    df_restricao: pd.DataFrame,
    perfil: PerfilInvestidor
) -> Optional[ResultadoMatch]:
    """
    Processa o match entre demanda do investidor e excedente de geração.

    Args:
        df_restricao: DataFrame com dados de restrição diária
        perfil: Perfil do investidor

    Returns:
        ResultadoMatch com todos os cálculos, ou None se não houver match
    """
    # Filtrar por subsistema
    df_match = df_restricao[
        df_restricao['nom_subsistema'] == perfil.subsistema_preferido
    ].copy()

    if df_match.empty:
        return None

    # Agregar por usina
    usinas_oferta = df_match.groupby(['nom_usina']).agg(
        mwh_disponivel=('mwh_restrito', 'sum'),
        pld_medio=('pld_medio', 'mean'),
        custo_total_restricao=('custo_restricao_rs', 'sum'),
        horas_com_restricao=('horas_com_restricao', 'sum'),
    ).reset_index()

    # Se nenhuma usina tem restrição > 0
    if usinas_oferta['mwh_disponivel'].sum() == 0:
        return None

    # Calcular horas por mês baseadas no perfil
    horas_mes = calcular_horas_mes(perfil.perfil_operacao)
    demanda_mensal_mwh = perfil.carga_mw * horas_mes

    # Preço da oferta (com desconto sobre baseline)
    preco_oferta_mwh = perfil.tarifa_baseline * (1 - (perfil.desconto_alvo_pct / 100))

    # Custos
    custo_baseline_mensal = demanda_mensal_mwh * perfil.tarifa_baseline
    custo_match_mensal = demanda_mensal_mwh * preco_oferta_mwh
    economia_mensal = custo_baseline_mensal - custo_match_mensal
    economia_anual = economia_mensal * 12

    # Receita do gerador (o que a usina receberia)
    receita_gerador_anual = custo_match_mensal * 12

    # CO2 evitado
    co2_evitado_ton_ano = (demanda_mensal_mwh * 12) * FATOR_EMISSAO_CO2_TON_POR_MWH

    # Análise de sensibilidade (±20%)
    cenario_agressivo = economia_anual * 1.2
    cenario_base = economia_anual
    cenario_conservador = economia_anual * 0.8

    # Calcular % de atendimento da demanda por usina
    usinas_oferta['atendimento_demanda_pct'] = (
        (usinas_oferta['mwh_disponivel'] / demanda_mensal_mwh) * 100
    ).clip(upper=100)

    # Ordenar por maior volume disponível
    usinas_oferta = usinas_oferta.sort_values(
        by='mwh_disponivel', ascending=False
    ).reset_index(drop=True)

    return ResultadoMatch(
        demanda_mensal_mwh=demanda_mensal_mwh,
        preco_oferta_mwh=preco_oferta_mwh,
        custo_baseline_mensal=custo_baseline_mensal,
        custo_match_mensal=custo_match_mensal,
        economia_mensal=economia_mensal,
        economia_anual=economia_anual,
        co2_evitado_ton_ano=co2_evitado_ton_ano,
        receita_gerador_anual=receita_gerador_anual,
        usinas_oferta=usinas_oferta,
        cenario_agressivo=cenario_agressivo,
        cenario_base=cenario_base,
        cenario_conservador=cenario_conservador,
    )


def formatar_brl(valor: float, compacto: bool = False) -> str:
    """
    Formata valor em Reais (BRL) padrão brasileiro.

    Args:
        valor: Valor numérico
        compacto: Se True, usa formato compacto (ex: 1,2 mi)

    Returns:
        String formatada
    """
    if compacto:
        if abs(valor) >= 1_000_000_000:
            return f"R$ {valor/1_000_000_000:.1f} bi"
        elif abs(valor) >= 1_000_000:
            return f"R$ {valor/1_000_000:.1f} mi"
        elif abs(valor) >= 1_000:
            return f"R$ {valor/1_000:.1f} mil"
        else:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Formato completo: 1.234.567,89
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero_br(valor: float, casas_decimais: int = 2) -> str:
    """
    Formata número no padrão brasileiro (ponto como separador de milhar, vírgula decimal).

    Args:
        valor: Valor numérico
        casas_decimais: Número de casas decimais

    Returns:
        String formatada
    """
    fmt = f"{{:,.{casas_decimais}f}}"
    return fmt.format(valor).replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_kpis_geracao(df_ger: pd.DataFrame) -> Dict[str, Any]:
    """Calcula KPIs principais da visão de geração."""
    return {
        'total_mwh': df_ger['mwh_gerado'].sum(),
        'media_diaria_mwh': df_ger.groupby('data')['mwh_gerado'].sum().mean(),
        'n_usinas': df_ger['nom_usina'].nunique(),
        'n_subsistemas': df_ger['nom_subsistema'].nunique(),
        'geracao_max_mw': df_ger['geracao_max_mw'].max(),
        'periodo_inicio': df_ger['data'].min(),
        'periodo_fim': df_ger['data'].max(),
    }


def calcular_kpis_restricao(df_rest: pd.DataFrame) -> Dict[str, Any]:
    """Calcula KPIs principais da visão de restrição."""
    return {
        'total_mwh_restrito': df_rest['mwh_restrito'].sum(),
        'custo_total_rs': df_rest['custo_restricao_rs'].sum(),
        'pld_medio': df_rest['pld_medio'].mean(),
        'pct_medio_restricao': df_rest['pct_restricao'].mean(),
        'n_usinas_com_restricao': df_rest[df_rest['mwh_restrito'] > 0]['nom_usina'].nunique(),
        'periodo_inicio': df_rest['data'].min(),
        'periodo_fim': df_rest['data'].max(),
    }


def preparar_dados_exportacao(
    resultado: ResultadoMatch,
    perfil: PerfilInvestidor
) -> pd.DataFrame:
    """
    Prepara DataFrame para exportação do Term Sheet.
    """
    df_export = resultado.usinas_oferta[[
        'nom_usina', 'mwh_disponivel', 'pld_medio', 'atendimento_demanda_pct'
    ]].copy()

    df_export['tarifa_proposta_mwh'] = resultado.preco_oferta_mwh
    df_export['economia_mensal_estimada'] = resultado.economia_mensal
    df_export['tipo_projeto'] = perfil.tipo_projeto
    df_export['subsistema'] = perfil.subsistema_preferido
    df_export['carga_mw'] = perfil.carga_mw
    df_export['perfil_operacao'] = perfil.perfil_operacao
    df_export['desconto_pct'] = perfil.desconto_alvo_pct

    return df_export