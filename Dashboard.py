import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title='Dashboard de Vendas', layout='wide')

# Função para formatar números grandes
def formata_numero(valor, prefixo= ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:,.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:,.2f} milhões'

st.title('DASHBOARD DE VENDAS 🛒')

url = 'https://labdados.com/produtos'   #Leitura dos dados da api

#Filtrando dados por regiao
regioes = ['Brasil', 'centro-oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Selecione a região', regioes)
if regiao == 'Brasil':
    regiao = ''

# Filtro por ano
todos_anos = st.sidebar.checkbox('Dados de todos os periodos', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)


query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)    #Fazendo a requisição da api
dados = pd.DataFrame.from_dict(response.json()) #transformando os dados em json
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')  #Transformando a coluna data em formato datetime

# Filtro dos vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', options=dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas

## Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()   #Agrupando os dados por local da compra e somando o preço
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index() #Agrupando os dados por mês e somando o preço
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year #Pegando o ano da data da compra
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name() #Pegando o mês da data da compra

receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False) #Agrupando os dados por categoria e somando o preço

### Tabela de quantidade de vendas


### tabela vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count'])) # Agrupando os dados por vendedor e somando o preço e contando a quantidade de vendas

vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

## Gráficos 
# Gráfico de mapa de receita por estado
fig_mapa_receita = px.scatter_geo(receita_estados,
                                   lat = 'lat',
                                   lon = 'lon',
                                   scope = 'south america',
                                   size = 'Preço',
                                   template = 'seaborn',
                                   hover_name = 'Local da compra',
                                   hover_data = {'lat':False,'lon':False},
                                   title = 'Receita por Estado')

# Gráfico de linha de receita mensal
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mês',
                             y = 'Preço',
                             markers= True,
                             range_x=[0, receita_mensal.max()],
                             color= 'Ano',
                             line_dash= 'Ano',
                             title = 'Receita Mensal'
)
fig_receita_mensal.update_layout(yaxis_title='Receita')

# Grafico de barras de receita por categoria
fig_receita_estados = px.bar(receita_estados.head(),
                                            x = 'Local da compra',
                                            y = 'Preço',
                                            text_auto = True,
                                            title = 'Top estados')

fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categoria = px.bar(receita_categoria,
                               text_auto=True,
                               title='Receita por Categoria de Produto')


fig_receita_categoria.update_layout(yaxis_title='Receita')


## Vissualização no streamlit

# Construindo as abas
aba1, aba2, aba3 = st.tabs(['Rceita', 'Quantidade de vendas', 'Vendedores'])


with aba1:
    coluna1, coluna2 = st.columns(2)  #Criando duas colunas para mostrar as métricas
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))   # Somando a coluna preço para mostrar a receita total
        st.plotly_chart(fig_mapa_receita, use_container_width=True)  #Mostrando o gráfico de mapa de receita
        st.plotly_chart(fig_receita_estados, use_container_width=True)  #Mostrando o gráfico de receita por estado
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) # Mostrando a quantidade de vendas (número de linhas)
        st.plotly_chart(fig_receita_mensal, use_container_width=True)  #Mostrando o gráfico de receita mensal
        st.plotly_chart(fig_receita_categoria, use_container_width=True)  #Mostrando o gráfico de receita por categoria

with aba2:
    coluna1, coluna2 = st.columns(2)  #Criando duas colunas para mostrar as métricas
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))   # Somando a coluna preço para mostrar a receita total
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) # Mostrando a quantidade de vendas (número de linhas)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)  # Input para quantidade de vendedores a mostrar
    coluna1, coluna2 = st.columns(2)  #Criando duas colunas para mostrar as métricas

    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))   # Somando a coluna preço para mostrar a receita total
        fig_receita_vendedores = px.bar(
            vendedores[['sum']]
            .sort_values('sum', ascending=False)
            .head(qtd_vendedores)
            .reset_index(),
            x='sum',
            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} Receita por Vendedor'
        )
        fig_receita_vendedores.update_layout(yaxis_title='Receita')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) # Mostrando a quantidade de vendas (número de linhas)
        fig_vendas_vendedores = px.bar(vendedores[['count']]
            .sort_values('count', ascending=False)
            .head(qtd_vendedores)
            .reset_index(),
            x = 'count',
            y = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
            text_auto = True,
            title=f'Top {qtd_vendedores} Quantidade de Vendas')
        fig_vendas_vendedores.update_layout(yaxis_title='Quantidade de Vendas')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True   
)
