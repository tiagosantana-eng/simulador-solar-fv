
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Engenharia Solar FV | Simulador Técnico-Econômico",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Simulador Técnico-Econômico de Sistemas Fotovoltaicos")
st.markdown(
    "Modelagem de geração mensal (CRESESB), perdas térmicas (NOCT), sobrecarga estrutural, "
    "regulação **Lei 14.300 (Fio B + Tributos)** e análise de investimentos (**VPL, TIR e Payback Fracionado**)."
)

# --- 1. BASE DE DADOS CLIMÁTICOS (12 MESES - CRESESB / INMET) ---
meses = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
dias_mes = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

base_climatica = {
    "São João del-Rei - MG": {
        "hsp": (5.65, 5.75, 5.25, 4.95, 4.55, 4.40, 4.65, 5.30, 5.45, 5.55, 5.40, 5.50),
        "temp_amb": 20.5,
        "tarifa_padrao": 0.94
    },
    "Belo Horizonte - MG": {
        "hsp": (5.80, 5.95, 5.45, 5.15, 4.75, 4.60, 4.85, 5.50, 5.65, 5.75, 5.55, 5.65),
        "temp_amb": 22.0,
        "tarifa_padrao": 0.94
    },
    "São Paulo - SP": {
        "hsp": (5.15, 5.30, 4.85, 4.35, 3.85, 3.65, 3.85, 4.45, 4.55, 4.90, 5.15, 5.25),
        "temp_amb": 20.0,
        "tarifa_padrao": 0.85
    },
    "Rio de Janeiro - RJ": {
        "hsp": (5.85, 6.00, 5.35, 4.75, 4.15, 3.95, 4.10, 4.75, 4.85, 5.25, 5.55, 5.80),
        "temp_amb": 24.5,
        "tarifa_padrao": 1.05
    },
    "Brasília - DF": {
        "hsp": (5.45, 5.60, 5.35, 5.45, 5.30, 5.25, 5.45, 6.05, 6.10, 5.75, 5.25, 5.25),
        "temp_amb": 21.5,
        "tarifa_padrao": 0.82
    }
}

# --- 2. BARRA LATERAL (PARÂMETROS DE ENTRADA) ---
st.sidebar.header("1. Localidade e Consumo")
cidade = st.sidebar.selectbox("Município de Instalação:", list(base_climatica.keys()))
consumo_mensal = st.sidebar.number_input("Consumo Médio Mensal (kWh):", min_value=100, max_value=100000, value=2550, step=50)
tipo_ligacao = st.sidebar.selectbox(
    "Padrão de Entrada (Custo Disponibilidade):",
    ("Monofásico (30 kWh)", "Bifásico (50 kWh)", "Trifásico (100 kWh)"),
    index=2
)
tarifa = st.sidebar.number_input(
    "Tarifa com Impostos (R$/kWh):",
    min_value=0.30,
    max_value=2.50,
    value=base_climatica.get(cidade).get("tarifa_padrao"),
    step=0.02
)

st.sidebar.header("2. Premissas Técnicas (Módulos)")
opcoes_modulos = (550, 585, 610)
potencia_modulo_w = st.sidebar.selectbox("Potência do Módulo FV (W):", opcoes_modulos, index=0)
simultaneidade = st.sidebar.slider(
    "Fator de Simultaneidade (Autoconsumo %):",
    min_value=10,
    max_value=90,
    value=35,
    help="Percentual da energia gerada consumida instantaneamente sem passar pela rede da distribuidora."
) / 100.0

st.sidebar.header("3. Premissas Financeiras (VPL / TIR)")
tma = st.sidebar.slider("Taxa Mínima de Atratividade - TMA (% a.a.):", min_value=4.0, max_value=18.0, value=10.5, step=0.5) / 100.0
reajuste_anual = st.sidebar.slider("Inflação Energética Estimada (% a.a.):", min_value=2.0, max_value=12.0, value=5.0, step=0.5) / 100.0

# --- 3. CÁLCULOS FÍSICOS E DE ENGENHARIA ---
dados_cidade = base_climatica.get(cidade)
hsp_mensal = dados_cidade.get("hsp")
hsp_medio = float(np.mean(hsp_mensal))
temp_amb = dados_cidade.get("temp_amb")

