import os
import re
import logging
import unicodedata
from typing import Optional, Dict
import pandas as pd
import numpy as np

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("DataPipeline")

COLUMN_ALIASES = {
    "timestamp": ["din_instante", "instante", "datahora", "data_hora", "timestamp", "hora", "dat_horario", "data"],
    "usina_id": ["id_ons", "cod_usina", "id_usina", "sigla_usina", "id_conjunto", "id_ponto_medicao"],
    "ceg": ["cod_ceg", "ceg", "codceg", "cd_ceg", "codempreendimento", "codigo_ceg"],
    "nome_usina": ["nom_usina", "nome_usina", "nom_usina_conjunto", "nom_conjuntousina", "nomempreendimento", "nome_empreendimento", "nom_conjunto"],
    "subsistema": ["id_subsistema", "subsistema", "submercado", "nom_subsistema", "id_submercado", "nom_submercado", "cod_submercado"],
    "geracao_mwh": ["val_geracaoverificada", "val_geracao", "geracao", "geracao_verificada", "val_geracaomwh", "val_gerverificada"],
    "corte_mwh": ["val_geracaolimitada", "val_restricao", "corte", "constrained_off", "cortes_mwh", "val_constrainedoff", "val_corte"],
    "pld": ["pld", "pld_hora", "val_pld", "preco", "val_pldhorario", "vlr_pld", "pld_mwh", "valor_pld", "pld_r_mwh"],
    "latitude": ["latitude", "num_coordenada_n", "numcoordnempreendimento", "lat", "num_latitude", "vlr_latitude"],
    "longitude": ["longitude", "num_coordenada_e", "numcoordeempreendimento", "lon", "lng", "num_longitude", "vlr_longitude"],
}

