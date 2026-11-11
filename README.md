# ReEnergia ⚡

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://energy-matchmaker-br.streamlit.app/)

Solução desenvolvida durante o **Hackathon ProEnergia**, focada em transformar restrições operacionais de geração (*constrained-off* / *curtailment*) em oportunidades de investimento energético de alto valor (ROI + ESG).

O projeto atua como um **marketplace de energia restrita**, conectando projetos de alta demanda (Data Centers de IA, plantas de Hidrogênio Verde e indústrias eletrointensivas) diretamente às usinas geradoras com excedente ocioso, garantindo tarifas competitivas e mitigando a pegada de carbono.

---

## 🎯 Problema e Solução

* **O Desafio:** Apenas em agosto de 2026, mais de R$ 1,8 milhão em energia renovável foi descartado por falta de infraestrutura de transmissão no Brasil (corte forçado). Milhões de MWh de energia renovável gerada são desperdiçados devido a restrições de transmissão na rede nacional, gerando prejuízos expressivos para o setor elétrico e investidores.
* **Nossa Solução:** Uma pipeline de dados otimizada em Parquet que alimenta um **Marketplace Bilateral**. A plataforma conecta projetos de alta demanda (Data Centers de IA, plantas de H₂V e indústrias) diretamente às usinas geradoras ociosas, identificando restrições e promovendo o *match* comercial entre a oferta ociosa e a demanda industrial.
* **O Resultado:** O *offtaker* garante energia mais barata, e a usina destrava uma nova linha de receita para uma energia que seria desperdiçada, otimizando o custo de suprimento e acelerando a descarbonização.

---

## 🚀 Funcionalidades da Plataforma

1. **Visão Geral de Geração:** Mapeamento temporal de produção consolidada por subsistema e tipo de fonte (ONS 2023).
2. **Análise de Restrições & Losses:** Cruzamento financeiro entre MWh cortados e o PLD (Preço de Liquidação das Diferenças), permitindo identificar os *hotspots* de desperdício energético (2026).
3. **Mapeamento Geográfico:** Geolocalização interativa das usinas impactadas, priorizando oportunidades de conexão próximas às cargas.
4. **Matchmaker de Investimentos:** Algoritmo que estressa cenários de volatilidade, calcula economia mensal/anual (ROI), receita da usina, impacto de CO₂ e gera um **Term Sheet Comercial (CSV)** pronto para a diretoria.

---

## 🛠️ Engenharia de Dados & Tecnologias

Para garantir performance na nuvem, abandonamos arquivos CSVs tradicionais que pesavam quase 1 GB. A pipeline foi refatorada para processar milhões de registros do ONS e CCEE em milissegundos utilizando a arquitetura colunar **Parquet**.

* **Linguagem:** Python 3.10+
* **Processamento de Dados:** Pandas, PyArrow (Formato Parquet para alta performance)
* **Visualização & Dashboard:** Streamlit, Plotly Express
* **Dados Fonte:** ONS, CCEE, ANEEL SIGA

---

## ⚙️ Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.10+ instalado.

### Configuração
Se desejar rodar o projeto em sua própria máquina, abra o terminal e execute os comandos abaixo em sequência:

```bash
# 1. Clone o repositório e entre na pasta
git clone https://github.com/otavioaugusto-dev/energy-analytics-hackathon.git
cd energy-analytics-hackathon

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Geração dos dados processados (se necessário)
# O projeto utiliza arquivos Parquet para alta performance. 
# Execute o pipeline de processamento para gerar/atualizar os dados:
python prepare_dashboard.py

# 4. Execute a aplicação
streamlit run app.py
```

---

## 🏗️ Estrutura do Projeto

```
.
├── app.py                    # Interface principal da aplicação (Streamlit)
├── data_loader.py            # Carregamento otimizado de dados com cache
├── calculations.py           # Lógica de negócio e cálculos do Matchmaker
├── ui_components.py          # Componentes visuais padronizados
├── prepare_dashboard.py      # Pipeline de transformação (CSV → Parquet)
├── data_pipeline.py          # Pipeline de leitura e limpeza de dados (ONS/CCEE)
├── requirements.txt          # Dependências do projeto
├── README.md                 # Esta documentação
└── data/                     # Diretório contendo datasets
    ├── dash_geracao_diaria.parquet      # Geração diária agregada (2023)
    ├── dash_restricao_diaria.parquet    # Restrição diária + PLD (2026)
    ├── ccee_pld_horario.csv             # PLD horário CCEE
    ├── ons_restricao_operacao.csv       # Restrição operacional ONS
    ├── aneel_siga.csv                   # Cadastro ANEEL SIGA
    └── raw/                             # Arquivos brutos do ONS (geração 2023)
```

---

## 💡 Autoria e Contribuições

Desenvolvido por **Otávio Augusto, Guilherme Florêncio e Arthur Silvino** durante o Hackathon ProEnergia.