# Modelagem Térmica (NOCT = 45°C a 1000 W/m² pico -> elevação de +31.25°C sobre T_amb; Coef. Térmico = -0.35%/°C)
temp_celula = temp_amb + 31.25
perda_termica = max(0.0, (temp_celula - 25.0) * 0.0035)
outras_perdas = 0.12  # Cabeamento CC/CA, sujeira, mismatch e eficiência do inversor (12%)
performance_ratio = (1.0 - perda_termica) * (1.0 - outras_perdas)

# Custo de disponibilidade (kWh/mês)
disp_map = {"Monofásico (30 kWh)": 30, "Bifásico (50 kWh)": 50, "Trifásico (100 kWh)": 100}
custo_disp_kwh = disp_map.get(tipo_ligacao)
energia_compensavel_alvo = max(50.0, consumo_mensal - custo_disp_kwh)
consumo_anual_compensavel = energia_compensavel_alvo * 12.0

# Dimensionamento da Potência (kWp)
potencia_necessaria_kwp = (energia_compensavel_alvo / 30.0) / (hsp_medio * performance_ratio)
qtd_modulos = int(np.ceil((potencia_necessaria_kwp * 1000.0) / potencia_modulo_w))
potencia_real_kwp = (qtd_modulos * potencia_modulo_w) / 1000.0

# Engenharia Mecânica / Estrutural e Ambiental
area_modulo_m2 = 2.58 if potencia_modulo_w == 550 else 2.75
peso_modulo_kg = 28.5 if potencia_modulo_w == 550 else 31.0
area_total_m2 = qtd_modulos * area_modulo_m2
carga_estrutural_kg_m2 = (qtd_modulos * (peso_modulo_kg + 4.5)) / area_total_m2

# Geração Mês a Mês (kWh)
geracao_mensal = [potencia_real_kwp * hsp * performance_ratio * dias for hsp, dias in zip(hsp_mensal, dias_mes)]
geracao_anual_ano1 = sum(geracao_mensal)
co2_evitado_25anos_ton = (geracao_anual_ano1 * 25 * 0.94 * 0.085) / 1000.0

# --- 4. ENGENHARIA ECONÔMICA (CONSERVADORA: LEI 14.300 + ICMS TUSD + O&M/SEGURO + INVERSOR) ---
if potencia_real_kwp <= 5:
    custo_kwp = 3950.0
elif potencia_real_kwp <= 15:
    custo_kwp = 3450.0
elif potencia_real_kwp <= 30:
    custo_kwp = 3100.0
else:
    custo_kwp = 2850.0

investimento_inicial = potencia_real_kwp * custo_kwp

# 34% não compensável na energia injetada (~28% Fio B + ~6% ICMS/tributos sobre TUSD)
parcela_nao_compensavel = 0.34
percentual_injetado = 1.0 - simultaneidade
cronograma_fio_b = (0.60, 0.75, 0.90) + (1.00,) * 22

anos = list(range(0, 26))
fluxo_caixa = [-investimento_inicial]
fluxo_acumulado = [-investimento_inicial]
fluxo_descontado_acumulado = [-investimento_inicial]

payback_simples_frac = None
payback_descontado_frac = None

