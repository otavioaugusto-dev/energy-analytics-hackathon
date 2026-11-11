# ReEnergia ⚡

Solução desenvolvida durante o **Hackathon ProEnergia**, focada em transformar restrições operacionais de geração (*constrained-off* / *curtailment*) em oportunidades de investimento energético de alto valor (ROI + ESG).

O projeto atua como um **marketplace de energia restrita**, conectando projetos de alta demanda (Data Centers de IA, plantas de Hidrogênio Verde e indústrias eletrointensivas) diretamente às usinas geradoras com excedente ocioso, garantindo tarifas competitivas e mitigando a pegada de carbono.

---

## 🎯 Problema e Solução

* **O Desafio:** Milhões de MWh de energia renovável gerada no Brasil são desperdiçados devido a restrições de transmissão na rede nacional, gerando prejuízos expressivos para o setor elétrico e investidores.
* **Nossa Solução:** Uma plataforma de inteligência de dados que identifica essas restrições e promove o *match* comercial entre a oferta ociosa e a demanda industrial, otimizando o custo de suprimento e acelerando a descarbonização.

---

## 🚀 Funcionalidades Principais

1. **Visão Geral de Geração:** Monitoramento consolidado da produção de energia renovável (ONS 2023) por subsistema e tipo de fonte.
2. **Análise de Restrições & Curtailment:** Cruzamento financeiro entre o volume restrito e o PLD, permitindo identificar os "hotspots" de desperdício energético (2026).
3. **Mapeamento Geográfico:** Geolocalização interativa dos ativos impactados, priorizando oportunidades de conexão próximas às cargas.
4. **Matchmaker de Investimentos:** Algoritmo de inteligência comercial que calcula a economia mensal/anual (ROI), realiza análise de sensibilidade financeira e gera um **Term Sheet Comercial (CSV)** para exportação.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Data Processing:** Pandas, PyArrow (Formato Parquet para alta performance)
* **Visualização:** Streamlit, Plotly Express
* **Fontes de Dados:** ONS, CCEE, ANEEL SIGA

---

## ⚙️ Instalação e Execução

### Pré-requisitos
- Python 3.10+ instalado.

### Configuração
1. **Clone o repositório:**
   ```bash
   git clone https://github.com/otavioaugusto-dev/energy-analytics-hackathon.git
   cd energy-analytics-hackathon
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Geração dos dados processados:**
   O projeto utiliza arquivos Parquet para alta performance. Se necessário, execute o pipeline de processamento:
   ```bash
   python prepare_dashboard.py
   ```

4. **Execute a aplicação:**
   ```bash
   streamlit run app.py
   ```

---

## 🏗️ Estrutura do Projeto

- `app.py`: Interface principal da aplicação (Streamlit).
- `data_loader.py`: Carregamento otimizado de dados.
- `calculations.py`: Lógica de negócio e cálculos do Matchmaker.
- `ui_components.py`: Componentes visuais padronizados.
- `prepare_dashboard.py`: Pipeline de transformação (CSV -> Parquet).
- `data/`: Diretório contendo datasets (processados e raw).

---

## 💡 Autoria e Contribuições

Desenvolvido por **Otávio Augusto** durante o Hackathon ProEnergia.

🤖 Gerado com [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
