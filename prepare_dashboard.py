"""
prepare_dashboard.py  (Sprint 2/3)

Recebe o dicionário de DataFrames do Sprint 1 (data_pipeline.main()):
    {'cadastro', 'pld', 'geracao', 'restricao'}
cruza as bases, calcula o custo da restrição (constrained-off) e reduz a
granularidade de HORA -> DIA para alimentar o dashboard sem travar.

Saídas (parquet, em data/):
    data/dash_geracao_diaria.parquet
    data/dash_restricao_diaria.parquet

Decisões de negócio / técnicas:
  * Geração (2023) e Restrição (2026) são processadas em pipelines independentes,
    preservando cada janela temporal (nenhum join entre elas pela data).
  * PLD só é cruzado com Restrição (mesma janela, 2026). Geração NÃO recebe PLD.
  * Dados sub-horários (ex.: 30 min) são colapsados por MÉDIA de MW dentro da hora
    (MW médio x 1h = MWh), evitando dupla contagem de MWh.
  * O enriquecimento com o cadastro é feito sobre a lista de usinas únicas e o
    resultado é ligado à base diária (equivalente ao left join linha a linha, mas
    muito mais barato). Cadastro é deduplicado por chave para não multiplicar linhas.
  * Chave de junção: nome da usina normalizado (sem acento, maiúsculo). Fallback
    para o CEG (ceg <-> idenucleoceg) quando o nome não casa (apenas geração).
"""

import logging
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)

DATA_DIR = Path("data")

ATTRS_CADASTRO = ["latitude", "longitude", "tipo_geracao", "potencia_kw"]

SUBSISTEMA_MAP = {
    "SUDESTE": "SUDESTE",
    "SUDESTE/CENTRO-OESTE": "SUDESTE",
    "SE/CO": "SUDESTE",
    "SECO": "SUDESTE",
    "SE": "SUDESTE",
    "SUL": "SUL",
    "S": "SUL",
    "NORDESTE": "NORDESTE",
    "NE": "NORDESTE",
    "NORTE": "NORTE",
    "N": "NORTE",
}


# --------------------------------------------------------------------------- #
# Utilitários
# --------------------------------------------------------------------------- #
def _norm_texto(valor):
    """Maiúsculo, sem acentos e sem espaços duplicados."""
    if pd.isna(valor):
        return None
    s = unicodedata.normalize("NFKD", str(valor))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).strip().upper()


def _norm_serie(serie: pd.Series) -> pd.Series:
    """Normaliza texto aplicando a função apenas aos valores únicos (rápido)."""
    mapa = {u: _norm_texto(u) for u in serie.dropna().unique()}
    return serie.map(mapa)


def _norm_subsistema(serie: pd.Series) -> pd.Series:
    norm = _norm_serie(serie)
    return norm.map(lambda x: SUBSISTEMA_MAP.get(x, x) if isinstance(x, str) else x)


def _exigir_colunas(df: pd.DataFrame, colunas, nome: str):
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Tabela '{nome}' sem as colunas obrigatórias: {faltantes}")


def _tabela_vazia(dfs: dict, chave: str) -> bool:
    df = dfs.get(chave)
    return df is None or not isinstance(df, pd.DataFrame) or df.empty


def _colapsar_horario(df: pd.DataFrame, chaves: list, valores: list) -> pd.DataFrame:
    """Garante 1 linha por (timestamp, chaves) usando média de MW dentro da hora."""
    return (
        df.groupby(chaves, observed=True, sort=False)[valores]
        .mean()
        .reset_index()
    )