for ano in range(1, 26):
    degradacao = (1.0 - 0.005) ** (ano - 1)
    geracao_ano = geracao_anual_ano1 * degradacao
    
    # Energia aproveitada limitada a 97% do consumo compensável (desconto de descasamento sazonal verão/inverno)
    energia_aproveitada = min(geracao_ano, consumo_anual_compensavel * 0.97)
    tarifa_ano = tarifa * ((1.0 + reajuste_anual) ** (ano - 1))
    
    fator_cobranca = cronograma_fio_b[ano - 1]
    custo_rede_anual = (energia_aproveitada * percentual_injetado) * (tarifa_ano * parcela_nao_compensavel * fator_cobranca)
    
    # O&M + Seguro anual (1.3% do CAPEX corrigido pela inflação) + Troca do inversor no Ano 13 (25% CAPEX)
    custo_om_seguro = (investimento_inicial * 0.013) * ((1.0 + reajuste_anual) ** (ano - 1))
    troca_inversor = (investimento_inicial * 0.25) if ano == 13 else 0.0
    
    economia_liquida = (energia_aproveitada * tarifa_ano) - custo_rede_anual - custo_om_seguro - troca_inversor
    
    fluxo_caixa.append(economia_liquida)
    saldo_anterior = fluxo_acumulado[-1]
    saldo_acum = saldo_anterior + economia_liquida
    fluxo_acumulado.append(saldo_acum)
    
    vp_fluxo = economia_liquida / ((1.0 + tma) ** ano)
    saldo_desc_anterior = fluxo_descontado_acumulado[-1]
    saldo_desc_acum = saldo_desc_anterior + vp_fluxo
    fluxo_descontado_acumulado.append(saldo_desc_acum)
    
    # Interpolação linear para Payback fracionado preciso (ex: 5.0 anos)
    if saldo_acum >= 0 and payback_simples_frac is None:
        payback_simples_frac = (ano - 1) + (abs(saldo_anterior) / economia_liquida)
    if saldo_desc_acum >= 0 and payback_descontado_frac is None:
        payback_descontado_frac = (ano - 1) + (abs(saldo_desc_anterior) / vp_fluxo)

vpl = fluxo_descontado_acumulado[-1]

# Cálculo robusto da TIR (Método da Bisseção sobre o VPL - à prova de múltiplos fluxos negativos)
def calcular_tir(fluxos):
    baixo, alto = -0.99, 5.0
    for _ in range(100):
        meio = (baixo + alto) / 2.0
        vpl_teste = sum(fc / ((1.0 + meio) ** t) for t, fc in enumerate(fluxos))
        if vpl_teste > 0:
            baixo = meio
        else:
            alto = meio
    return ((baixo + alto) / 2.0) * 100.0

tir = calcular_tir(fluxo_caixa)

# --- 5. INTERFACE EM ABAS ---
tab1, tab2, tab3 = st.tabs((
    "📊 Dimensionamento & Balanço Energético",
    "💰 Viabilidade Econômica (VPL / TIR)",
    "📐 Memorial de Cálculo & Premissas"
))

