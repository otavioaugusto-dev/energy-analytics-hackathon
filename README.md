<<<<<<< HEAD
# ReEnergia ⚡
=======
# ⚡ Marketplace & Energy Analytics — ONS / CCEE

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://energy-matchmaker-br.streamlit.app/)
>>>>>>> a1e2801bb81e0723d5b935fd396bd36e37039005

Solução desenvolvida durante o **Hackathon ProEnergia**, focada em transformar restrições operacionais de geração (*constrained-off* / *curtailment*) em oportunidades de investimento energético de alto valor (ROI + ESG).

O projeto atua como um **marketplace de energia restrita**, conectando projetos de alta demanda (Data Centers de IA, plantas de Hidrogênio Verde e indústrias eletrointensivas) diretamente às usinas geradoras com excedente ocioso, garantindo tarifas competitivas e mitigando a pegada de carbono.

---

## 🎯 Problema e Solução

<<<<<<< HEAD
* **O Desafio:** Milhões de MWh de energia renovável gerada no Brasil são desperdiçados devido a restrições de transmissão na rede nacional, gerando prejuízos expressivos para o setor elétrico e investidores.
* **Nossa Solução:** Uma plataforma de inteligência de dados que identifica essas restrições e promove o *match* comercial entre a oferta ociosa e a demanda industrial, otimizando o custo de suprimento e acelerando a descarbonização.

---

## 🚀 Funcionalidades Principais

1. **Visão Geral de Geração:** Monitoramento consolidado da produção de energia renovável (ONS 2023) por subsistema e tipo de fonte.
2. **Análise de Restrições & Curtailment:** Cruzamento financeiro entre o volume restrito e o PLD, permitindo identificar os "hotspots" de desperdício energético (2026).
3. **Mapeamento Geográfico:** Geolocalização interativa dos ativos impactados, priorizando oportunidades de conexão próximas às cargas.
4. **Matchmaker de Investimentos:** Algoritmo de inteligência comercial que calcula a economia mensal/anual (ROI), realiza análise de sensibilidade financeira e gera um **Term Sheet Comercial (CSV)** para exportação.
=======
* **O Desafio:** Apenas em agosto de 2026, mais de R$ 1,8 milhão em energia renovável foi descartado por falta de infraestrutura de transmissão no Brasil (corte forçado).
* **Nossa Solução:** Uma pipeline de dados otimizada em Parquet que alimenta um **Marketplace Bilateral**. A plataforma conecta projetos de alta demanda (Data Centers de IA, plantas de H2V e indústrias) diretamente às usinas geradoras ociosas. 
* **O Resultado:** O *offtaker* garante energia mais barata, e a usina destrava uma nova linha de receita para uma energia que seria desperdiçada.

---

## 🚀 Funcionalidades da Plataforma

1. **Visão Geral de Geração:** Mapeamento temporal de produção consolidada por subsistema.
2. **Análise de Restrições & Losses:** Cruzamento financeiro entre MWh cortados e o PLD (Preço de Liquidação das Diferenças).
3. **Mapeamento Geográfico:** Geolocalização interativa das usinas impactadas.
4. **Matchmaker de Investimentos:** Algoritmo que estressa cenários de volatilidade, calcula economia mensal/anual (ROI), receita da usina, impacto de CO₂ e gera um **Term Sheet Comercial (CSV)** pronto para a diretoria.
>>>>>>> a1e2801bb81e0723d5b935fd396bd36e37039005

---

## 🛠️ Engenharia de Dados & Tecnologias

Para garantir performance na nuvem, abandonamos arquivos CSVs tradicionais que pesavam quase 1 GB. 
A pipeline foi refatorada para processar milhões de registros do ONS e CCEE em milissegundos utilizando a arquitetura colunar **Parquet**.

* **Linguagem:** Python 3.10+
<<<<<<< HEAD
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
=======
* **Processamento de Dados:** Pandas, PyArrow
* **Visualização & Dashboard:** Streamlit, Plotly Express
* **Dados Fonte:** ONS, CCEE, ANEEL SIGA

---

## ⚙️ Como Executar o Projeto Localmente

Se desejar rodar o projeto em sua própria máquina, abra o terminal e execute os comandos abaixo em sequência:
>>>>>>> a1e2801bb81e0723d5b935fd396bd36e37039005

1. Clone o repositório e entre na pasta:
    git clone https://github.com/otavioaugusto-dev/energy-analytics-hackathon.git
    cd energy-analytics-hackathon

<<<<<<< HEAD
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
=======
2. Instale as dependências:
    pip install -r requirements.txt

3. Execute a aplicação:
    streamlit run app.py
>>>>>>> a1e2801bb81e0723d5b935fd396bd36e37039005
