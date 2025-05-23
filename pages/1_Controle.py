import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import sys
import os

# Adicionar o diretório raiz ao path para importar utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    check_authentication, 
    add_transaction, 
    get_all_transactions, 
    calculate_balance, 
    format_btc,
    get_current_brazil_date,
    delete_transaction
)

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# Verificar autenticação
if not check_authentication():
    st.warning("Você precisa fazer login para acessar esta página.")
    st.stop()

st.title("💼 Controle Financeiro")

# Inicializar estado para controlar a atualização da página
if "transacao_adicionada" not in st.session_state:
    st.session_state.transacao_adicionada = False
    
if "transacao_apagada" not in st.session_state:
    st.session_state.transacao_apagada = False

# Função para marcar que uma transação foi adicionada
def marcar_transacao_adicionada():
    st.session_state.transacao_adicionada = True

# Função para marcar que uma transação foi apagada
def marcar_transacao_apagada(transaction_id):
    if delete_transaction(transaction_id):
        st.session_state.transacao_apagada = True
        

# Formulário para nova transação
with st.form("form_transacao", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    data = col1.date_input("Data", get_current_brazil_date())
    tipo = col2.selectbox("Tipo", ["Depósito", "Saque"])
    valor = col3.number_input("Valor (฿)", min_value=0.0, step=0.0001, format="%.4f")
    
    # Botões do formulário
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Adicionar", on_click=marcar_transacao_adicionada)
    with col2:
        limpar = st.form_submit_button("Limpar")

# Processar adição de transação
if st.session_state.transacao_adicionada and valor > 0:
    if add_transaction(data, tipo, valor):
        st.success("Transação adicionada com sucesso!")
        # Resetar o estado para evitar duplicação
        st.session_state.transacao_adicionada = False


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
    # Criar cópia do dataframe para exibição
    df_exibicao = df_transacoes.copy()
    
    # Formatar a data para exibição
    df_exibicao['Data'] = pd.to_datetime(df_exibicao['Data']).dt.strftime('%d/%m/%Y')
    
    # Formatar valores para exibição
    df_exibicao['Valor_Exibicao'] = df_exibicao['Valor'].apply(lambda x: format_btc(x))
    
    # Criar colunas para o dataframe
    col1, col2 = st.columns([0.85, 0.15])
    
    # Exibir dataframe principal
    with col1:
        st.dataframe(
            df_exibicao[['Data', 'Tipo', 'Valor_Exibicao']].rename(columns={'Valor_Exibicao': 'Valor'}),
            use_container_width=True
        )
    
    # Exibir opções para apagar transações
    with col2:
        st.subheader("Ações")
        for idx, row in df_exibicao.iterrows():
            if st.button(f"🗑️ Apagar", key=f"delete_{row['id']}"):
                marcar_transacao_apagada(row['id'])
                st.success(f"Transação de {row['Tipo']} no valor de {row['Valor_Exibicao']} apagada!")
                # O experimental_rerun já está na função marcar_transacao_apagada
    
    # Adicionar botão para exportar dados
    csv = df_exibicao[['Data', 'Tipo', 'Valor_Exibicao']].rename(columns={'Valor_Exibicao': 'Valor'}).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar transações (CSV)",
        data=csv,
        file_name="transacoes_financeiras.csv",
        mime="text/csv",
    )
else:
    st.info("Nenhuma transação registrada. Adicione sua primeira transação usando o formulário acima.")

# Resetar o estado de transação apagada
if st.session_state.transacao_apagada:
    st.session_state.transacao_apagada = False
