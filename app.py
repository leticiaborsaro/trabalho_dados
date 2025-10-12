
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import warnings
import streamlit as st

warnings.filterwarnings('ignore')

# Configuração da página do Streamlit
st.set_page_config(layout="wide", page_title="Análise ODS: Crescimento vs Desigualdade")

# ===============================================================
# TÍTULO E INTRODUÇÃO
# ===============================================================
st.title("📊 Análise ODS: Crescimento Econômico vs. Desigualdade no Brasil")
st.markdown("""
Esta aplicação analisa a relação entre o **Crescimento Econômico (ODS 8)** e a **Redução das Desigualdades (ODS 10)** no Brasil.
Os dados nacionais são obtidos do PNUD e Banco Mundial, enquanto os dados estaduais vêm de uma base de dados consolidada do IBGE hospedada no GitHub.
""")

# ===============================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS (COM CACHE)
# ===============================================================

# O @st.cache_data garante que os dados sejam carregados apenas uma vez.
@st.cache_data
def carregar_dados_nacionais():
    """Carrega e combina os dados nacionais."""
    try:
        # GNI do UNDP
        brasil_data_url = "https://github.com/leticiaborsaro/trabalho_dados/blob/main/Brazil.csv?raw=true"
        brasil_data = pd.read_csv(brasil_data_url)
        gni_pc_br = brasil_data[brasil_data['key'].str.contains("Gross National Income", na=False)].copy()
        gni_pc_br['Year'] = gni_pc_br['key'].str.extract(r'\((\d{4})\)').astype(int)
        gni_pc_br = gni_pc_br.rename(columns={'value': 'GNI_per_Capita'})
        gni_pc_br['GNI_per_Capita'] = pd.to_numeric(gni_pc_br['GNI_per_Capita'], errors='coerce')
        gni_pc_br = gni_pc_br[['Year', 'GNI_per_Capita']].dropna()

        # Gini e Desemprego do Banco Mundial
        gini_url = "https://api.worldbank.org/v2/country/BR/indicator/SI.POV.GINI?format=json&per_page=100"
        desemprego_url = "https://api.worldbank.org/v2/country/BR/indicator/SL.UEM.TOTL.ZS?format=json&per_page=100"
        
        gini_data = requests.get(gini_url, timeout=30).json()[1]
        desemprego_data = requests.get(desemprego_url, timeout=30).json()[1]
        
        gini_df = pd.DataFrame([{'Year': int(item['date']), 'Gini': float(item['value'])} for item in gini_data if item['value'] is not None])
        desemprego_df = pd.DataFrame([{'Year': int(item['date']), 'Desemprego': float(item['value'])} for item in desemprego_data if item['value'] is not None])

        # Merge
        dados_nacionais = pd.merge(gni_pc_br, gini_df, on='Year', how='left')
        
        ### ESTA É A LINHA QUE FOI CORRIGIDA ###
        dados_nacionais = pd.merge(dados_nacionais, desemprego_df, on='Year', how='left')
        
        return dados_nacionais.sort_values('Year').reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados nacionais: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_dados_estaduais():
    """Carrega os dados estaduais do seu link no GitHub."""
    try:
        url_dados_estaduais = "https://github.com/leticiaborsaro/trabalho_dados/blob/main/dados_estaduais_ibge.csv?raw=true"
        df_estados = pd.read_csv(url_dados_estaduais)
        return df_estados
    except Exception as e:
        st.error(f"Erro ao carregar dados estaduais do GitHub: {e}")
        return pd.DataFrame()

# --- Execução do Carregamento ---
dados_nacionais = carregar_dados_nacionais()
df_estados = carregar_dados_estaduais()


# ===============================================================
# ANÁLISE NACIONAL
# ===============================================================
st.header("1. Análise Nacional: A Visão Geral do Brasil")

if not dados_nacionais.empty:
    dados_corr = dados_nacionais[['GNI_per_Capita', 'Gini']].dropna()
    correlacao = dados_corr['GNI_per_Capita'].corr(dados_corr['Gini'])
    
    col1, col2 = st.columns([1, 2]) # Dando mais espaço para o gráfico
    with col1:
        st.metric(label="Correlação (GNI per Capita vs. Gini)", value=f"{correlacao:.3f}")
        if correlacao < -0.3:
            st.success("Tendência de Crescimento Inclusivo: Historicamente, o aumento da renda esteve associado a uma redução da desigualdade.")
        else:
            st.warning("Relação Fraca ou Neutra: Crescimento econômico por si só não foi um fator determinante para a trajetória da desigualdade.")

    with col2:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=dados_nacionais['Year'], y=dados_nacionais['GNI_per_Capita'], name='GNI per Capita', line=dict(color='#1f77b4', width=3)))
        fig4.add_trace(go.Scatter(x=dados_nacionais['Year'], y=dados_nacionais['Gini'], name='Índice de Gini', yaxis='y2', line=dict(color='#d62728', width=3)))
        fig4.update_layout(
            title='<b>Evolução do Crescimento e Desigualdade no Brasil</b>',
            yaxis=dict(title='GNI per Capita (US$ PPP)'),
            yaxis2=dict(title='Índice de Gini', overlaying='y', side='right', showgrid=False),
            legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top"),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig4, use_container_width=True)

# ===============================================================
# ANÁLISE ESTADUAL
# ===============================================================
st.header("2. Análise Estadual: As Diferentes Realidades do Brasil")

if not df_estados.empty:
    # --- Barra lateral com filtros ---
    st.sidebar.header("Filtros Interativos")
    anos_disponiveis = sorted(df_estados['Ano'].unique())
    ano_selecionado = st.sidebar.slider(
        "Selecione o ano para o Ranking Estadual:",
        min_value=min(anos_disponiveis),
        max_value=max(anos_disponiveis),
        value=max(anos_disponiveis)
    )
    df_filtrado = df_estados[df_estados['Ano'] == ano_selecionado]

    # --- Análise Estadual ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Ranking de PIB per Capita ({ano_selecionado})")
        df_ranking_pib = df_filtrado.sort_values('PIB_per_Capita', ascending=True)
        fig2 = px.bar(df_ranking_pib, y='Estado', x='PIB_per_Capita', color='Regiao',
                      title=f'<b>PIB per Capita por Estado ({ano_selecionado})</b>',
                      labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Estado': ''},
                      height=600, template='plotly_white')
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.subheader(f"Relação PIB vs. Desigualdade ({ano_selecionado})")
        fig3 = px.scatter(df_filtrado, x='PIB_per_Capita', y='Gini',
                          color='Regiao', size='PIB_per_Capita',
                          title=f'<b>PIB per Capita vs. Gini por Estado ({ano_selecionado})</b>',
                          labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Gini': 'Índice de Gini'},
                          hover_data=['Estado'],
                          height=600, template='plotly_white')
        st.plotly_chart(fig3, use_container_width=True)

else:
    st.warning("Não foi possível carregar os dados estaduais para a análise.")
