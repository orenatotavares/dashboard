import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
from utils import (
    check_authentication, 
    add_transaction, 
    get_all_transactions, 
    calculate_balance, 
    format_btc,
    get_current_brazil_date
)

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# Verificar autenticação
if not check_authentication():
    st.warning("Você precisa fazer login para acessar esta página.")
    st.stop()

st.title("💼 Controle Financeiro")

# Formulário para nova transação
with st.form("form_transacao"):
    col1, col2, col3 = st.columns(3)
    data = col1.date_input("Data", get_current_brazil_date())
    tipo = col2.selectbox("Tipo", ["Depósito", "Saque"])
    valor = col3.number_input("Valor (฿)", min_value=0.0, step=0.0001, format="%.4f")
    submit = st.form_submit_button("Adicionar")

if submit and valor > 0:
    if add_transaction(data, tipo, valor):
        st.success("Transação adicionada com sucesso!")
        # Forçar atualização da página para mostrar a nova transação
        st.experimental_rerun()

# Obter transações do banco de dados
df_transacoes = get_all_transactions()

# Cálculo de saldo
saldo = calculate_balance()

# Obter lucro total da página principal
lucro_total = st.session_state.get("lucro_total", 0)

# Calcular saldo geral (saldo + lucro)
saldo_geral = saldo + lucro_total

# Exibir métricas
col1, col2, col3 = st.columns(3)
col1.metric("💰 Saldo na plataforma", format_btc(saldo))
col2.metric("📈 Lucro total operações", format_btc(lucro_total))
col3.metric("📊 Saldo total com lucros", format_btc(saldo_geral))

# Mostrar histórico
st.subheader("📜 Histórico de transações")

if not df_transacoes.empty:
    # Formatar a data para exibição
    df_transacoes['Data'] = pd.to_datetime(df_transacoes['Data']).dt.strftime('%d/%m/%Y')
    
    # Formatar valores para exibição
    df_transacoes['Valor'] = df_transacoes['Valor'].apply(lambda x: format_btc(x))
    
    # Exibir dataframe
    st.dataframe(df_transacoes, use_container_width=True)
else:
    st.info("Nenhuma transação registrada. Adicione sua primeira transação usando o formulário acima.")

# Adicionar botão para exportar dados
if not df_transacoes.empty:
    csv = df_transacoes.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar transações (CSV)",
        data=csv,
        file_name="transacoes_financeiras.csv",
        mime="text/csv",
    )