# --------------------------------------------------------------------------- #
# Cadastro (dimensão de usinas)
# --------------------------------------------------------------------------- #
def _preparar_cadastro(cadastro: pd.DataFrame):
    """Retorna (lookup_por_nome, lookup_por_ceg), ambos deduplicados."""
    _exigir_colunas(cadastro, ["nom_usina"], "cadastro")
    logging.info("Preparando dimensão de CADASTRO (%d linhas)...", len(cadastro))

    c = cadastro.copy()
    c["nom_usina"] = _norm_serie(c["nom_usina"])
    c = c.rename(
        columns={
            "numcoordnempreendimento": "latitude",
            "numcoordeempreendimento": "longitude",
            "sigtipogeracao": "tipo_geracao",
            "mdapotenciafiscalizadakw": "potencia_kw",
            "idenucleoceg": "ceg_key",
        }
    )
    for col in ATTRS_CADASTRO:
        if col not in c.columns:
            c[col] = np.nan

    # Coordenadas fora do território brasileiro viram NaN (evita lixo no mapa)
    lat_ok = c["latitude"].between(-35, 6)
    lon_ok = c["longitude"].between(-75, -30)
    invalidas = int((~(lat_ok & lon_ok) & c["latitude"].notna()).sum())
    if invalidas:
        logging.warning("  %d usinas com coordenadas fora do Brasil -> NaN", invalidas)
    c.loc[~(lat_ok & lon_ok), ["latitude", "longitude"]] = np.nan

    # Prioriza a maior potência ao deduplicar
    c = c.sort_values("potencia_kw", ascending=False, na_position="last")

    por_nome = (
        c.dropna(subset=["nom_usina"])
        .drop_duplicates("nom_usina")[["nom_usina"] + ATTRS_CADASTRO]
        .reset_index(drop=True)
    )

    if "ceg_key" in c.columns:
        c["ceg_key"] = c["ceg_key"].astype("string").str.strip().str.upper()
        por_ceg = (
            c.dropna(subset=["ceg_key"])
            .drop_duplicates("ceg_key")[["ceg_key"] + ATTRS_CADASTRO]
            .set_index("ceg_key")
        )
    else:
        por_ceg = pd.DataFrame(columns=ATTRS_CADASTRO)

    logging.info(
        "  Cadastro únicos: %d por nome | %d por CEG", len(por_nome), len(por_ceg)
    )
    return por_nome, por_ceg


def _enriquecer_com_cadastro(
    diario: pd.DataFrame,
    por_nome: pd.DataFrame,
    por_ceg: pd.DataFrame,
    ceg_por_usina: dict = None,
    rotulo: str = "",
) -> pd.DataFrame:
    """Left join com o cadastro (lat, lon, tipo, potência) via usinas únicas."""
    usinas = diario[["nom_usina"]].drop_duplicates().reset_index(drop=True)
    usinas = usinas.merge(por_nome, on="nom_usina", how="left")

    # Fallback por CEG (quando o nome não casou)
    if ceg_por_usina and len(por_ceg):
        sem_match = usinas["tipo_geracao"].isna() & usinas["latitude"].isna()
        if sem_match.any():
            ceg = usinas.loc[sem_match, "nom_usina"].map(ceg_por_usina)
            recuperadas = 0
            for col in ATTRS_CADASTRO:
                valores = ceg.map(por_ceg[col])
                usinas.loc[sem_match, col] = valores.values
            recuperadas = int(
                (usinas.loc[sem_match, "latitude"].notna()).sum()
            )
            logging.info("  [%s] Recuperadas %d usinas via CEG", rotulo, recuperadas)

    total = len(usinas)
    sem_coord = int(usinas["latitude"].isna().sum())
    logging.info(
        "  [%s] Usinas únicas: %d | sem coordenadas no cadastro: %d (%.1f%%)",
        rotulo, total, sem_coord, 100 * sem_coord / max(total, 1),
    )
    if sem_coord:
        exemplos = usinas.loc[usinas["latitude"].isna(), "nom_usina"].head(10).tolist()
        logging.info("  [%s] Exemplos sem match: %s", rotulo, exemplos)

    return diario.merge(usinas, on="nom_usina", how="left")


