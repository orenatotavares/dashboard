import streamlit as st
import pandas as pd
import plotly.express as px
import time
import hmac
import base64
import hashlib
import urllib.parse
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz

# Configuração inicial
st.set_page_config(page_title="Dashboard de Ordens", layout="wide")
st.title("📊 Dashboard")

# Carrega variáveis do .env
load_dotenv()

# Autenticação
senha_correta = os.getenv("SENHA_DASHBOARD")
senha_digitada = st.text_input("Digite a senha para acessar o dashboard:", type="password")
if senha_digitada != senha_correta:
    st.warning("Acesso restrito. Digite a senha correta.")
    st.stop()

# Chaves da API
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
passphrase = os.getenv("PASSPHRASE")

if isinstance(api_secret, str):
    api_secret = api_secret.encode()

def generate_signature(timestamp, method, path, query_string, secret):
    message = f"{timestamp}{method}{path}{query_string}"
    signature = hmac.new(secret, message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

@st.cache_data(ttl=600) # Adiciona cache para evitar chamadas repetidas à API
def get_closed_positions():
    base_url = 'https://api.lnmarkets.com'
    path = '/v2/futures'
    method = 'GET'
    params = {'type': 'closed', 'limit': 1000}
    query_string = urllib.parse.urlencode(params )
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, path, query_string, api_secret)
    headers = {
        'LNM-ACCESS-KEY': api_key, 'LNM-ACCESS-SIGNATURE': signature,
        'LNM-ACCESS-PASSPHRASE': passphrase, 'LNM-ACCESS-TIMESTAMP': timestamp,
    }
    try:
        response = requests.get(f"{base_url}{path}?{query_string}", headers=headers)
        response.raise_for_status()
        data = pd.DataFrame(response.json())
        if data.empty:
            st.warning("Nenhum dado retornado pela API.")
            return pd.DataFrame()
        return data
    except requests.RequestException as e:
        st.error(f"Erro ao acessar a API: {e}")
        return pd.DataFrame()

def process_data(df):
    if df.empty: return df
    required_columns = ['market_filled_ts', 'closed_ts', 'opening_fee', 'closing_fee', 'sum_carry_fees', 'pl', 'entry_margin', 'price']
    if not all(col in df.columns for col in required_columns):
        st.error("Dados da API incompletos. Colunas necessárias não encontradas.")
        return pd.DataFrame()

    df = df[df['market_filled_ts'].notna() & df['closed_ts'].notna()].copy()
    fuso_brasil = pytz.timezone('America/Sao_Paulo')
    df['Saida'] = pd.to_datetime(df['closed_ts'], unit='ms', errors='coerce').dt.tz_localize('UTC').dt.tz_convert(fuso_brasil)
    df['Entrada'] = pd.to_datetime(df['market_filled_ts'], unit='ms', errors='coerce').dt.tz_localize('UTC').dt.tz_convert(fuso_brasil)
    
    df['Taxa'] = df['opening_fee'] + df['closing_fee'] + df['sum_carry_fees']
    df['Lucro'] = df['pl'] - df['Taxa']
    df['ROI'] = (df['Lucro'] / df['entry_margin']) * 100
    
    df = df.sort_values(by='Saida').reset_index(drop=True)
    df['Lucro_Acumulado'] = df['Lucro'].cumsum()
    
    df.index = df.index + 1
    df.index.name = "Nº"
    return df

# --- Funções de Gráfico (com melhorias) ---

def create_monthly_chart(df):
    df_monthly = df.set_index('Saida').resample('M').agg({'Lucro': 'sum'}).reset_index()
    df_monthly['Mes'] = df_monthly['Saida'].dt.strftime('%b/%Y')
    df_monthly['Cor'] = ['green' if lucro >= 0 else 'red' for lucro in df_monthly['Lucro']]
    
    fig = px.bar(
        df_monthly, x='Mes', y='Lucro', text='Lucro',
        title='Lucro Mensal', labels={'Lucro': 'Lucro (฿)', 'Mes': 'Mês'}
    )
    fig.update_traces(
        marker_color=df_monthly['Cor'],
        texttemplate='₿%{text:,.0f}', textposition='outside'
    )
    fig.update_layout(yaxis_title='Lucro (฿)', xaxis_title='Mês', bargap=0.4)
    return fig

# --- Layout do Dashboard ---

# Carrega os dados (usando cache)
df_raw = get_closed_positions()
df_processed = process_data(df_raw)

if not df_processed.empty:
    # --- Barra Lateral com Filtros Interativos ---
    st.sidebar.header("Filtros Interativos")
    
    # Filtro de data
    min_date = df_processed['Saida'].min().date()
    max_date = df_processed['Saida'].max().date()
    
    date_range = st.sidebar.date_input(
        "Selecione o Período de Análise",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    
    # Garante que o filtro tenha duas datas
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Filtra o DataFrame principal com base no intervalo de datas
        mask = (df_processed['Saida'].dt.date >= start_date) & (df_processed['Saida'].dt.date <= end_date)
        df_filtered = df_processed.loc[mask]
    else:
        st.sidebar.warning("Por favor, selecione um intervalo de datas válido.")
        df_filtered = df_processed # Usa o dataframe completo se o filtro falhar

    # --- Exibição Principal ---
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para o período selecionado.")
    else:
        # Métricas
        st.subheader("Métricas de Desempenho do Período")
        lucro_total = df_filtered['Lucro'].sum()
        total_investido = df_filtered['entry_margin'].sum()
        roi_total = (lucro_total / total_investido) * 100 if total_investido != 0 else 0
        num_ordens = len(df_filtered)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Lucro Total", f"₿ {int(lucro_total):,}".replace(",", "."))
        col2.metric("💰 Total Investido", f"₿ {int(total_investido):,}".replace(",", "."))
        col3.metric("📊 ROI Total", f"{roi_total:.2f}%")
        col4.metric("📋 Total de Ordens", num_ordens)

        st.markdown("---")

        # --- Gráficos ---
        st.subheader("Visualização de Dados")
        
        # 1. Curva de Lucro Acumulado
        st.markdown("#### Curva de Lucro Acumulado")
        st.area_chart(df_filtered.set_index('Saida')[['Lucro_Acumulado']])

        # 2. Gráfico Mensal com Cores Dinâmicas
        fig_monthly = create_monthly_chart(df_filtered)
        st.plotly_chart(fig_monthly, use_container_width=True)

        # Tabela de Ordens
        st.subheader("📋 Detalhes das Ordens Fechadas")
        df_display = df_filtered[['Entrada', 'entry_margin', 'price', 'Saida', 'Taxa', 'Lucro', 'ROI']].rename(columns={
            'entry_margin': 'Margem', 'price': 'Preço de Entrada'
        })
        
        st.dataframe(
            df_display.style.format({
                'Entrada': '{:%d/%m/%Y %H:%M}',
                'Saida': '{:%d/%m/%Y %H:%M}',
                'Margem': '₿ {:,.0f}',
                'Preço de Entrada': '$ {:,.1f}',
                'Taxa': '₿ {:,.0f}',
                'Lucro': '₿ {:,.0f}',
                'ROI': '{:.2f}%'
            }).background_gradient(cmap='RdYlGn', subset=['Lucro', 'ROI']),
            use_container_width=True
        )
else:
    st.warning("Nenhuma ordem encontrada ou erro na API. Tente atualizar a página.")
