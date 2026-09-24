"""
data_pipeline.py
Pipeline defensivo de leitura e limpeza de dados do mercado de energia (ONS/CCEE).

Tipos de tabela tratados (todos CSV com sep=';' dentro de data/):
  1. CADASTRO  -> idenucleoceg, nomempreendimento, ...
  2. PLD       -> data_hora, submercado, valor_pld
  3. GERACAO   -> din_instante, id_subsistema, ..., ceg, val_geracao
  4. RESTRICAO -> data_hora, nom_usina, nom_subsistema, val_geracaoverificada, val_restricao, ...
"""

import logging
import sys
import traceback
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuração
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
SEP = ";"
ENCODINGS = ("utf-8", "utf-8-sig", "latin-1")  # tentativas em ordem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("pipeline")


# --------------------------------------------------------------------------- #
# Utilitários genéricos
# --------------------------------------------------------------------------- #
def _read_csv_robusto(path: Path, **kwargs) -> pd.DataFrame:
    """Lê CSV com sep=';' tentando múltiplos encodings."""
    ultimo_erro = None
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, sep=SEP, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            ultimo_erro = e
            log.warning("  Encoding %s falhou em %s, tentando o próximo...", enc, path.name)
    raise ultimo_erro if ultimo_erro else RuntimeError(f"Falha ao ler {path}")


def _padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espaços das extremidades e converte nomes de colunas para minúsculas."""
    df.columns = df.columns.str.strip().str.lower()
    return df


def _unificar_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia 'data_hora'/'din_instante' para 'timestamp' e trata o tempo."""
    df = df.rename(columns={"data_hora": "timestamp", "din_instante": "timestamp"})

    if "timestamp" not in df.columns:
        return df

    # Se por acaso existirem duas colunas 'timestamp', mantém a primeira
    if isinstance(df["timestamp"], pd.DataFrame):
        log.warning("  Colunas 'timestamp' duplicadas; mantendo a primeira.")
        df = df.loc[:, ~df.columns.duplicated()]

    ts = pd.to_datetime(df["timestamp"], errors="coerce")

    # Caso venha como object (offsets mistos), força UTC e depois remove timezone
    if not pd.api.types.is_datetime64_any_dtype(ts):
        log.warning("  Timestamp com tipo misto; convertendo via UTC.")
        ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_localize(None)

    df["timestamp"] = ts.dt.floor("h")

    n_nat = int(df["timestamp"].isna().sum())
    if n_nat:
        log.warning("  %d linhas com timestamp inválido (NaT) — serão descartadas.", n_nat)
        df = df.dropna(subset=["timestamp"])
    return df


def _para_numerico(df: pd.DataFrame, colunas) -> pd.DataFrame:
    """Converte colunas para numérico, tolerando vírgula decimal."""
    for c in colunas:
        if c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip().str.replace(",", ".", regex=False)
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _limpar_strings(df: pd.DataFrame, colunas) -> pd.DataFrame:
    for c in colunas:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()
    return df


# --------------------------------------------------------------------------- #
# Identificação do tipo de arquivo (pelo cabeçalho)
# --------------------------------------------------------------------------- #
def identificar_tipo(path: Path) -> str:
    """Retorna 'cadastro', 'pld', 'geracao', 'restricao' ou 'desconhecido'."""
    header = None
    for enc in ENCODINGS:
        try:
            header = pd.read_csv(path, sep=SEP, encoding=enc, nrows=0)
            break
        except UnicodeDecodeError:
            continue
    if header is None:
        return "desconhecido"

    cols = set(header.columns.str.strip().str.lower())

    if {"idenucleoceg", "nomempreendimento"} <= cols:
        return "cadastro"
    if {"valor_pld", "submercado"} <= cols:
        return "pld"
    if {"val_geracaoverificada", "val_restricao"} <= cols:
        return "restricao"
    if {"val_geracao", "din_instante"} <= cols:
        return "geracao"
    return "desconhecido"