# --------------------------------------------------------------------------- #
# Geração (2023) -> diário
# --------------------------------------------------------------------------- #
def _agregar_geracao_diaria(geracao, por_nome, por_ceg) -> pd.DataFrame:
    _exigir_colunas(
        geracao, ["timestamp", "nom_usina", "nom_subsistema", "val_geracao"], "geracao"
    )
    logging.info("GERAÇÃO: %d linhas horárias de entrada", len(geracao))

    cols = ["timestamp", "nom_usina", "nom_subsistema", "val_geracao"]
    if "ceg" in geracao.columns:
        cols.append("ceg")
    g = geracao[cols].copy()

    g["nom_usina"] = _norm_serie(g["nom_usina"])
    g["nom_subsistema"] = _norm_subsistema(g["nom_subsistema"])
    g = g.dropna(subset=["timestamp", "nom_usina", "nom_subsistema"])

    ceg_por_usina = None
    if "ceg" in g.columns:
        tmp = g[["nom_usina", "ceg"]].dropna().drop_duplicates("nom_usina")
        ceg_por_usina = dict(
            zip(tmp["nom_usina"], tmp["ceg"].astype(str).str.strip().str.upper())
        )
        g = g.drop(columns="ceg")

    g["nom_usina"] = g["nom_usina"].astype("category")
    g["nom_subsistema"] = g["nom_subsistema"].astype("category")

    logging.info("  Colapsando para 1 linha por hora/usina...")
    g = _colapsar_horario(g, ["timestamp", "nom_subsistema", "nom_usina"], ["val_geracao"])
    logging.info("  Linhas após colapso horário: %d", len(g))

    g["data"] = g["timestamp"].dt.normalize()
    logging.info("  Agregando HORA -> DIA (data, subsistema, usina)...")
    diario = (
        g.groupby(["data", "nom_subsistema", "nom_usina"], observed=True, sort=False)
        .agg(
            mwh_gerado=("val_geracao", "sum"),
            geracao_media_mw=("val_geracao", "mean"),
            geracao_max_mw=("val_geracao", "max"),
            horas_registradas=("val_geracao", "count"),
        )
        .reset_index()
    )
    diario["nom_usina"] = diario["nom_usina"].astype(str)
    diario["nom_subsistema"] = diario["nom_subsistema"].astype(str)

    diario = _enriquecer_com_cadastro(
        diario, por_nome, por_ceg, ceg_por_usina, rotulo="geracao"
    )
    diario = diario.sort_values(["data", "nom_subsistema", "nom_usina"]).reset_index(drop=True)
    logging.info(
        "GERAÇÃO diária pronta: %s | período %s -> %s",
        diario.shape, diario["data"].min(), diario["data"].max(),
    )
    return diario


# --------------------------------------------------------------------------- #
# Restrição (2026) + PLD -> diário
# --------------------------------------------------------------------------- #
def _preparar_pld_horario(pld: pd.DataFrame) -> pd.DataFrame:
    _exigir_colunas(pld, ["timestamp", "submercado", "valor_pld"], "pld")
    p = pld[["timestamp", "submercado", "valor_pld"]].copy()
    p["nom_subsistema"] = _norm_subsistema(p["submercado"])
    p = p.dropna(subset=["timestamp", "nom_subsistema"])
    p = (
        p.groupby(["timestamp", "nom_subsistema"], sort=False)["valor_pld"]
        .mean()
        .reset_index()
    )
    logging.info(
        "PLD horário preparado: %s | subsistemas: %s | período %s -> %s",
        p.shape, sorted(p["nom_subsistema"].unique().tolist()),
        p["timestamp"].min(), p["timestamp"].max(),
    )
    return p


