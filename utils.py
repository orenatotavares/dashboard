import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
import pytz

# Configuração do caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'dashboard.db')

# Função para verificar autenticação
def check_authentication():
    """
    Verifica se o usuário está autenticado.
    Retorna True se autenticado, False caso contrário.
    """
    return st.session_state.get("authenticated", False)

# Função para autenticar usuário
def authenticate_user(senha_digitada, senha_correta):
    """
    Autentica o usuário com base na senha fornecida.
    Armazena o estado de autenticação na session_state.
    """
    if senha_digitada == senha_correta:
        st.session_state.authenticated = True
        return True
    return False

# Função para inicializar o banco de dados
def init_database():
    """
    Inicializa o banco de dados SQLite para armazenar transações financeiras.
    Cria a tabela se não existir.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de transações se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Função para adicionar transação ao banco de dados
def add_transaction(data, tipo, valor):
    """
    Adiciona uma nova transação ao banco de dados.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO transacoes (data, tipo, valor, timestamp) VALUES (?, ?, ?, ?)",
        (data.strftime("%Y-%m-%d"), tipo, valor, timestamp)
    )
    
    conn.commit()
    conn.close()
    
    return True

# Função para obter todas as transações do banco de dados
def get_all_transactions():
    """
    Recupera todas as transações do banco de dados.
    Retorna um DataFrame pandas.
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT id, data, tipo, valor FROM transacoes ORDER BY data DESC"
    df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    # Converter a coluna de data para o formato datetime
    if not df.empty:
        df['Data'] = pd.to_datetime(df['data'])
        df = df.drop(columns=['data'])
        df = df.rename(columns={'tipo': 'Tipo', 'valor': 'Valor'})
        df['Valor'] = df['Valor'].astype(int)
    
    return df

# Função para apagar uma transação do banco de dados
def delete_transaction(transaction_id):
    """
    Apaga uma transação do banco de dados pelo ID.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transaction_id,))
    
    conn.commit()
    conn.close()
    
    return True

# Função para calcular o saldo total
def calculate_balance():
    """
    Calcula o saldo total com base nas transações.
    """
    df = get_all_transactions()
    
    if df.empty:
        return 0
    
    # Calcular saldo (depósitos positivos, saques negativos)
    df['Valor_Calculado'] = df.apply(
        lambda row: row["Valor"] if row["Tipo"] == "Depósito" else -row["Valor"], 
        axis=1
    )
    
    return df['Valor_Calculado'].sum()

# Função para formatar valores em Bitcoin
def format_btc(value):
    """
    Formata um valor para exibição em Bitcoin.
    """
    return f"฿ {value:,}".replace(",", ".")

    

# Função para obter o fuso horário do Brasil
def get_brazil_timezone():
    """
    Retorna o fuso horário do Brasil.
    """
    return pytz.timezone('America/Sao_Paulo')

# Função para obter a data atual no fuso horário do Brasil
def get_current_brazil_date():
    """
    Retorna a data atual no fuso horário do Brasil.
    """
    fuso_brasil = get_brazil_timezone()
    return datetime.now(fuso_brasil).date()