# --------------------------------------------------------------------------- #
# Funções de leitura/limpeza por tipo
# --------------------------------------------------------------------------- #
def ler_cadastro(path: Path) -> pd.DataFrame:
    log.info("Lendo CADASTRO DE USINAS: %s", path.name)
    df = _read_csv_robusto(path)
    log.info("  Linhas brutas: %d | Colunas brutas: %s", len(df), list(df.columns))

    df = _padronizar_colunas(df)
    df = df.rename(columns={"nomempreendimento": "nom_usina"})
    df = _limpar_strings(df, ["idenucleoceg", "nom_usina", "sigtipogeracao"])
    df = _para_numerico(
        df, ["numcoordnempreendimento", "numcoordeempreendimento", "mdapotenciafiscalizadakw"]
    )
    df = df.drop_duplicates()

    log.info("  Total de linhas CADASTRO: %d", len(df))
    log.info("  Colunas após limpeza: %s", list(df.columns))
    return df


def ler_pld(path: Path) -> pd.DataFrame:
    log.info("Lendo PLD: %s", path.name)
    df = _read_csv_robusto(path)
    log.info("  Linhas brutas: %d | Colunas brutas: %s", len(df), list(df.columns))

    df = _padronizar_colunas(df)
    df = _unificar_timestamp(df)
    df = _limpar_strings(df, ["submercado"])
    df = _para_numerico(df, ["valor_pld"])
    df = df.drop_duplicates()

    log.info("  Total de linhas PLD: %d", len(df))
    log.info("  Colunas após limpeza: %s", list(df.columns))
    return df


def ler_geracao(path: Path) -> pd.DataFrame:
    log.info("Lendo GERAÇÃO (ONS): %s", path.name)
    df = _read_csv_robusto(path)
    log.info("  Linhas brutas: %d | Colunas brutas: %s", len(df), list(df.columns))

    df = _padronizar_colunas(df)
    df = _unificar_timestamp(df)
    df = _limpar_strings(df, ["nom_usina", "nom_subsistema", "nom_estado", "ceg", "id_ons"])
    df = _para_numerico(df, ["val_geracao"])
    df = df.drop_duplicates()

    log.info("  Total de linhas GERAÇÃO: %d", len(df))
    log.info("  Colunas após limpeza: %s", list(df.columns))
    return df


def ler_restricao(path: Path) -> pd.DataFrame:
    log.info("Lendo GERAÇÃO VERIFICADA / RESTRIÇÃO: %s", path.name)
    df = _read_csv_robusto(path)
    log.info("  Linhas brutas: %d | Colunas brutas: %s", len(df), list(df.columns))

    df = _padronizar_colunas(df)
    df = _unificar_timestamp(df)
    df = _limpar_strings(df, ["nom_usina", "nom_subsistema", "dsc_motivo_restricao"])
    df = _para_numerico(df, ["val_geracaoverificada", "val_restricao"])
    df = df.drop_duplicates()

    log.info("  Total de linhas RESTRIÇÃO: %d", len(df))
    log.info("  Colunas após limpeza: %s", list(df.columns))
    return df


