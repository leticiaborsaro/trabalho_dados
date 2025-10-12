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
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #E6E6FA;
        border-radius: 10px 10px 0px 0px;
        gap: 1rem;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ===============================================================
# PALETA DE CORES ROXA PROFISSIONAL
# ===============================================================
CORES_ROXO = {
    'roxo_escuro': '#6A0DAD',
    'roxo_medio': '#8A2BE2', 
    'roxo_claro': '#9370DB',
    'lavanda': '#E6E6FA',
    'roxo_suave': '#F8F7FF'
}

CORES_REGIOES = {
    'Norte': '#4B0082',      # Roxo escuro
    'Nordeste': '#8A2BE2',   # Roxo azulado
    'Sudeste': '#9370DB',    # Roxo médio
    'Sul': '#BA55D3',        # Roxo claro
    'Centro-Oeste': '#DA70D6' # Orquídea
}

# ===============================================================
# FUNÇÕES DE CARREGAMENTO (MANTIDAS)
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

# ===============================================================
# CARREGAMENTO DOS DADOS
# ===============================================================
dados_nacionais = carregar_dados_nacionais()
df_estados = carregar_dados_estaduais()

# ===============================================================
# CABEÇALHO PRINCIPAL
# ===============================================================
st.markdown('<h1 class="main-header">📊 ANÁLISE ODS BRASIL</h1>', unsafe_allow_html=True)
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
# BARRA LATERAL COM DESIGN ROXO
# ===============================================================
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #6A0DAD, #9370DB); padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
        <h2>⚙️ CONTROLES</h2>
        <p>Personalize sua análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not df_estados.empty:
        anos_disponiveis = sorted(df_estados['Ano'].unique())
        ano_selecionado = st.slider(
            "**📅 Selecione o ano:**",
            min_value=min(anos_disponiveis),
            max_value=max(anos_disponiveis),
            value=max(anos_disponiveis),
            help="Analise a evolução ano a ano"
        )

        regioes_disponiveis = sorted(df_estados['Regiao'].unique())
        regioes_selecionadas = st.multiselect(
            "**🗺️ Filtre por regiões:**",
            options=regioes_disponiveis,
            default=regioes_disponiveis,
            help="Compare regiões específicas"
        )

        # KPIs DINÂMICOS NA BARRA LATERAL
        st.markdown("---")
        st.markdown("### 📈 RESUMO DO ANO")
        
        if regioes_selecionadas:
            df_filtrado = df_estados[(df_estados['Ano'] == ano_selecionado) & (df_estados['Regiao'].isin(regioes_selecionadas))]
            
            if not df_filtrado.empty:
                estado_mais_rico = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmax()]
                estado_mais_pobre = df_filtrado.loc[df_filtrado['PIB_per_Capita'].idxmin()]
                estado_mais_igual = df_filtrado.loc[df_filtrado['Gini'].idxmin()]
                
                st.metric("🏆 Maior PIB per Capita", f"{estado_mais_rico['Estado']}", f"R$ {estado_mais_rico['PIB_per_Capita']:,.0f}")
                st.metric("📊 Menor Desigualdade", f"{estado_mais_igual['Estado']}", f"Gini: {estado_mais_igual['Gini']:.3f}")
                
                disparidade = estado_mais_rico['PIB_per_Capita'] / estado_mais_pobre['PIB_per_Capita']
                st.metric("⚖️ Disparidade Regional", f"{disparidade:.1f}x", "Rico vs Pobre")

# ===============================================================
# LAYOUT PRINCIPAL COM ABAS
# ===============================================================
tab1, tab2, tab3 = st.tabs(["🌎 VISÃO NACIONAL", "🗺️ ANÁLISE ESTADUAL", "📚 CONCLUSÕES"])

