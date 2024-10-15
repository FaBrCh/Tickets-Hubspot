import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import seaborn as sns
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Dashboard de Tickets", layout="wide")

# Função para carregar os dados
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    colunas_importantes = ['Ticket ID', 'Nome do ticket', 'Descrição do ticket', 'Data de criação', 
                        'Prioridade', 'Proprietário do ticket', 'Fonte', 'Categoria', 'Sub-categoria', 
                        'Associated Company', 'Data de fechamento', 'Tempo para o fechamento (HH:mm:ss)', 
                        'Resolução']
    df = df[colunas_importantes]
    df['Data de criação'] = pd.to_datetime(df['Data de criação'], errors='coerce')
    df['Data de fechamento'] = pd.to_datetime(df['Data de fechamento'], errors='coerce')
    df['Tempo para o fechamento'] = pd.to_timedelta(df['Tempo para o fechamento (HH:mm:ss)'], errors='coerce')
    return df

st.title("Dashboard de Análise de Tickets")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Sidebar para filtros
    st.sidebar.header("Filtros")

    # Novas opções de filtro de data
    filtro_data = st.sidebar.selectbox("Tipo de filtro de data", ["Sem filtro", "Intervalo", "Mês específico", "Ano específico"])

    if filtro_data == "Sem filtro":
        data_inicio = df['Data de criação'].min().date()
        data_fim = df['Data de criação'].max().date()
    elif filtro_data == "Intervalo":
        data_inicio = st.sidebar.date_input("Data de Início", df['Data de criação'].min().date())
        data_fim = st.sidebar.date_input("Data de Fim", df['Data de criação'].max().date())
    elif filtro_data == "Mês específico":
        mes = st.sidebar.selectbox("Selecione o mês", range(1, 13), format_func=lambda x: calendar.month_name[x])
        ano = st.sidebar.selectbox("Selecione o ano", range(df['Data de criação'].dt.year.min(), df['Data de criação'].dt.year.max() + 1))
        data_inicio = pd.Timestamp(year=ano, month=mes, day=1).date()
        data_fim = (data_inicio + pd.offsets.MonthEnd(1)).date()
    else:  # Ano específico
        ano = st.sidebar.selectbox("Selecione o ano", range(df['Data de criação'].dt.year.min(), df['Data de criação'].dt.year.max() + 1))
        data_inicio = pd.Timestamp(year=ano, month=1, day=1).date()
        data_fim = pd.Timestamp(year=ano, month=12, day=31).date()

    categoria = st.sidebar.multiselect("Selecione as Categorias", options=df['Categoria'].unique())
    subcategoria = st.sidebar.multiselect("Selecione as Subcategorias", options=df['Sub-categoria'].unique())
    proprietario = st.sidebar.multiselect("Selecione os Proprietários", options=df['Proprietário do ticket'].dropna().unique())
    empresa = st.sidebar.multiselect("Selecione as Empresas", options=df['Associated Company'].dropna().unique())

    # Aplicar filtros
    if filtro_data == "Sem filtro":
        mask = pd.Series(True, index=df.index)
    else:
        mask = (df['Data de criação'].dt.date >= data_inicio) & (df['Data de criação'].dt.date <= data_fim)

    if categoria:
        mask &= df['Categoria'].isin(categoria)
    if subcategoria:
        mask &= df['Sub-categoria'].isin(subcategoria)
    if proprietario:
        mask &= df['Proprietário do ticket'].isin(proprietario)
    if empresa:
        mask &= df['Associated Company'].isin(empresa)
    filtered_df = df[mask]

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Tickets", len(filtered_df))
    col2.metric("Tickets Abertos", len(filtered_df[filtered_df['Data de fechamento'].isnull()]))
    col3.metric("Tempo Médio de Resolução", f"{filtered_df['Tempo para o fechamento'].mean().total_seconds() / 3600:.2f} horas")
    col4.metric("Tickets de Alta Prioridade", len(filtered_df[filtered_df['Prioridade'] == 'High']))

    # Gráficos
    st.header("Análise de Tickets")

    # Tickets por Categoria
    st.subheader("Tickets por Categoria")
    categoria_counts = filtered_df['Categoria'].value_counts()
    categoria_percentages = (categoria_counts / len(filtered_df) * 100)
    fig_categoria = px.bar(categoria_counts, title="Tickets por Categoria")
    fig_categoria.update_traces(
        text=categoria_counts.values,
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Quantidade: %{y}<br>" +
                      "Porcentagem: %{customdata:.2f}%<extra></extra>",
        customdata=categoria_percentages
    )
    st.plotly_chart(fig_categoria, use_container_width=True)

    # Tickets por Subcategoria (Top 10)
    st.subheader("Top 10 Subcategorias")
    subcategoria_counts = filtered_df['Sub-categoria'].value_counts().nlargest(10)
    subcategoria_percentages = (subcategoria_counts / len(filtered_df) * 100)
    fig_subcategoria = px.bar(subcategoria_counts, title="Top 10 Subcategorias")
    fig_subcategoria.update_traces(
        text=subcategoria_counts.values,
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Quantidade: %{y}<br>" +
                      "Porcentagem: %{customdata:.2f}%<extra></extra>",
        customdata=subcategoria_percentages
    )
    st.plotly_chart(fig_subcategoria, use_container_width=True)

    # Tickets por Proprietário
    st.subheader("Tickets por Proprietário")
    proprietario_counts = filtered_df['Proprietário do ticket'].value_counts()
    proprietario_percentages = (proprietario_counts / len(filtered_df) * 100)
    fig_proprietario = px.bar(proprietario_counts, title="Tickets por Proprietário")
    fig_proprietario.update_traces(
        text=proprietario_counts.values,
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Quantidade: %{y}<br>" +
                      "Porcentagem: %{customdata:.2f}%<extra></extra>",
        customdata=proprietario_percentages
    )
    st.plotly_chart(fig_proprietario, use_container_width=True)

    # Tickets criados por período
    daily_counts = filtered_df.groupby(filtered_df['Data de criação'].dt.date).size().reset_index(name='count')
    fig_timeline = px.line(daily_counts, x='Data de criação', y='count', title="Tickets Criados por Dia")
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Tickets criados por mês
    st.subheader("Tickets Criados por Mês")
    filtered_df['Mês'] = filtered_df['Data de criação'].dt.to_period('M')
    monthly_counts = filtered_df['Mês'].value_counts().sort_index()
    monthly_percentages = (monthly_counts / len(filtered_df) * 100)
    monthly_counts.index = monthly_counts.index.astype(str)
    fig_month = px.bar(monthly_counts, title="Tickets Criados por Mês")
    fig_month.update_traces(
        text=monthly_counts.values,
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Quantidade: %{y}<br>" +
                      "Porcentagem: %{customdata:.2f}%<extra></extra>",
        customdata=monthly_percentages
    )
    st.plotly_chart(fig_month, use_container_width=True)

    # Tempo médio de resolução por categoria
    st.subheader("Tempo Médio de Resolução por Categoria")
    tempo_medio = filtered_df.groupby('Categoria')['Tempo para o fechamento'].mean().apply(lambda x: x.total_seconds() / 3600).sort_values(ascending=False)
    categoria_counts = filtered_df['Categoria'].value_counts()
    categoria_percentages = (categoria_counts / len(filtered_df) * 100)
    fig_tempo = px.bar(tempo_medio, title="Tempo Médio de Resolução por Categoria (Horas)")
    fig_tempo.update_traces(
        text=[f"{val:.2f}" for val in tempo_medio.values],
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Tempo Médio: %{y:.2f} horas<br>" +
                      "Quantidade: %{customdata[0]}<br>" +
                      "Porcentagem: %{customdata[1]:.2f}%<extra></extra>",
        customdata=list(zip(categoria_counts[tempo_medio.index], categoria_percentages[tempo_medio.index]))
    )
    fig_tempo.update_layout(yaxis_title="Horas")
    st.plotly_chart(fig_tempo, use_container_width=True)

    # Tickets por Empresa Associada (Top 10)
    st.subheader("Top 10 Empresas Associadas")
    empresa_counts = filtered_df['Associated Company'].value_counts().nlargest(10)
    empresa_percentages = (empresa_counts / len(filtered_df) * 100)
    fig_empresa = px.bar(empresa_counts, title="Top 10 Empresas Associadas")
    fig_empresa.update_traces(
        text=empresa_counts.values,
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                      "Quantidade: %{y}<br>" +
                      "Porcentagem: %{customdata:.2f}%<extra></extra>",
        customdata=empresa_percentages
    )
    st.plotly_chart(fig_empresa, use_container_width=True)

    # Distribuição do tempo de fechamento
    filtered_df['Tempo para o fechamento (horas)'] = filtered_df['Tempo para o fechamento'].dt.total_seconds() / 3600
    fig_tempo_dist = px.histogram(filtered_df, x='Tempo para o fechamento (horas)', 
                                  title="Distribuição do Tempo de Fechamento (Horas)",
                                  labels={'Tempo para o fechamento (horas)': 'Horas'})
    fig_tempo_dist.update_traces(xbins=dict(size=4))  # Ajuste o tamanho dos bins conforme necessário
    fig_tempo_dist.update_layout(bargap=0.1)
    st.plotly_chart(fig_tempo_dist, use_container_width=True)

    # Tabela de dados
    st.header("Dados dos Tickets")
    st.dataframe(filtered_df)

    # Download dos dados filtrados
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download dos dados filtrados",
        data=csv,
        file_name="tickets_filtrados.csv",
        mime="text/csv",
    )

    # Após os gráficos existentes, adicione o mapa de calor
    st.header("Análise de Categorias e Subcategorias")

    # Preparar dados para o mapa de calor
    heatmap_data = filtered_df.groupby(['Categoria', 'Sub-categoria']).size().unstack(fill_value=0)

    # Criar o mapa de calor
    fig_heatmap = px.imshow(heatmap_data.T,  # Transpor os dados para trocar os eixos
                            labels=dict(x="Categoria", y="Sub-categoria", color="Número de Tickets"),
                            x=heatmap_data.index,
                            y=heatmap_data.columns,
                            aspect="auto",
                            title="Mapa de Calor: Categorias vs Subcategorias")

    fig_heatmap.update_xaxes(side="top")
    fig_heatmap.update_layout(height=800)  # Aumentar a altura para melhor visualização
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Após os filtros e antes dos gráficos existentes

    st.header("Análises Descritivas")

    # Estatísticas resumidas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Estatísticas de Tempo de Resolução (em horas)")
        tempo_resolucao = filtered_df['Tempo para o fechamento'].dt.total_seconds() / 3600
        stats = tempo_resolucao.describe()
        st.write(f"Média: {stats['mean']:.2f}")
        st.write(f"Mediana: {stats['50%']:.2f}")
        st.write(f"Desvio Padrão: {stats['std']:.2f}")
        st.write(f"Mínimo: {stats['min']:.2f}")
        st.write(f"Máximo: {stats['max']:.2f}")

    with col2:
        st.subheader("Distribuição de Prioridades")
        prioridade_counts = filtered_df['Prioridade'].value_counts()
        fig_prioridade = px.pie(values=prioridade_counts.values, names=prioridade_counts.index, title="Distribuição de Prioridades")
        st.plotly_chart(fig_prioridade, use_container_width=True)

    # Análise de tendência temporal
    st.subheader("Tendência de Tickets ao Longo do Tempo")
    tickets_por_dia = filtered_df.groupby(filtered_df['Data de criação'].dt.date).size().reset_index(name='Número de Tickets')
    fig_tendencia = px.line(tickets_por_dia, x='Data de criação', y='Número de Tickets', title="Tendência de Tickets Criados por Dia")
    st.plotly_chart(fig_tendencia, use_container_width=True)

    # Top 5 categorias com maior tempo médio de resolução
    st.subheader("Top 5 Categorias com Maior Tempo Médio de Resolução")
    top_5_categorias = filtered_df.groupby('Categoria')['Tempo para o fechamento'].mean().sort_values(ascending=False).head(5)
    top_5_categorias = top_5_categorias.dt.total_seconds() / 3600  # Convertendo para horas
    fig_top_5 = px.bar(top_5_categorias, x=top_5_categorias.index, y=top_5_categorias.values, 
                       labels={'y': 'Tempo Médio (horas)', 'x': 'Categoria'},
                       title="Top 5 Categorias com Maior Tempo Médio de Resolução")
    fig_top_5.update_traces(text=[f"{float(val):.2f}" for val in top_5_categorias.values], textposition='outside')
    st.plotly_chart(fig_top_5, use_container_width=True)

    # Correlação entre prioridade e tempo de resolução
    st.subheader("Relação entre Prioridade e Tempo de Resolução")
    tempo_por_prioridade = filtered_df.groupby('Prioridade')['Tempo para o fechamento'].mean().sort_values(ascending=False)
    tempo_por_prioridade = tempo_por_prioridade.dt.total_seconds() / 3600  # Convertendo para horas
    fig_prioridade_tempo = px.bar(tempo_por_prioridade, x=tempo_por_prioridade.index, y=tempo_por_prioridade.values,
                                  labels={'y': 'Tempo Médio (horas)', 'x': 'Prioridade'},
                                  title="Tempo Médio de Resolução por Prioridade")
    fig_prioridade_tempo.update_traces(text=[f"{float(val):.2f}" for val in tempo_por_prioridade.values], textposition='outside')
    st.plotly_chart(fig_prioridade_tempo, use_container_width=True)

    st.header("Análises Temporais")

    # Preparar dados
    filtered_df['Mês'] = filtered_df['Data de criação'].dt.to_period('M').astype(str)

    # Tickets por mês e categoria
    st.subheader("Tickets Criados por Mês e Categoria")
    tickets_mes_categoria = filtered_df.groupby(['Mês', 'Categoria']).size().unstack(fill_value=0)
    fig_mes_categoria = px.bar(tickets_mes_categoria, 
                               x=tickets_mes_categoria.index, 
                               y=tickets_mes_categoria.columns,
                               title="Tickets Criados por Mês e Categoria",
                               labels={'value': 'Número de Tickets', 'Mês': 'Mês', 'variable': 'Categoria'})
    fig_mes_categoria.update_layout(barmode='stack', xaxis={'categoryorder':'category ascending'})
    st.plotly_chart(fig_mes_categoria, use_container_width=True)

    # Tickets por mês e subcategoria (top 10 subcategorias)
    st.subheader("Tickets Criados por Mês e Subcategoria (Top 10)")
    top_10_subcategorias = filtered_df['Sub-categoria'].value_counts().nlargest(10).index
    tickets_mes_subcategoria = filtered_df[filtered_df['Sub-categoria'].isin(top_10_subcategorias)].groupby(['Mês', 'Sub-categoria']).size().unstack(fill_value=0)
    fig_mes_subcategoria = px.bar(tickets_mes_subcategoria, 
                                  x=tickets_mes_subcategoria.index, 
                                  y=tickets_mes_subcategoria.columns,
                                  title="Tickets Criados por Mês e Subcategoria (Top 10)",
                                  labels={'value': 'Número de Tickets', 'Mês': 'Mês', 'variable': 'Subcategoria'})
    fig_mes_subcategoria.update_layout(barmode='stack', xaxis={'categoryorder':'category ascending'})
    st.plotly_chart(fig_mes_subcategoria, use_container_width=True)

    # Análise de tendência por categoria
    st.subheader("Tendência de Tickets por Categoria")
    fig_tendencia_categoria = px.line(tickets_mes_categoria, 
                                      x=tickets_mes_categoria.index, 
                                      y=tickets_mes_categoria.columns,
                                      title="Tendência de Tickets por Categoria",
                                      labels={'value': 'Número de Tickets', 'Mês': 'Mês', 'variable': 'Categoria'})
    st.plotly_chart(fig_tendencia_categoria, use_container_width=True)

    # Proporção de categorias ao longo do tempo
    st.subheader("Proporção de Categorias ao Longo do Tempo")
    proporcao_categorias = tickets_mes_categoria.div(tickets_mes_categoria.sum(axis=1), axis=0)
    fig_proporcao = px.area(proporcao_categorias, 
                            x=proporcao_categorias.index, 
                            y=proporcao_categorias.columns,
                            title="Proporção de Categorias ao Longo do Tempo",
                            labels={'value': 'Proporção', 'Mês': 'Mês', 'variable': 'Categoria'})
    st.plotly_chart(fig_proporcao, use_container_width=True)

    # Adicionar explicações
    st.write("""
    Estas análises temporais nos permitem observar como o volume e a distribuição dos tickets evoluem ao longo do tempo:

    1. O gráfico de barras empilhadas de "Tickets Criados por Mês e Categoria" mostra o volume total de tickets por mês, com a contribuição de cada categoria.
    2. O gráfico de "Tickets Criados por Mês e Subcategoria (Top 10)" foca nas 10 subcategorias mais frequentes, permitindo uma visão mais detalhada.
    3. A "Tendência de Tickets por Categoria" ajuda a identificar padrões sazonais ou tendências de longo prazo para cada categoria.
    4. A "Proporção de Categorias ao Longo do Tempo" mostra como a composição relativa das categorias muda mês a mês, independentemente do volume total.

    Estas visualizações podem ajudar a identificar:
    - Períodos de pico ou baixa demanda
    - Mudanças na importância relativa de diferentes categorias ou subcategorias
    - Possíveis efeitos sazonais ou tendências de longo prazo
    """)

else:
    st.write("Por favor, faça o upload de um arquivo CSV para começar a análise.")