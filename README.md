# ☀️ Simulador Técnico-Econômico de Sistemas Fotovoltaicos

Aplicação web interativa desenvolvida em **Python** para dimensionamento preliminar, análise de balanço energético e estudo de viabilidade financeira de sistemas solares fotovoltaicos conectados à rede (On-Grid).

## 🎯 Funcionalidades Principais

* **Sazonalidade Solarimétrica (12 meses):** Cruzamento entre a curva de geração mensal (base CRESESB/CEPEL) e o perfil de consumo do cliente.
* **Modelagem Térmica:** Estimativa da temperatura de operação da célula fotovoltaica (NOCT = 45 °C) e cálculo da perda térmica real (coeficiente = -0,35 %/°C).
* **Engenharia Estrutural e Ambiental:** Cálculo da área mínima de cobertura (m²), sobrecarga distribuída no telhado (kg/m²) e emissões de CO2 evitadas em 25 anos.
* **Regulação (Lei 14.300):** Simulação da cobrança escalonada do Fio B sobre a energia injetada na rede, descontando o autoconsumo instantâneo (fator de simultaneidade) e o custo de disponibilidade.
* **Análise de Investimentos:** Fluxo de caixa de 25 anos com cálculo de **VPL (Valor Presente Líquido)**, **TIR (Taxa Interna de Retorno)**, **Payback Descontado**, economia de escala no CAPEX e exportação em CSV.

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Streamlit** (Interface web interativa)
* **Pandas & NumPy** (Modelagem matemática, fluxo de caixa e cálculo de TIR)
* **Plotly** (Gráficos interativos)

## 🚀 Como Executar Localmente

1. Clone este repositório ou baixe os arquivos.
2. Instale as dependências necessárias:
   `pip install streamlit pandas numpy plotly`
3. Execute a aplicação:
   `streamlit run app.py`