# ===============================================================
# ABA 1: VISÃO NACIONAL
# ===============================================================
with tab1:
    st.markdown('<h2 class="sub-header">📈 TRAJETÓRIA NACIONAL BRASILEIRA</h2>', unsafe_allow_html=True)
    
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
                <h3>🔄 Correlação</h3>
                <p style="font-size: 2rem; margin: 0;">{correlacao:.3f}</p>
                <p>Crescimento vs Desigualdade</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            gini_atual = dados_nacionais['Gini'].iloc[-1]
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚖️ Desigualdade</h3>
                <p style="font-size: 2rem; margin: 0;">{gini_atual:.3f}</p>
                <p>Índice de Gini 2023</p>
            </div>
            """, unsafe_allow_html=True)
        
        # GRÁFICO NACIONAL MELHORADO
        fig_nacional = go.Figure()
        
        # Área do GNI
        fig_nacional.add_trace(go.Scatter(
            x=dados_nacionais['Year'], 
            y=dados_nacionais['GNI_per_Capita'],
            name='GNI per Capita',
            line=dict(color=CORES_ROXO['roxo_medio'], width=4),
            fill='tozeroy',
            fillcolor='rgba(138, 43, 226, 0.1)',
            hovertemplate='<b>Ano: %{x}</b><br>GNI: US$ %{y:,.0f}<extra></extra>'
        ))
        
        # Linha do Gini
        fig_nacional.add_trace(go.Scatter(
            x=dados_nacionais['Year'], 
            y=dados_nacionais['Gini'],
            name='Índice de Gini',
            line=dict(color='#FF6B6B', width=4, dash='dot'),
            yaxis='y2',
            hovertemplate='<b>Ano: %{x}</b><br>Gini: %{y:.3f}<extra></extra>'
        ))
        
        fig_nacional.update_layout(
            title='<b>EVOLUÇÃO DO CRESCIMENTO E DESIGUALDADE NO BRASIL (1990-2023)</b>',
            xaxis_title='Ano',
            yaxis=dict(
                title='GNI per Capita (US$ PPP)',
                titlefont=dict(color=CORES_ROXO['roxo_medio']),
                tickfont=dict(color=CORES_ROXO['roxo_medio'])
            ),
            yaxis2=dict(
                title='Índice de Gini',
                titlefont=dict(color='#FF6B6B'),
                tickfont=dict(color='#FF6B6B'),
                overlaying='y',
                side='right',
                showgrid=False
            ),
            template='plotly_white',
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='rgba(248,247,255,0.5)'
        )
        
        st.plotly_chart(fig_nacional, use_container_width=True)
        
        # EXPLICAÇÃO DO GRÁFICO NACIONAL
        st.markdown("""
        <div class="explanation-box">
            <h4>🎯 O QUE ESTE GRÁFICO NOS REVELA?</h4>
            <p><strong>Padrão de Crescimento Inclusivo:</strong> A correlação negativa de -0.428 indica que, historicamente, 
            quando a economia brasileira cresce, a desigualdade tende a diminuir. Isso é um sinal positivo para o desenvolvimento sustentável.</p>
            
            <p><strong>Períodos de Transformação:</strong> Observe como a desigualdade caiu significativamente entre 2001-2014, 
            período marcado por políticas sociais e crescimento econômico. Já a partir de 2015, enfrentamos desafios com a crise econômica.</p>
            
            <p><strong>Conclusão:</strong> O Brasil demonstra que é possível conciliar crescimento com redução de desigualdades, 
            mas isso requer políticas consistentes e um ambiente econômico favorável.</p>
        </div>
        """, unsafe_allow_html=True)

# ===============================================================
# ABA 2: ANÁLISE ESTADUAL
# ===============================================================
with tab2:
    st.markdown('<h2 class="sub-header">🔍 REALIDADES ESTADUAIS COMPARADAS</h2>', unsafe_allow_html=True)
    
    if not df_estados.empty and 'regioes_selecionadas' in locals() and regioes_selecionadas:
        df_filtrado = df_estados[(df_estados['Ano'] == ano_selecionado) & (df_estados['Regiao'].isin(regioes_selecionadas))]
        
        if not df_filtrado.empty:
            # LAYOUT EM COLUNAS PARA OS GRÁFICOS
            col1, col2 = st.columns(2)
            
            with col1:
                # GRÁFICO DE BARRAS HORIZONTAIS - PIB
                st.markdown("#### 💰 RANKING DE RIQUEZA ESTADUAL")
                
                df_ranking_pib = df_filtrado.sort_values('PIB_per_Capita', ascending=True)
                fig_pib = px.bar(
                    df_ranking_pib, 
                    y='Estado', 
                    x='PIB_per_Capita',
                    color='Regiao',
                    color_discrete_map=CORES_REGIOES,
                    title=f'<b>PIB PER CAPITA POR ESTADO ({ano_selecionado})</b>',
                    labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Estado': ''},
                    height=500,
                    template='plotly_white',
                    hover_data={'Gini': ':.3f', 'Regiao': True}
                )
                
                fig_pib.update_layout(
                    showlegend=True,
                    plot_bgcolor='rgba(248,247,255,0.5)',
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                st.plotly_chart(fig_pib, use_container_width=True)
                
                # EXPLICAÇÃO PIB
                st.markdown("""
                <div class="explanation-box">
                    <h4>📊 INTERPRETANDO A RIQUEZA ESTADUAL</h4>
                    <p><strong>Distrito Federal como Outlier:</strong> A capital federal lidera com folga devido à concentração 
                    de serviços públicos e alta renda dos funcionários públicos.</p>
                    
                    <p><strong>Padrão Regional:</strong> Observe como estados do <strong>Centro-Oeste e Sul</strong> tendem a ter 
                    PIBs mais altos, enquanto <strong>Nordeste</strong> concentra os menores valores.</p>
                    
                    <p><strong>Desafio do Desenvolvimento:</strong> A diferença de 10.6x entre o mais rico e o mais pobre 
                    revela a necessidade de políticas regionais específicas.</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # GRÁFICO DE BARRAS HORIZONTAIS - GINI
                st.markdown("#### ⚖️ RANKING DE DESIGUALDADE")
                
                df_ranking_gini = df_filtrado.sort_values('Gini', ascending=False)
                fig_gini = px.bar(
                    df_ranking_gini, 
                    y='Estado', 
                    x='Gini',
                    color='Regiao',
                    color_discrete_map=CORES_REGIOES,
                    title=f'<b>ÍNDICE DE GINI POR ESTADO ({ano_selecionado})</b>',
                    labels={'Gini': 'Índice de Gini', 'Estado': ''},
                    height=500,
                    template='plotly_white',
                    hover_data={'PIB_per_Capita': ':,.0f', 'Regiao': True}
                )
                
                fig_gini.update_layout(
                    showlegend=True,
                    plot_bgcolor='rgba(248,247,255,0.5)',
                    yaxis={'categoryorder': 'total descending'}
                )
                
                st.plotly_chart(fig_gini, use_container_width=True)
                
                # EXPLICAÇÃO GINI
                st.markdown("""
                <div class="explanation-box">
                    <h4>🎯 ENTENDENDO A DESIGUALDADE ESTADUAL</h4>
                    <p><strong>Santa Catarina como Modelo:</strong> Com Gini de 0.418, é referência nacional em igualdade, 
                    combinando desenvolvimento econômico com distribuição de renda.</p>
                    
                    <p><strong>Surpresa do Norte:</strong> Estados como Rondônia mostram que é possível ter relativa igualdade 
                    mesmo em regiões menos desenvolvidas economicamente.</p>
                    
                    <p><strong>Desafio Nordestino:</strong> A região precisa enfrentar desigualdades históricas através de 
                    políticas educacionais e de geração de emprego.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # GRÁFICO DE DISPERSÃO INTERATIVO
            st.markdown("---")
            st.markdown("#### 🔗 RELAÇÃO ENTRE RIQUEZA E DESIGUALDADE")
            
            fig_scatter = px.scatter(
                df_filtrado, 
                x='PIB_per_Capita', 
                y='Gini',
                color='Regiao',
                size='PIB_per_Capita',
                color_discrete_map=CORES_REGIOES,
                title=f'<b>PIB vs DESIGUALDADE: ANÁLISE DE RELAÇÃO ({ano_selecionado})</b>',
                labels={'PIB_per_Capita': 'PIB per Capita (R$)', 'Gini': 'Índice de Gini'},
                hover_name='Estado',
                template='plotly_white',
                size_max=40
            )
            
            # Adicionar linha de tendência
            fig_scatter.update_traces(
                marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey'))
            )
            
            # Adicionar quadrantes explicativos
            pib_medio = df_filtrado['PIB_per_Capita'].mean()
            gini_medio = df_filtrado['Gini'].mean()
            
            fig_scatter.add_hline(y=gini_medio, line_dash="dash", line_color="gray", opacity=0.7)
            fig_scatter.add_vline(x=pib_medio, line_dash="dash", line_color="gray", opacity=0.7)
            
            fig_scatter.update_layout(
                height=600,
                plot_bgcolor='rgba(248,247,255,0.5)',
                showlegend=True
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # EXPLICAÇÃO DO SCATTER PLOT
            st.markdown("""
            <div class="explanation-box">
                <h4>🎪 MAPA DE RELAÇÕES: ONDE CADA ESTADO SE ENCAIXA?</h4>
                
                <p><strong>Quadrante Ideal (Inferior Direito):</strong> Estados com <strong>alto PIB e baixa desigualdade</strong>. 
                Exemplo: Santa Catarina - o modelo a ser seguido.</p>
                
                <p><strong>Quadrante de Desafio (Superior Esquerdo):</strong> Estados com <strong>baixo PIB e alta desigualdade</strong>. 
                Exemplo: Maranhão - necessidade de políticas urgentes.</p>
                
                <p><strong>Quadrante de Oportunidade (Inferior Esquerdo):</strong> Estados com <strong>baixo PIB mas relativa igualdade</strong>. 
                Podem crescer mantendo a distribuição.</p>
                
                <p><strong>Quadrante de Concentração (Superior Direito):</strong> Estados <strong>ricos mas desiguais</strong>. 
                Precisam melhorar a distribuição dos ganhos.</p>
                
                <p><strong>Conclusão:</strong> O objetivo é mover todos os estados para o quadrante inferior direito - 
                <strong>ricos e igualitários</strong>.</p>
            </div>
            """, unsafe_allow_html=True)

# ===============================================================
# ABA 3: CONCLUSÕES
# ===============================================================
with tab3:
    st.markdown('<h2 class="sub-header">🎯 CONCLUSÕES E RECOMENDAÇÕES</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="explanation-box">
            <h3>✅ DESCOBERTAS PRINCIPAIS</h3>
            
            <h4>📈 Crescimento Inclusivo</h4>
            <p>O Brasil apresenta correlação negativa entre crescimento e desigualdade (-0.428), 
            indicando que o desenvolvimento econômico tem beneficiado os mais pobres.</p>
            
            <h4>🗺️ Desafios Regionais</h4>
            <p>Disparidade de 10.6x entre estados mais rico e mais pobre revela necessidade de 
            políticas regionais específicas.</p>
            
            <h4>🏆 Modelos de Sucesso</h4>
            <p>Santa Catarina combina alto desenvolvimento com baixa desigualdade (Gini 0.418), 
            servindo de referência nacional.</p>
            
            <h4>⚖️ Nordeste Prioritário</h4>
            <p>Região concentra os maiores desafios, exigindo atenção especial em políticas 
            redistributivas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="explanation-box">
            <h3>💡 RECOMENDAÇÕES ESTRATÉGICAS</h3>
            
            <h4>🎯 Políticas Regionais</h4>
            <p>Desenvolver estratégias específicas para cada contexto estadual e regional, 
            reconhecendo as diferentes realidades.</p>
            
            <h4>📚 Educação e Capacitação</h4>
            <p>Investir massivamente em educação nas regiões menos desenvolvidas para 
            quebrar ciclos de desigualdade.</p>
            
            <h4>🏗️ Infraestrutura Regional</h4>
            <p>Direcionar investimentos em infraestrutura para estados com menor desenvolvimento 
            econômico.</p>
            
            <h4>📊 Monitoramento Contínuo</h4>
            <p>Manter sistema de acompanhamento dos indicadores de desigualdade para 
            ajustar políticas quando necessário.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # MENSAGEM FINAL
    st.markdown("""
    <div style='background: linear-gradient(135deg, #6A0DAD, #9370DB); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-top: 2rem;'>
        <h2>🎓 CONCLUSÃO FINAL</h2>
        <p style='font-size: 1.2rem;'>
        O Brasil demonstra que <strong>crescimento econômico e redução de desigualdades podem caminhar juntos</strong>. 
        No entanto, os desafios regionais históricos exigem <strong>políticas persistentes e bem direcionadas</strong> 
        para alcançarmos um desenvolvimento verdadeiramente sustentável e inclusivo.
        </p>
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
