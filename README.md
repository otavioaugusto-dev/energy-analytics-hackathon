# ⚡ Marketplace & Energy Analytics — ONS / CCEE / ANEEL

Solução desenvolvida para o **Hackathon Energy Analytics**, focada em transformar restrições operacionais de geração (*constrained-off* / *curtailment*) em oportunidades de investimento energético de alto valor (ROI + ESG).

---

## 🎯 O Problema & A Solução

* **O Desafio:** Milhões de MWh de energia renovável gerada são cortados por restrições de transmissão na rede nacional (gerando prejuízos expressivos no setor elétrico).
* **Nossa Solução:** Uma pipeline de dados otimizada em Parquet que alimenta um **Marketplace Matchmaker**. A plataforma conecta projetos de alta demanda (Data Centers de IA, plantas de Hidrogênio Verde e indústrias) diretamente às usinas geradoras com excedente ocioso, garantindo tarifas com desconto vs Baseline e mitigando pegada de $CO_2$.

---

## 🚀 Funcionalidades do Dashboard

1. **Visão Geral de Geração (2023):** Mapeamento temporal de produção consolidada por subsistema e usinas no Brasil.
2. **Análise de Restrições & Losses (2026):** Cruzamento financeiro entre MWh cortados e o PLD (Preço de Liquidação das Diferenças).
3. **Mapeamento Geográfico:** Geolocalização interativa das usinas impactadas via MapLibre/Plotly.
4. **Matchmaker de Investimentos:** Algoritmo que calcula a economia mensal/anual (ROI), faz análise de sensibilidade e gera um **Term Sheet Comercial (CSV)** pronto para download.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Processamento de Dados:** Pandas, PyArrow (Formato Parquet)
* **Visualização & Dashboard:** Streamlit, Plotly Express
* **Dados Fonte:** ONS, CCEE, ANEEL SIGA

---

## ⚙️ Como Executar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/otavioaugusto-dev/energy-analytics-hackathon.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
   cd NOME_DO_REPOSITORIO
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   streamlit run app.py
   ```