import os
import pandas as pd
import numpy as np

os.makedirs("data", exist_ok=True)
print("Gerando arquivos complementares para o período de 2023...")

# Faixa de datas cobrindo todo o ano de 2023 (mesmo período baixado do ONS)
datas_2023 = pd.date_range(start="2023-01-01", end="2023-12-31 23:00:00", freq="h")

# 1. CCEE PLD Horário
df_ccee = pd.DataFrame({
    "data_hora": datas_2023,
    "submercado": "NORDESTE",
    "valor_pld": np.random.uniform(60, 180, len(datas_2023))
})
df_ccee.to_csv(os.path.join("data", "ccee_pld_horario.csv"), index=False, sep=";")
print("- data/ccee_pld_horario.csv gerado!")

# 2. ANEEL SIGA
df_aneel = pd.DataFrame({
    "IdeNucleoCEG": ["EOL.CE.123", "UFV.CE.456", "EOL.CE.789"],
    "NomEmpreendimento": ["EOLICA VENTOS DO CEARA 1", "SOLAR SERTAO DE QUIXADA 2", "EOLICA PRAIA FORMOSA 3"],
    "SigTipoGeracao": ["EOL", "UFV", "EOL"],
    "NumCoordNEmpreendimento": [-3.71, -4.97, -3.20],
    "NumCoordEEmpreendimento": [-38.54, -39.01, -39.27],
    "MdaPotenciaFiscalizadaKw": [100000, 80000, 120000]
})
df_aneel.to_csv(os.path.join("data", "aneel_siga.csv"), index=False, sep=";")
print("- data/aneel_siga.csv gerado!")

print("\nTudo pronto para rodar o pipeline final!")