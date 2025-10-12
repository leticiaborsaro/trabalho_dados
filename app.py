import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Configuração da página do Streamlit - DEVE SER O PRIMEIRO COMANDO
st.set_page_config(layout="wide", page_title="Análise ODS Brasil")

# ===============================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS (COM CACHE PARA VELOCIDADE)
# ===============================================================

@st.cache_data
def carregar_dados_nacionais():
    """Carrega e combina os dados nacionais."""
    try:
        brasil_data_url = "https://github.com/leticiaborsaro/trabalho_dados/blob/main/Brazil.csv?raw=true"
        brasil_data = pd.read_csv(brasil_data_url)
        gni_pc_br = brasil_data[brasil_data['key'].str.contains("Gross National Income", na=False)].copy()
        gni_pc_br['Year'] = gni_pc_br['key'].str.extract(r'\((\d{4})\)').astype(int)
        gni_pc_br = gni_pc_br.rename(columns={'value': 'GNI_per_Capita'})
        gni_pc_br['GNI_per_Capita'] = pd.to_numeric(gni_pc_br['GNI_per_Capita'], errors='coerce')
        gni_pc_br = gni_pc_br[['Year', 'GNI_per_Capita']].dropna()

        gini_url = "https://api.worldbank.org/v2/country/BR/indicator/SI.POV.GINI?format=json&per_page=100"
        gini_data = requests.get(gini_url, timeout=30).json()[1]
        gini_df = pd.DataFrame([{'Year': int(item['date']), 'Gini': float(item['value'])} for item in gini_data if item['value'] is not None])
        
        dados_nacionais = pd.merge(gni_pc_br, gini_df, on='Year', how='left')
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
# TÍTULO PRINCIPAL E INTRODUÇÃO
# ===============================================================
st.title("📊 Análise ODS: Crescimento Econômico vs. Desigualdade no Brasil")
st.markdown("""
Esta aplicação interativa analisa a relação entre o **Crescimento Econômico (ODS 8)** e a **Redução das Desigualdades (ODS 10)** no Brasil. 
Explore os dados nacionais e as realidades distintas dos estados brasileiros utilizando os filtros na barra lateral.
""")

# ===============================================================
# BARRA LATERAL COM FILTROS INTERATIVOS
# ===============================================================
st.sidebar.header("⚙️ Filtros Interativos")

if not df_estados.empty:
    anos_disponiveis = sorted(df_estados['Ano'].unique())
    ano_selecionado = st.sidebar.slider(
        "Selecione o ano para a análise estadual:",
        min_value=min(anos_disponiveis),
        max_value=max(anos_disponiveis),
        value=max(anos_disponiveis)
    )

    regioes_disponiveis = sorted(df_estados['Regiao'].unique())
    regioes_selecionadas = st.sidebar.multiselect(
        "Selecione as regiões para visualizar:",
        options=regioes_disponiveis,
        default=regioes_disponiveis
    )

    # Filtrar os dados com base nos filtros da barra lateral
    if regioes_selecionadas:
        df_filtrado = df_estados[(df_estados['Ano'] == ano_selecionado) & (df_estados['Regiao'].isin(regioes_selecionadas))]
    else: # Caso o usuário desmarque todas as regiões
        df_filtrado = pd.DataFrame()

    # --- KPIs DINÂMICOS NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Resumo para {ano_selecionado}")
    if not df_filtrado.empty:
        estado_mais_rico = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmax()]
        estado_mais_pobre = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmin()]
        disparidade = estado_mais_rico['PIB_per_Capita'] / estado_mais_pobre['PIB_per_Capita']
        
        st.sidebar.metric(label="Estado com Maior PIB per Capita", value=estado_mais_rico['Estado'])
        st.sidebar.metric(label="Estado com Menor PIB per Capita", value=estado_mais_pobre['Estado'])
        st.sidebar.metric(label="Disparidade Econômica", value=f"{disparidade:.1f}x")
    else:
        st.sidebar.warning("Selecione ao menos uma região.")

# ===============================================================
# LAYOUT COM ABAS
# ===============================================================
tab1, tab2 = st.tabs(["🌎 Análise Nacional", "🗺️ Análise Estadual Detalhada"])