def _agregar_restricao_diaria(restricao, pld, por_nome, por_ceg) -> pd.DataFrame:
    _exigir_colunas(
        restricao,
        ["timestamp", "nom_usina", "nom_subsistema", "val_geracaoverificada", "val_restricao"],
        "restricao",
    )
    logging.info("RESTRIÇÃO: %d linhas de entrada", len(restricao))

    r = restricao[
        ["timestamp", "nom_usina", "nom_subsistema", "val_geracaoverificada", "val_restricao"]
    ].copy()
    r["nom_usina"] = _norm_serie(r["nom_usina"])
    r["nom_subsistema"] = _norm_subsistema(r["nom_subsistema"])
    r = r.dropna(subset=["timestamp", "nom_usina", "nom_subsistema"])

    logging.info("  Colapsando para 1 linha por hora/usina (MW médio = MWh na hora)...")
    r = _colapsar_horario(
        r,
        ["timestamp", "nom_subsistema", "nom_usina"],
        ["val_geracaoverificada", "val_restricao"],
    )
    logging.info("  Linhas após colapso horário: %d", len(r))

    # --- Cruzamento com PLD (timestamp + subsistema) ---
    p = _preparar_pld_horario(pld)
    r = r.merge(p, on=["timestamp", "nom_subsistema"], how="left")
    sem_pld = int(r["valor_pld"].isna().sum())
    logging.info(
        "  Merge PLD: %d de %d linhas sem PLD (%.2f%%)",
        sem_pld, len(r), 100 * sem_pld / max(len(r), 1),
    )
    if sem_pld == len(r):
        logging.warning("  ATENÇÃO: nenhum PLD casou (verifique períodos/subsistemas).")

    # --- Feature engineering: custo da restrição (R$) ---
    r["custo_restricao_rs"] = r["val_restricao"] * r["valor_pld"]
    r["tem_restricao"] = (r["val_restricao"] > 0).astype("int8")
    r["sem_pld"] = r["valor_pld"].isna().astype("int8")

    # --- Agregação HORA -> DIA ---
    r["data"] = r["timestamp"].dt.normalize()
    r["nom_usina"] = r["nom_usina"].astype("category")
    r["nom_subsistema"] = r["nom_subsistema"].astype("category")

    logging.info("  Agregando HORA -> DIA (data, subsistema, usina)...")
    diario = (
        r.groupby(["data", "nom_subsistema", "nom_usina"], observed=True, sort=False)
        .agg(
            mwh_verificado=("val_geracaoverificada", "sum"),
            mwh_restrito=("val_restricao", "sum"),
            custo_restricao_rs=("custo_restricao_rs", "sum"),
            pld_medio=("valor_pld", "mean"),
            horas_com_restricao=("tem_restricao", "sum"),
            horas_sem_pld=("sem_pld", "sum"),
            horas_registradas=("val_restricao", "count"),
        )
        .reset_index()
    )
    diario["nom_usina"] = diario["nom_usina"].astype(str)
    diario["nom_subsistema"] = diario["nom_subsistema"].astype(str)

    potencial = diario["mwh_verificado"] + diario["mwh_restrito"]
    diario["mwh_potencial"] = potencial
    diario["pct_restricao"] = np.where(
        potencial > 0, 100 * diario["mwh_restrito"] / potencial, np.nan
    )

    diario = _enriquecer_com_cadastro(diario, por_nome, por_ceg, None, rotulo="restricao")
    diario = diario.sort_values(["data", "nom_subsistema", "nom_usina"]).reset_index(drop=True)
    logging.info(
        "RESTRIÇÃO diária pronta: %s | período %s -> %s | custo total R$ %.2f",
        diario.shape, diario["data"].min(), diario["data"].max(),
        diario["custo_restricao_rs"].sum(),
    )
    return diario


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #
def build_analytical_dataset(dfs: dict) -> dict:
    """
    Recebe o dicionário do Sprint 1 e devolve:
        {'geracao_diaria': DataFrame, 'restricao_diaria': DataFrame}
    """
    logging.info("=" * 70)
    logging.info("SPRINT 2: CONSTRUINDO DATASET ANALÍTICO")
    logging.info("=" * 70)

    saida = {"geracao_diaria": pd.DataFrame(), "restricao_diaria": pd.DataFrame()}

    # Cadastro (dimensão)
    if _tabela_vazia(dfs, "cadastro"):
        logging.warning("Cadastro vazio/ausente: dados sairão sem lat/lon/tipo.")
        por_nome = pd.DataFrame(columns=["nom_usina"] + ATTRS_CADASTRO)
        por_ceg = pd.DataFrame(columns=ATTRS_CADASTRO)
    else:
        try:
            por_nome, por_ceg = _preparar_cadastro(dfs["cadastro"])
        except Exception as e:  # noqa: BLE001
            logging.error("Falha ao preparar cadastro: %s: %s", type(e).__name__, e)
            por_nome = pd.DataFrame(columns=["nom_usina"] + ATTRS_CADASTRO)
            por_ceg = pd.DataFrame(columns=ATTRS_CADASTRO)

    # Geração
    logging.info("-" * 70)
    if _tabela_vazia(dfs, "geracao"):
        logging.warning("Tabela 'geracao' vazia/ausente: pulando.")
    else:
        try:
            saida["geracao_diaria"] = _agregar_geracao_diaria(dfs["geracao"], por_nome, por_ceg)
        except Exception as e:  # noqa: BLE001
            logging.error("Falha na geração diária: %s: %s", type(e).__name__, e)

    # Restrição + PLD
    logging.info("-" * 70)
    if _tabela_vazia(dfs, "restricao"):
        logging.warning("Tabela 'restricao' vazia/ausente: pulando.")
    elif _tabela_vazia(dfs, "pld"):
        logging.warning("Tabela 'pld' vazia/ausente: restrição sairá sem custo financeiro.")
        try:
            pld_vazio = pd.DataFrame(
                {"timestamp": pd.to_datetime([]), "submercado": [], "valor_pld": []}
            )
            saida["restricao_diaria"] = _agregar_restricao_diaria(
                dfs["restricao"], pld_vazio, por_nome, por_ceg
            )
        except Exception as e:  # noqa: BLE001
            logging.error("Falha na restrição diária: %s: %s", type(e).__name__, e)
    else:
        try:
            saida["restricao_diaria"] = _agregar_restricao_diaria(
                dfs["restricao"], dfs["pld"], por_nome, por_ceg
            )
        except Exception as e:  # noqa: BLE001
            logging.error("Falha na restrição diária: %s: %s", type(e).__name__, e)

    return saida


