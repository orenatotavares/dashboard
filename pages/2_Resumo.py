import streamlit as st
import pandas as pd
import plotly.express as px
from utils import (
    check_authentication, 
    calculate_balance, 
    format_btc,
    get_all_transactions
)

# Configuração da página
st.set_page_config(page_title="Resumo Financeiro", layout="wide")

# Verificar autenticação
if not check_authentication():
    st.warning("Você precisa fazer login para acessar esta página.")
    st.stop()

st.title("📈 Resumo Financeiro")

# Obter dados financeiros
saldo = calculate_balance()
lucro_total = st.session_state.get("lucro_total", 0)
saldo_geral = saldo + lucro_total

# Obter transações
df_transacoes = get_all_transactions()

# Exibir métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("💰 Saldo na plataforma", format_btc(saldo))
col2.metric("📈 Lucro total operações", format_btc(lucro_total))
col3.metric("📊 Saldo total com lucros", format_btc(saldo_geral))

# Criar gráficos de análise financeira
st.subheader("📊 Análise de Transações")

if not df_transacoes.empty:
    # Preparar dados para gráficos
    df_transacoes['Data'] = pd.to_datetime(df_transacoes['Data'])
    df_transacoes['Mês'] = df_transacoes['Data'].dt.strftime('%m/%Y')
    df_transacoes['Valor_Calculado'] = df_transacoes.apply(
        lambda row: row["Valor"] if row["Tipo"] == "Depósito" else -row["Valor"], 
        axis=1
    )
    
    # Gráfico de transações por tipo
    fig1 = px.pie(
        df_transacoes, 
        names='Tipo', 
        values='Valor',
        title='Distribuição de Transações por Tipo',
        color_discrete_sequence=['#4CAF50', '#F44336']
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico de evolução do saldo ao longo do tempo
    df_evolucao = df_transacoes.sort_values('Data')
    df_evolucao['Saldo_Acumulado'] = df_evolucao['Valor_Calculado'].cumsum()
    
    fig2 = px.line(
        df_evolucao,
        x='Data',
        y='Saldo_Acumulado',
        title='Evolução do Saldo ao Longo do Tempo',
        labels={'Saldo_Acumulado': 'Saldo (฿)', 'Data': 'Data'},
        markers=True
    )
    fig2.update_layout(yaxis_title='Saldo (฿)', xaxis_title='Data')
    st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico de transações por mês
    df_mensal = df_transacoes.groupby(['Mês', 'Tipo'])['Valor'].sum().reset_index()
    
    fig3 = px.bar(
        df_mensal,
        x='Mês',
        y='Valor',
        color='Tipo',
        title='Transações Mensais por Tipo',
        labels={'Valor': 'Valor (฿)', 'Mês': 'Mês'},
        barmode='group',
        color_discrete_sequence=['#4CAF50', '#F44336']
    )
    fig3.update_layout(yaxis_title='Valor (฿)', xaxis_title='Mês')
    st.plotly_chart(fig3, use_container_width=True)
    
else:
    st.info("Nenhuma transação registrada. Adicione transações na página de Controle Financeiro para visualizar análises.")

# Adicionar informações sobre o saldo total
st.subheader("💡 Informações")
st.info("""
Este resumo financeiro integra os dados do seu controle financeiro com os lucros das operações.
- O saldo na plataforma representa a soma de todos os depósitos menos os saques.
- O lucro total das operações é calculado automaticamente com base nos dados da página principal.
- O saldo total representa o valor real disponível, considerando tanto o saldo quanto os lucros.
""")