# --- CONTEÚDO DA ABA 1: ANÁLISE NACIONAL ---
with tab1:
    st.header("A Visão Geral do Brasil (1990-2023)")
    
    if not dados_nacionais.empty:
        dados_corr = dados_nacionais[['GNI_per_Capita', 'Gini']].dropna()
        correlacao = dados_corr['GNI_per_Capita'].corr(dados_corr['Gini'])
        
        st.info(f"**Correlação Nacional (GNI per Capita vs. Gini): {correlacao:.3f}**")
        if correlacao < -0.3:
            st.markdown("📈 **Interpretação:** Historicamente, o Brasil apresentou um padrão de **crescimento inclusivo**, onde o aumento da renda esteve associado a uma moderada redução da desigualdade.")
        else:
            st.markdown("↔️ **Interpretação:** A relação entre crescimento e desigualdade é fraca, sugerindo que outros fatores, como políticas públicas, são mais determinantes para a distribuição de renda.")

        # Gráfico de evolução nacional
        fig_nacional = go.Figure()
        fig_nacional.add_trace(go.Scatter(x=dados_nacionais['Year'], y=dados_nacionais['GNI_per_Capita'], name='GNI per Capita', line=dict(color='royalblue', width=3)))
        fig_nacional.add_trace(go.Scatter(x=dados_nacionais['Year'], y=dados_nacionais['Gini'], name='Índice de Gini', yaxis='y2', line=dict(color='firebrick', width=3)))
        fig_nacional.update_layout(
            title='<b>Evolução do Crescimento Econômico e Desigualdade no Brasil</b>',
            yaxis=dict(title='GNI per Capita (US$ PPP)'),
            yaxis2=dict(title='Índice de Gini', overlaying='y', side='right', showgrid=False),
            legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", bgcolor='rgba(255,255,255,0.6)'),
            template='plotly_white',
            hovermode='x unified'
        )
        st.plotly_chart(fig_nacional, use_container_width=True)

# --- CONTEÚDO DA ABA 2: ANÁLISE ESTADUAL ---
with tab2:
    st.header(f"As Diferentes Realidades do Brasil em {ano_selecionado}")

    if not df_filtrado.empty:
        # Paleta de cores para as regiões
        cores_regioes = {
            'Norte': '#2ca02c',       # Verde
            'Nordeste': '#ff7f0e',    # Laranja
            'Sudeste': '#d62728',     # Vermelho
            'Sul': '#1f77b4',         # Azul
            'Centro-Oeste': '#9467bd' # Roxo
        }

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking de Riqueza (PIB per Capita)")
            df_ranking_pib = df_filtrado.sort_values('PIB_per_Capita', ascending=True)
            fig_pib = px.bar(
                df_ranking_pib, y='Estado', x='PIB_per_Capita', color='Regiao',
                title=f'<b>PIB per Capita por Estado ({ano_selecionado})</b>',
                labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Estado': ''},
                height=600, template='plotly_white', color_discrete_map=cores_regioes,
                hover_data={'Gini': ':.3f'} # Adiciona Gini no hover
            )
            st.plotly_chart(fig_pib, use_container_width=True)
        
        with col2:
            st.subheader("Ranking de Desigualdade (Gini)")
            df_ranking_gini = df_filtrado.sort_values('Gini', ascending=False)
            fig_gini = px.bar(
                df_ranking_gini, y='Estado', x='Gini', color='Regiao',
                title=f'<b>Índice de Gini por Estado ({ano_selecionado})</b>',
                labels={'Gini': 'Índice de Gini', 'Estado': ''},
                height=600, template='plotly_white', color_discrete_map=cores_regioes,
                hover_data={'PIB_per_Capita': ':,.0f'} # Adiciona PIB no hover
            )
            st.plotly_chart(fig_gini, use_container_width=True)
            
        st.markdown("---") # Linha divisória para dar espaço
        
        st.subheader(f"Análise de Correlação: Riqueza vs. Desigualdade ({ano_selecionado})")
        fig_scatter = px.scatter(
            df_filtrado, x='PIB_per_Capita', y='Gini',
            color='Regiao', size='PIB_per_Capita',
            title=f'<b>PIB per Capita vs. Gini por Estado ({ano_selecionado})</b>',
            labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Gini': 'Índice de Gini'},
            hover_name='Estado', # Mostra o nome do estado no hover
            template='plotly_white',
            color_discrete_map=cores_regioes
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        st.warning("Nenhum dado para exibir. Por favor, selecione ao menos uma região na barra lateral.")
