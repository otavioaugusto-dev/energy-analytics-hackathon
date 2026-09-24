import pandas as pd

files = {
    "Restrição (ONS)": "data/ons_restricao_operacao.csv",
    "Geração (ONS)": "data/ons_geracao_verificada.csv",
    "ANEEL (SIGA)": "data/aneel_siga.csv",
    "PLD (CCEE)": "data/ccee_pld_horario.csv"
}

for name, path in files.items():
    print(f"\n=== {name} ({path}) ===")
    try:
        df = pd.read_csv(path, nrows=2)
        print("Colunas:", list(df.columns))
        print(df.head(1))
    except Exception as e:
        print(f"Erro ao ler {path}: {e}")