def clean_str(val) -> str:
    """Remove acentos, caracteres especiais e converte para minúsculas."""
    if pd.isna(val) or val is None:
        return ""
    s = unicodedata.normalize('NFKD', str(val)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
    return re.sub(r'[^a-z0-9]', '', s)

def normalize_subsistema(val) -> str:
    """Padroniza subsistemas para siglas canônicas: SE, S, NE, N."""
    s = str(val).upper().strip()
    if any(k in s for k in ["SUDESTE", "CENTRO", "SE", "1"]):
        return "SE"
    if any(k in s for k in ["SUL", "S", "2"]):
        return "S"
    if any(k in s for k in ["NORDESTE", "NE", "3"]):
        return "NE"
    if any(k in s for k in ["NORTE", "N", "4"]):
        return "N"
    return s

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapeia nomes de colunas usando a lista de aliases."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    mapping = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns and target not in mapping.values():
                mapping[alias] = target
                break
    return df.rename(columns=mapping)

def _build_usina_mapping(ger_df: pd.DataFrame, coff_df: pd.DataFrame, aneel_df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
    """Cria dicionário de mapeamento entre variações de nomes/siglas e a chave única da Geração."""
    # Coleta IDs e Nomes únicos da Geração (Nossa referência)
    ger_usinas = []
    for _, row in ger_df[["usina_id", "nome_usina"] if "nome_usina" in ger_df.columns else ["usina_id"]].drop_duplicates().iterrows():
        uid = str(row["usina_id"]).strip()
        uid_clean = clean_str(uid)
        name_clean = clean_str(row["nome_usina"]) if "nome_usina" in row and pd.notna(row["nome_usina"]) else ""
        ger_usinas.append({"uid": uid, "uid_clean": uid_clean, "name_clean": name_clean})

    mapping = {}

    # Mapeia usinas da Restrição para a Geração
    coff_names = coff_df["nome_usina"].dropna().unique() if "nome_usina" in coff_df.columns else []
    coff_ids = coff_df["usina_id"].dropna().unique() if "usina_id" in coff_df.columns else []
    all_coff_keys = set(coff_names).union(set(coff_ids))

    for key in all_coff_keys:
        k_clean = clean_str(key)
        if not k_clean:
            continue
        
        # 1. Match exato
        match = next((g["uid"] for g in ger_usinas if k_clean == g["uid_clean"] or k_clean == g["name_clean"]), None)
        
        # 2. Match por substring (sigla contida no nome ou nome contido na sigla)
        if not match:
            match = next((g["uid"] for g in ger_usinas if g["uid_clean"] and (g["uid_clean"] in k_clean or k_clean in g["uid_clean"])), None)
            
        # 3. Match por nome da usina
        if not match:
            match = next((g["uid"] for g in ger_usinas if g["name_clean"] and (g["name_clean"] in k_clean or k_clean in g["name_clean"])), None)

        if match:
            mapping[key] = match

    return mapping

def build_master_dataset(
    data_dir: str = "data",
    output_parquet: str = "data/master_hourly.parquet"
) -> pd.DataFrame:
    coff_path = os.path.join(data_dir, "ons_restricao_operacao.csv")
    ger_path = os.path.join(data_dir, "ons_geracao_verificada.csv")
    aneel_path = os.path.join(data_dir, "aneel_siga.csv")
    pld_path = os.path.join(data_dir, "ccee_pld_horario.csv")

    log.info("Lendo CSVs do diretório '%s'...", data_dir)
    coff_raw = _normalize_columns(pd.read_csv(coff_path))
    ger_raw = _normalize_columns(pd.read_csv(ger_path))
    aneel_raw = _normalize_columns(pd.read_csv(aneel_path)) if os.path.exists(aneel_path) else None
    pld_raw = _normalize_columns(pd.read_csv(pld_path)) if os.path.exists(pld_path) else None

    # Normalização de Datas
    ger_raw["timestamp"] = pd.to_datetime(ger_raw["timestamp"]).dt.tz_localize(None).dt.floor("h")
    coff_raw["timestamp"] = pd.to_datetime(coff_raw["timestamp"]).dt.tz_localize(None).dt.floor("h")

    # Normalização de Subsistema
    if "subsistema" in ger_raw.columns:
        ger_raw["subsistema"] = ger_raw["subsistema"].apply(normalize_subsistema)
    if "subsistema" in coff_raw.columns:
        coff_raw["subsistema"] = coff_raw["subsistema"].apply(normalize_subsistema)

    # Garantia de ID na Geração
    if "usina_id" not in ger_raw.columns and "nome_usina" in ger_raw.columns:
        ger_raw["usina_id"] = ger_raw["nome_usina"].apply(clean_str)

    # Construção do Mapa Inteligente de IDs
    log.info("Mapeando correspondência de siglas e nomes de usinas...")
    usina_map = _build_usina_mapping(ger_raw, coff_raw, aneel_raw)
    
    # Aplicação do Mapa no Restrição
    if "usina_id" in coff_raw.columns:
        coff_raw["usina_id"] = coff_raw["usina_id"].map(usina_map).fillna(coff_raw["usina_id"])
    elif "nome_usina" in coff_raw.columns:
        coff_raw["usina_id"] = coff_raw["nome_usina"].map(usina_map)

    shared_usinas = set(ger_raw["usina_id"].dropna()).intersection(set(coff_raw["usina_id"].dropna()))
    log.info("Match ONS Restrição x Geração: %d usinas unificadas com sucesso.", len(shared_usinas))

    # Agrupamento da Geração
    ger_group_cols = ["timestamp", "usina_id"]
    if "subsistema" in ger_raw.columns:
        ger_group_cols.append("subsistema")

    ger_agg = ger_raw.groupby(ger_group_cols, as_index=False).agg({
        "geracao_mwh": "sum",
        **({col: "first" for col in ["nome_usina", "ceg"] if col in ger_raw.columns})
    })

    # Agrupamento do Constrained-Off
    coff_agg = coff_raw.groupby(["timestamp", "usina_id"], as_index=False)["corte_mwh"].sum()

    # Merge Principal: Geração + Restrição
    master = ger_agg.merge(coff_agg, on=["timestamp", "usina_id"], how="left")
    master["corte_mwh"] = master["corte_mwh"].fillna(0.0)

    # Flags de Imputação
    master["geracao_mwh_imputado"] = master["geracao_mwh"].isna()
    master["corte_mwh_imputado"] = False
    master["geracao_mwh"] = master["geracao_mwh"].fillna(0.0)

    # Enriquecimento com Metadados da ANEEL (Latitude/Longitude)
    if aneel_raw is not None:
        log.info("Vinculando geolocalização ANEEL...")
        aneel_raw["nome_clean"] = aneel_raw["nome_usina"].apply(clean_str) if "nome_usina" in aneel_raw.columns else ""
        aneel_raw["ceg_clean"] = aneel_raw["ceg"].apply(clean_str) if "ceg" in aneel_raw.columns else ""
        
        geo_cols = [c for c in ["latitude", "longitude"] if c in aneel_raw.columns]
        if geo_cols:
            geo_dict = {}
            for _, row in aneel_raw.dropna(subset=geo_cols, how="all").iterrows():
                data = {c: row[c] for c in geo_cols}
                if row["ceg_clean"]:
                    geo_dict[row["ceg_clean"]] = data
                if row["nome_clean"]:
                    geo_dict[row["nome_clean"]] = data

            master_uids = master[["usina_id"]].drop_duplicates()
            geo_list = []
            for uid in master_uids["usina_id"]:
                u_clean = clean_str(uid)
                match_geo = next((v for k, v in geo_dict.items() if u_clean in k or k in u_clean), {})
                geo_list.append({"usina_id": uid, **match_geo})

            geo_df = pd.DataFrame(geo_list)
            master = master.merge(geo_df, on="usina_id", how="left")
            log.info("Coordenadas vinculadas para %d usinas.", master["latitude"].notna().nunique())

    # Merge do PLD
    if pld_raw is not None:
        log.info("Vinculando PLD por hora e subsistema...")
        pld_raw["timestamp"] = pd.to_datetime(pld_raw["timestamp"]).dt.tz_localize(None).dt.floor("h")
        if "subsistema" in pld_raw.columns:
            pld_raw["subsistema"] = pld_raw["subsistema"].apply(normalize_subsistema)

        pld_agg = pld_raw.groupby(["timestamp", "subsistema"], as_index=False)["pld"].mean()
        master = master.merge(pld_agg, on=["timestamp", "subsistema"], how="left")

    log.info("Master DataFrame concluído: %d linhas, %d usinas únicas.", len(master), master["usina_id"].nunique())
    
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)
    master.to_parquet(output_parquet, index=False)
    log.info("Snapshot parquet salvo em '%s'.", output_parquet)

    print("\n--- Amostra do Resultado ---")
    print(master.head())
    print("\n--- Tipos das Colunas ---")
    print(master.dtypes)
    return master

if __name__ == "__main__":
    build_master_dataset()