# ⚡ Marketplace & Energy Analytics — ONS / CCEE

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://energy-matchmaker-br.streamlit.app/)

Solução desenvolvida para o **Hackathon Energy Analytics**, focada em transformar restrições operacionais de geração (*constrained-off* / *curtailment*) em oportunidades de investimento energético de alto valor (ROI + ESG).

---

## 🎯 O Problema & A Solução

* **O Desafio:** Apenas em agosto de 2026, mais de R$ 1,8 milhão em energia renovável foi descartado por falta de infraestrutura de transmissão no Brasil (corte forçado).
* **Nossa Solução:** Uma pipeline de dados otimizada em Parquet que alimenta um **Marketplace Bilateral**. A plataforma conecta projetos de alta demanda (Data Centers de IA, plantas de H2V e indústrias) diretamente às usinas geradoras ociosas. 
* **O Resultado:** O *offtaker* garante energia mais barata, e a usina destrava uma nova linha de receita para uma energia que seria desperdiçada.

---

## 🚀 Funcionalidades da Plataforma

1. **Visão Geral de Geração:** Mapeamento temporal de produção consolidada por subsistema.
2. **Análise de Restrições & Losses:** Cruzamento financeiro entre MWh cortados e o PLD (Preço de Liquidação das Diferenças).
3. **Mapeamento Geográfico:** Geolocalização interativa das usinas impactadas.
4. **Matchmaker de Investimentos:** Algoritmo que estressa cenários de volatilidade, calcula economia mensal/anual (ROI), receita da usina, impacto de CO₂ e gera um **Term Sheet Comercial (CSV)** pronto para a diretoria.

---

## 🛠️ Engenharia de Dados & Tecnologias

Para garantir performance na nuvem, abandonamos arquivos CSVs tradicionais que pesavam quase 1 GB. 
A pipeline foi refatorada para processar milhões de registros do ONS e CCEE em milissegundos utilizando a arquitetura colunar **Parquet**.

* **Linguagem:** Python 3.10+
* **Processamento de Dados:** Pandas, PyArrow
* **Visualização & Dashboard:** Streamlit, Plotly Express
* **Dados Fonte:** ONS, CCEE, ANEEL SIGA

---

## ⚙️ Como Executar o Projeto Localmente

Se desejar rodar o projeto em sua própria máquina, abra o terminal e execute os comandos abaixo em sequência:

1. Clone o repositório e entre na pasta:
    git clone https://github.com/otavioaugusto-dev/energy-analytics-hackathon.git
    cd energy-analytics-hackathon

2. Instale as dependências:
    pip install -r requirements.txt

3. Execute a aplicação:
    streamlit run app.py