with tab1:
    st.subheader(f"Resultados Técnicos — {cidade}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Potência Instalada", f"{potencia_real_kwp:.2f} kWp", f"{qtd_modulos} módulos de {potencia_modulo_w}W")
    c2.metric("Performance Ratio (PR)", f"{performance_ratio*100:.1f}%", f"Perda térmica: -{perda_termica*100:.1f}%")
    c3.metric("Área e Carga Estrutural", f"{area_total_m2:.1f} m²", f"{carga_estrutural_kg_m2:.1f} kg/m² no telhado")
    c4.metric("CO₂ Evitado (25 anos)", f"{co2_evitado_25anos_ton:.1f} ton", f"Geração Ano 1: {geracao_anual_ano1:,.0f} kWh")

    st.divider()

    df_mensal = pd.DataFrame({
        "Mês": meses,
        "Geração FV (kWh)": geracao_mensal,
        "Consumo Alvo (kWh)": [consumo_mensal] * 12
    })

    fig_mensal = go.Figure()
    fig_mensal.add_trace(go.Bar(
        x=df_mensal["Mês"],
        y=df_mensal["Geração FV (kWh)"],
        name="Geração Fotovoltaica (kWh)",
        marker_color="#00CC96"
    ))
    fig_mensal.add_trace(go.Scatter(
        x=df_mensal["Mês"],
        y=df_mensal["Consumo Alvo (kWh)"],
        name="Consumo Mensal (kWh)",
        mode="lines+markers",
        line=dict(color="#EF553B", width=3, dash="dash")
    ))
    fig_mensal.update_layout(
        title="Balanço Energético Mensal: Geração Solar vs. Consumo (Sazonalidade CRESESB)",
        xaxis_title="Mês do Ano",
        yaxis_title="Energia (kWh)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_mensal, use_container_width=True)

with tab2:
    st.subheader("Análise de Investimento (Modelo Conservador: Lei 14.300, O&M/Seguro e Inversor)")
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("CAPEX Estimado", f"R$ {investimento_inicial:,.2f}", f"R$ {custo_kwp:,.2f} / kWp")
    f2.metric(
        "Payback Descontado",
        f"{payback_descontado_frac:.1f} anos" if payback_descontado_frac else "> 25 anos",
        f"Simples: {payback_simples_frac:.1f} anos" if payback_simples_frac else "> 25 anos"
    )
f3.metric("VPL (Valor Presente Líquido)", f"R$ {vpl:,.2f}", f"TMA: {tma*100:.1f}% a.a.")
f4.metric("TIR (Taxa Interna de Retorno)", f"{tir:.1f}% a.a.", "Retorno sobre capital")
st.divider()
df_financeiro = pd.DataFrame({
"Ano": anos,
"Fluxo Líquido Anual (R$)": fluxo_caixa,
"Saldo Acumulado Simples (R$)": fluxo_acumulado,
"Saldo Acumulado Descontado (R$)": fluxo_descontado_acumulado
})
cores_barras = ["#EF553B" if val < 0 else "#00CC96" for val in df_financeiro["Saldo Acumulado Descontado (R$)"]]
fig_fin = go.Figure()
fig_fin.add_trace(go.Bar(
x=df_financeiro["Ano"],
y=df_financeiro["Saldo Acumulado Descontado (R$)"],
name="Saldo Acumulado Descontado (VPL)",
marker_color=cores_barras
))
fig_fin.add_trace(go.Scatter(
x=df_financeiro["Ano"],
y=df_financeiro["Saldo Acumulado Simples (R$)"],
name="Saldo Acumulado Simples",
mode="lines",
line=dict(color="#636EFA", width=2)
))
fig_fin.update_layout(
title="Evolução do Fluxo de Caixa Acumulado (25 Anos - inclui troca de inversor no Ano 13)",
xaxis_title="Ano de Operação",
yaxis_title="Valor Acumulado (R$)",
hovermode="x unified"
)
st.plotly_chart(fig_fin, use_container_width=True)
nome_cidade_limpo = cidade.split(" - ").pop(0).lower().replace(" ", "")
nome_arquivo = f"viabilidade_solar{nome_cidade_limpo}.csv"
csv = df_financeiro.to_csv(index=False).encode("utf-8")
st.download_button(
label="📥 Baixar Tabela de Fluxo de Caixa (CSV)",
data=csv,
file_name=nome_arquivo,
mime="text/csv"
)
with tab3:
    # Conteúdo da Aba 3
    st.subheader("Equações e Premissas de Engenharia")
    st.markdown(f"""
    * **Escopo de Aplicação:** Modelagem calibrada para unidades consumidoras do **Grupo B (Baixa Tensão)** em horizonte de 25 anos com aquisição via capital próprio (à vista).
    * **Base Solarimétrica:** Médias mensais de irradiação no plano horizontal obtidas via **CRESESB/CEPEL** para **{cidade}** (HSP médio anual: `{hsp_medio:.2f} kWh/m²·dia`).
    * **Modelagem Térmica (Pico STC):** Temperatura estimada da célula fotovoltaica de **`{temp_celula:.1f} °C`** (baseada em T_amb = `{temp_amb} °C`, NOCT = `45 °C` a 1000 W/m²), gerando perda térmica de **`{perda_termica*100:.2f}%`** (coeficiente térmico = `-0,35 %/°C`).
    * **Engenharia Estrutural:** Considera módulos comerciais de `{area_modulo_m2} m²` e `{peso_modulo_kg} kg` somados a `4,5 kg` de perfis de alumínio e grampos por módulo, resultando em uma carga distribuída de **`{carga_estrutural_kg_m2:.1f} kg/m²`**.
    * **Regulação (Lei 14.300 + Tributos):** A parcela compensada via rede (`{(1-simultaneidade)*100:.0f}%` da geração, limitada a 97% do consumo compensável) sofre cobrança escalonada de **34%** sobre a tarifa cheia (~28% Fio B + ~6% ICMS/tributos sobre TUSD), enquanto o autoconsumo instantâneo (`{simultaneidade*100:.0f}%`) é isento.
    * **Operação, Manutenção, Seguro e Reposição:** Desconto anual de `1,3%` sobre o CAPEX (corrigido pela inflação) para limpeza, seguro e inspeção, degradação linear de `0,5% a.a.` nos módulos e provisão de `25%` do CAPEX no **Ano 13** para substituição do inversor.
    """)
