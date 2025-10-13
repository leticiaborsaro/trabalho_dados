import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ===============================================================
# CONFIGURAÇÃO DA PÁGINA 
# ===============================================================
st.set_page_config(
    layout="wide", 
    page_title="Análise ODS Brasil - Crescimento vs Desigualdade",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS personalizado para tema roxo
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #6A0DAD;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #8A2BE2;
        border-bottom: 2px solid #9370DB;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #6A0DAD, #9370DB);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
    }
    .explanation-box {
        background-color: #F8F7FF;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #6A0DAD;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===============================================================
# PALETA DE CORES ROXA 
# ===============================================================
CORES_ROXO = {
    'roxo_escuro': '#6A0DAD',
    'roxo_medio': '#8A2BE2', 
    'roxo_claro': '#9370DB',
    'lavanda': '#E6E6FA',
    'roxo_suave': '#F8F7FF'
}

CORES_REGIOES = {
    'Norte': '#4B0082',
    'Nordeste': '#8A2BE2',
    'Sudeste': '#9370DB',
    'Sul': '#BA55D3',
    'Centro-Oeste': '#DA70D6'
}

# ===============================================================
# FUNÇÕES DE CARREGAMENTO
# ===============================================================

@st.cache_data
def carregar_dados_nacionais():
    try:
        brasil_data_url = "https://github.com/leticiaborsaro/trabalho_dados/blob/main/Brazil.csv?raw=true"
        brasil_data = pd.read_csv(brasil_data_url)
        gni_pc_br = brasil_data[brasil_data['key'].str.contains("Gross National Income", na=False)].copy()
        gni_pc_br['Year'] = gni_pc_br['key'].str.extract(r'\((\d{4})\)').astype(int)
        gni_pc_br = gni_pc_br.rename(columns={'value': 'GNI_per_Capita'})
        gni_pc_br['GNI_per_Capita'] = pd.to_numeric(gni_pc_br['GNI_per_Capita'], errors='coerce')
        gni_pc_br = gni_pc_br[['Year', 'GNI_per_Capita']].dropna()

        # Dados Gini do Banco Mundial
        gini_url = "https://api.worldbank.org/v2/country/BR/indicator/SI.POV.GINI?format=json&per_page=100"
        response = requests.get(gini_url, timeout=30)
        gini_data = response.json()
        
        gini_records = []
        if len(gini_data) > 1:
            for item in gini_data[1]:
                if item.get('value') is not None:
                    gini_records.append({
                        'Year': int(item['date']),
                        'Gini': float(item['value'])
                    })
        
        gini_df = pd.DataFrame(gini_records)
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
        st.error(f"Erro ao carregar dados estaduais: {e}")
        return pd.DataFrame()

# ===============================================================
# CARREGAMENTO DOS DADOS
# ===============================================================
dados_nacionais = carregar_dados_nacionais()
df_estados = carregar_dados_estaduais()

# ===============================================================
# CABEÇALHO PRINCIPAL
# ===============================================================
st.markdown('<h1 class="main-header">ANÁLISE ODS BRASIL</h1>', unsafe_allow_html=True)
st.markdown('<h2 style="text-align: center; color: #8A2BE2;">Crescimento Econômico vs Desigualdade de Renda</h2>', unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <p style='font-size: 1.2rem; color: #666;'>
    Explore a relação entre <strong>ODS 8 (Crescimento Econômico)</strong> e 
    <strong>ODS 10 (Redução das Desigualdades)</strong> no contexto brasileiro
    </p>
</div>
""", unsafe_allow_html=True)

# ===============================================================
# BARRA LATERAL 
# ===============================================================
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #6A0DAD, #9370DB); padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
        <h2> CONTROLES</h2>
        <p>Personalize sua análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not df_estados.empty:
        anos_disponiveis = sorted(df_estados['Ano'].unique())
        ano_selecionado = st.selectbox(
            "** Selecione o ano:**",
            options=anos_disponiveis,
            index=len(anos_disponiveis)-1,
            help="Analise a evolução ano a ano"
        )

        regioes_disponiveis = sorted(df_estados['Regiao'].unique())
        regioes_selecionadas = st.multiselect(
            "**Filtre por regiões:**",
            options=regioes_disponiveis,
            default=regioes_disponiveis,
            help="Compare regiões específicas"
        )

        # KPIs DINÂMICOS NA BARRA LATERAL
        st.markdown("---")
        st.markdown("###RESUMO DO ANO")
        
        if regioes_selecionadas:
            df_filtrado = df_estados[(df_estados['Ano'] == ano_selecionado) & (df_estados['Regiao'].isin(regioes_selecionadas))]
            
            if not df_filtrado.empty:
                estado_mais_rico = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmax()]
                estado_mais_pobre = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmin()]
                estado_mais_igual = df_filtrado.loc[df_filtrado['Gini'].idxmin()]
                
                st.metric(" - Maior PIB", estado_mais_rico['Estado'], f"R$ {estado_mais_rico['PIB_per_Capita']:,.0f}")
                st.metric(" - Mais Igual", estado_mais_igual['Estado'], f"Gini: {estado_mais_igual['Gini']:.3f}")
                
                disparidade = estado_mais_rico['PIB_per_Capita'] / estado_mais_pobre['PIB_per_Capita']
                st.metric("Disparidade", f"{disparidade:.1f}x")

# ===============================================================
# LAYOUT PRINCIPAL COM ABAS
# ===============================================================
tab1, tab2, tab3 = st.tabs(["VISÃO NACIONAL", "ANÁLISE ESTADUAL", "CONCLUSÕES"])

# ===============================================================
# ABA 1: VISÃO NACIONAL
# ===============================================================
with tab1:
    st.markdown('<h2 class="sub-header">TRAJETÓRIA NACIONAL BRASILEIRA</h2>', unsafe_allow_html=True)
    
    if not dados_nacionais.empty:
        # CÁLCULO DA CORRELAÇÃO
        dados_corr = dados_nacionais[['GNI_per_Capita', 'Gini']].dropna()
        correlacao = dados_corr['GNI_per_Capita'].corr(dados_corr['Gini'])
        
        # CARDS DE MÉTRICAS NACIONAIS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            crescimento = ((dados_nacionais['GNI_per_Capita'].iloc[-1] - dados_nacionais['GNI_per_Capita'].iloc[0]) / dados_nacionais['GNI_per_Capita'].iloc[0]) * 100
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 Crescimento</h3>
                <p style="font-size: 2rem; margin: 0;">+{crescimento:.1f}%</p>
                <p>1990-2023</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Correlação</h3>
                <p style="font-size: 2rem; margin: 0;">{correlacao:.3f}</p>
                <p>Crescimento vs Desigualdade</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            gini_atual = dados_nacionais['Gini'].iloc[-1]
            st.markdown(f"""
            <div class="metric-card">
                <h3>Desigualdade</h3>
                <p style="font-size: 2rem; margin: 0;">{gini_atual:.3f}</p>
                <p>Índice de Gini 2023</p>
            </div>
            """, unsafe_allow_html=True)
        
        # GRÁFICO NACIONAL
        fig_nacional = go.Figure()
        
        # GNI
        fig_nacional.add_trace(go.Scatter(
            x=dados_nacionais['Year'], 
            y=dados_nacionais['GNI_per_Capita'],
            name='GNI per Capita',
            line=dict(color=CORES_ROXO['roxo_medio'], width=4),
            fill='tozeroy',
            fillcolor='rgba(138, 43, 226, 0.1)'
        ))
        
        # Gini (se disponível)
        if 'Gini' in dados_nacionais.columns:
            fig_nacional.add_trace(go.Scatter(
                x=dados_nacionais['Year'], 
                y=dados_nacionais['Gini'],
                name='Índice de Gini',
                line=dict(color='#FF6B6B', width=4, dash='dot'),
                yaxis='y2'
            ))
        
        # Layout
        fig_nacional.update_layout(
            title='EVOLUÇÃO DO CRESCIMENTO E DESIGUALDADE NO BRASIL (1990-2023)',
            xaxis_title='Ano',
            yaxis_title='GNI per Capita (US$ PPP)',
            yaxis2=dict(
                title='Índice de Gini',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            template='plotly_white',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_nacional, use_container_width=True)
        
        # EXPLICAÇÃO DO GRÁFICO NACIONAL - USANDO MARKDOWN PURO
        st.markdown("---")
        st.markdown("### O QUE ESTE GRÁFICO NOS REVELA?")
        
        st.markdown(f"""
        **Padrão de Crescimento Inclusivo:** A correlação negativa de **{correlacao:.3f}** indica que, historicamente, 
        quando a economia brasileira cresce, a desigualdade tende a diminuir.
        
        **Períodos de Transformação:** Observe como a desigualdade caiu significativamente entre 2001-2014, 
        período marcado por políticas sociais e crescimento econômico.
        
        **Conclusão:** O Brasil demonstra que é possível conciliar crescimento com redução de desigualdades, 
        mas isso requer políticas consistentes e um ambiente econômico favorável.
        """)

# ===============================================================
# ABA 2: ANÁLISE ESTADUAL
# ===============================================================
with tab2:
    st.markdown('<h2 class="sub-header">REALIDADES ESTADUAIS COMPARADAS</h2>', unsafe_allow_html=True)
    
    if not df_estados.empty and 'regioes_selecionadas' in locals() and regioes_selecionadas:
        df_filtrado = df_estados[(df_estados['Ano'] == ano_selecionado) & (df_estados['Regiao'].isin(regioes_selecionadas))]
        
        if not df_filtrado.empty:
            # LAYOUT EM COLUNAS
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### RANKING DE RIQUEZA ESTADUAL")
                
                df_ranking_pib = df_filtrado.sort_values('PIB_per_Capita', ascending=True)
                fig_pib = px.bar(
                    df_ranking_pib, 
                    y='Estado', 
                    x='PIB_per_Capita',
                    color='Regiao',
                    color_discrete_map=CORES_REGIOES,
                    title=f'PIB PER CAPITA POR ESTADO ({ano_selecionado})',
                    labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Estado': ''},
                    height=500
                )
                st.plotly_chart(fig_pib, use_container_width=True)
                
                # EXPLICAÇÃO PIB - MARKDOWN PURO
                st.markdown("---")
                st.markdown("#### INTERPRETANDO A RIQUEZA ESTADUAL")
                st.markdown("""
                **Distrito Federal como Outlier:** A capital federal lidera com folga devido à concentração 
                de serviços públicos e alta renda dos funcionários públicos.
                
                **Padrão Regional:** Observe como estados do **Centro-Oeste e Sul** tendem a ter 
                PIBs mais altos, enquanto **Nordeste** concentra os menores valores.
                
                **Desafio do Desenvolvimento:** A diferença de 10.6x entre o mais rico e o mais pobre 
                revela a necessidade de políticas regionais específicas.
                """)
            
            with col2:
                st.markdown("####RANKING DE DESIGUALDADE")
                
                df_ranking_gini = df_filtrado.sort_values('Gini', ascending=False)
                fig_gini = px.bar(
                    df_ranking_gini, 
                    y='Estado', 
                    x='Gini',
                    color='Regiao',
                    color_discrete_map=CORES_REGIOES,
                    title=f'ÍNDICE DE GINI POR ESTADO ({ano_selecionado})',
                    labels={'Gini': 'Índice de Gini', 'Estado': ''},
                    height=500
                )
                st.plotly_chart(fig_gini, use_container_width=True)
                
                # EXPLICAÇÃO GINI - MARKDOWN PURO
                st.markdown("---")
                st.markdown("#### ENTENDENDO A DESIGUALDADE ESTADUAL")
                st.markdown("""
                **Santa Catarina como Modelo:** Com Gini de 0.418, é referência nacional em igualdade, 
                combinando desenvolvimento econômico com distribuição de renda.
                
                **Surpresa do Norte:** Estados como Rondônia mostram que é possível ter relativa igualdade 
                mesmo em regiões menos desenvolvidas economicamente.
                
                **Desafio Nordestino:** A região precisa enfrentar desigualdades históricas através de 
                políticas educacionais e de geração de emprego.
                """)
            
            # GRÁFICO DE DISPERSÃO
            st.markdown("---")
            st.markdown("####RELAÇÃO ENTRE RIQUEZA E DESIGUALDADE")
            
            fig_scatter = px.scatter(
                df_filtrado, 
                x='PIB_per_Capita', 
                y='Gini',
                color='Regiao',
                size='PIB_per_Capita',
                color_discrete_map=CORES_REGIOES,
                title=f'PIB vs DESIGUALDADE: ANÁLISE DE RELAÇÃO ({ano_selecionado})',
                labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Gini': 'Índice de Gini'},
                hover_name='Estado',
                size_max=40
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # EXPLICAÇÃO SCATTER - MARKDOWN PURO
            st.markdown("---")
            st.markdown("#### MAPA DE RELAÇÕES: ONDE CADA ESTADO SE ENCAIXA?")
            st.markdown("""
            **Quadrante Ideal (Inferior Direito):** Estados com **alto PIB e baixa desigualdade**. 
            Exemplo: Santa Catarina - o modelo a ser seguido.
            
            **Quadrante de Desafio (Superior Esquerdo):** Estados com **baixo PIB e alta desigualdade**. 
            Exemplo: Maranhão - necessidade de políticas urgentes.
            
            **Quadrante de Oportunidade (Inferior Esquerdo):** Estados com **baixo PIB mas relativa igualdade**. 
            Podem crescer mantendo a distribuição.
            
            **Quadrante de Concentração (Superior Direito):** Estados **ricos mas desiguais**. 
            Precisam melhorar a distribuição dos ganhos.
            
            **Conclusão:** O objetivo é mover todos os estados para o quadrante inferior direito - 
            **ricos e igualitários**.
            """)

# ===============================================================
# ABA 3: CONCLUSÕES
# ===============================================================
with tab3:
    st.markdown('<h2 class="sub-header">CONCLUSÕES E RECOMENDAÇÕES</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### DESCOBERTAS PRINCIPAIS")
        st.markdown("""
        **Crescimento Inclusivo**
        O Brasil apresenta correlação negativa entre crescimento e desigualdade (-0.428), 
        indicando que o desenvolvimento econômico tem beneficiado os mais pobres.
        
        **Desafios Regionais**
        Disparidade de 10.6x entre estados mais rico e mais pobre revela necessidade de 
        políticas regionais específicas.
        
        **Modelos de Sucesso**
        Santa Catarina combina alto desenvolvimento com baixa desigualdade (Gini 0.418), 
        servindo de referência nacional.
        
        **Nordeste Prioritário**
        Região concentra os maiores desafios, exigindo atenção especial em políticas 
        redistributivas.
        """)
    
    with col2:
        st.markdown("###RECOMENDAÇÕES ESTRATÉGICAS")
        st.markdown("""
        **Políticas Regionais**
        Desenvolver estratégias específicas para cada contexto estadual e regional, 
        reconhecendo as diferentes realidades.
        
        **Educação e Capacitação**
        Investir massivamente em educação nas regiões menos desenvolvidas para 
        quebrar ciclos de desigualdade.
        
        **Infraestrutura Regional**
        Direcionar investimentos em infraestrutura para estados com menor desenvolvimento 
        econômico.
        
        **Monitoramento Contínuo**
        Manter sistema de acompanhamento dos indicadores de desigualdade para 
        ajustar políticas quando necessário.
        """)
    
    # MENSAGEM FINAL
    st.markdown("---")
    st.markdown("### CONCLUSÃO FINAL")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #6A0DAD, #9370DB); padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
    O Brasil demonstra que **crescimento econômico e redução de desigualdades podem caminhar juntos**. 
    No entanto, os desafios regionais históricos exigem **políticas persistentes e bem direcionadas** 
    para alcançarmos um desenvolvimento verdadeiramente sustentável e inclusivo.
    </div>
    """, unsafe_allow_html=True)

# ===============================================================
# RODAPÉ
# ===============================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p><strong>Análise ODS Brasil</strong> | Dados: UNDP, Banco Mundial, IBGE | Desenvolvido para análise acadêmica</p>
    <p>ODS 8 - Crescimento Econômico | ODS 10 - Redução das Desigualdades</p>
</div>
""", unsafe_allow_html=True)