LEITORES = {
    "cadastro": ler_cadastro,
    "pld": ler_pld,
    "geracao": ler_geracao,
    "restricao": ler_restricao,
}


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> dict:
    log.info("=" * 70)
    log.info("INICIANDO PIPELINE DE DADOS")
    log.info("Diretório de dados: %s", DATA_DIR.resolve())
    log.info("=" * 70)

    if not DATA_DIR.exists():
        log.error("Diretório '%s' não encontrado. Abortando.", DATA_DIR)
        return {}

    arquivos = sorted(
        {p for p in DATA_DIR.rglob("*") if p.is_file() and p.suffix.lower() == ".csv"}
    )
    log.info("Arquivos CSV encontrados: %d", len(arquivos))

    acumulado = {k: [] for k in LEITORES}
    ignorados = []

    for path in arquivos:
        log.info("-" * 70)
        try:
            tipo = identificar_tipo(path)
            log.info("Arquivo: %s -> tipo identificado: %s", path.name, tipo.upper())

            if tipo == "desconhecido":
                log.warning("  Tipo desconhecido, ignorando: %s", path.name)
                ignorados.append((path.name, "tipo desconhecido"))
                continue

            df = LEITORES[tipo](path)
            df["arquivo_origem"] = path.name
            acumulado[tipo].append(df)

        except Exception as e:  # noqa: BLE001 - defensivo de propósito
            log.error("  ERRO ao processar %s: %s: %s", path.name, type(e).__name__, e)
            log.debug(traceback.format_exc())
            ignorados.append((path.name, f"{type(e).__name__}: {e}"))
            continue

    # Consolida por tipo
    log.info("=" * 70)
    log.info("CONSOLIDANDO DATAFRAMES POR TIPO")
    resultado = {}
    for tipo, lista in acumulado.items():
        if not lista:
            log.warning("Nenhum arquivo válido para o tipo %s.", tipo.upper())
            resultado[tipo] = pd.DataFrame()
            continue
        try:
            df = pd.concat(lista, ignore_index=True)
            resultado[tipo] = df
            log.info(
                "%-10s | arquivos: %d | linhas: %d | colunas: %s",
                tipo.upper(), len(lista), len(df), list(df.columns),
            )
        except Exception as e:  # noqa: BLE001
            log.error("Falha ao consolidar %s: %s", tipo, e)
            resultado[tipo] = pd.DataFrame()

    # Resumo final
    log.info("=" * 70)
    log.info("RESUMO FINAL")
    for tipo, df in resultado.items():
        if df.empty:
            log.info("  %-10s: VAZIO", tipo.upper())
            continue
        msg = f"  {tipo.upper():<10}: {len(df):>10} linhas"
        if "timestamp" in df.columns:
            msg += f" | período: {df['timestamp'].min()} -> {df['timestamp'].max()}"
        log.info(msg)

    if ignorados:
        log.warning("Arquivos ignorados (%d):", len(ignorados))
        for nome, motivo in ignorados:
            log.warning("  - %s: %s", nome, motivo)

    log.info("PIPELINE FINALIZADO.")
    return resultado


if __name__ == "__main__":
    dfs = main()
    import pandas as pd

def gerar_master(dfs: dict):
    # 1. Preparar a base principal (Geração + Restrição usando outer join por causa das datas diferentes)
    log.info("Iniciando merge das bases...")
    df_ger = dfs['geracao']
    df_rest = dfs['restricao']
    
    # Merge usando timestamp, nom_subsistema e nom_usina
    chaves_merge = ['timestamp', 'nom_usina', 'nom_subsistema']
    
    # Fazendo outer join para não perder dados de 2023 (Geração) nem de 2026 (Restrição)
    master = pd.merge(df_ger, df_rest, on=chaves_merge, how='outer', suffixes=('_ger', '_rest'))
    
    # 2. Trazer o PLD (cruzando por timestamp e submercado/subsistema)
    # Primeiro garantimos que o nome da chave seja o mesmo
    df_pld = dfs['pld'].rename(columns={'submercado': 'nom_subsistema'})
    master = pd.merge(master, df_pld, on=['timestamp', 'nom_subsistema'], how='left')
    
    # 3. Trazer o Cadastro ANEEL (cruzando pelo nome da usina)
    df_cad = dfs['cadastro']
    master = pd.merge(master, df_cad, on='nom_usina', how='left')
    
    log.info(f"MASTER DATASET CRIADO: {len(master)} linhas e {len(master.columns)} colunas")
    
    # Salvar para usar no modelo de ML ou Dashboard
    caminho_saida = "data/master_dataset_final.parquet" # Parquet salva 10x mais rápido que CSV
    master.to_parquet(caminho_saida, index=False)
    log.info(f"Arquivo salvo com sucesso em: {caminho_saida}")
    
    return master

# Coloque isso lá no final do seu arquivo, no bloco if __name__ == '__main__':
# dfs = main()
# df_final = gerar_master(dfs)
    # Acesso rápido: dfs['cadastro'], dfs['pld'], dfs['geracao'], dfs['restricao']