def export_parquet(datasets: dict, out_dir: Path = DATA_DIR) -> dict:
    """Salva as visões agregadas em parquet e loga o shape final."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    destinos = {
        "geracao_diaria": out_dir / "dash_geracao_diaria.parquet",
        "restricao_diaria": out_dir / "dash_restricao_diaria.parquet",
    }

    logging.info("=" * 70)
    logging.info("EXPORTANDO PARQUET")
    caminhos = {}
    for nome, caminho in destinos.items():
        df = datasets.get(nome)
        if df is None or df.empty:
            logging.warning("%s vazio: nada exportado.", nome)
            continue
        try:
            df.to_parquet(caminho, index=False, compression="snappy")
            tamanho_mb = caminho.stat().st_size / 1024**2
            logging.info(
                "Exportado %s | shape final: %s | %.2f MB | colunas: %s",
                caminho, df.shape, tamanho_mb, list(df.columns),
            )
            caminhos[nome] = caminho
        except ImportError:
            logging.error("Instale um engine parquet: pip install pyarrow")
        except Exception as e:  # noqa: BLE001
            logging.error("Falha ao exportar %s: %s: %s", nome, type(e).__name__, e)
    return caminhos


def main(dfs: dict = None) -> dict:
    if dfs is None:
        logging.info("Nenhum dicionário recebido: executando o pipeline do Sprint 1...")
        from data_pipeline import main as rodar_pipeline

        dfs = rodar_pipeline()

    datasets = build_analytical_dataset(dfs)
    export_parquet(datasets)
    logging.info("SPRINT 2 FINALIZADO.")
    return datasets


if __name__ == "__main__":
    main()