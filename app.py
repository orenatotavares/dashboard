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
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from datetime import datetime
import pytz
from utils import check_authentication, authenticate_user, init_database, get_brazil_timezone

# Configuração da página
st.set_page_config(page_title="Dashboard de Ordens", layout="wide")

# Inicialização do banco de dados
init_database()

# Carrega variáveis do .env
load_dotenv()

# Autenticação com senha
# Usar variável de ambiente ou senha padrão para implantação
senha_correta = os.getenv("SENHA_DASHBOARD")

# Verificar autenticação
if not check_authentication():
    st.title("🔒 Login")
    st.markdown("""
    ### Bem-vindo ao Dashboard de Ordens
    
    Por favor, faça login para acessar o dashboard.
    """)
    
    # Usar form para capturar o Enter automaticamente
    with st.form(key="login_form"):
        senha_digitada = st.text_input("Digite a senha para acessar o dashboard:", type="password")
        submit_button = st.form_submit_button("Entrar")
        
        if submit_button:
            if authenticate_user(senha_digitada, senha_correta):
                st.success("Login realizado com sucesso!")
                # Usar experimental_rerun apenas para o login
            else:
                st.error("Senha incorreta. Tente novamente.")
    
    st.stop()

# Se chegou aqui, o usuário está autenticado
st.title("📊 Dashboard")

# Chaves da API
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
passphrase = os.getenv("PASSPHRASE")

# Verificar se as chaves da API estão configuradas
if not api_key or not api_secret or not passphrase:
    st.warning("⚠️ Chaves da API não configuradas. Configure as variáveis de ambiente API_KEY, API_SECRET e PASSPHRASE.")
    
    # Criar dados de exemplo para demonstração
    if "df" not in st.session_state or st.session_state.df.empty:
        # Criar dados de exemplo
        data = {
            'market_filled_ts': [1620000000000, 1620100000000, 1620200000000, 1620300000000],
            'closed_ts': [1620050000000, 1620150000000, 1620250000000, 1620350000000],
            'entry_margin': [1000, 2000, 1500, 3000],
            'price': [50000, 51000, 52000, 49000],
            'opening_fee': [10, 20, 15, 30],
            'closing_fee': [10, 20, 15, 30],
            'sum_carry_fees': [5, 10, 7, 15],
            'pl': [200, -300, 400, -200]
        }
        st.session_state.df = pd.DataFrame(data)
        st.info("Exibindo dados de exemplo para demonstração.")
else:
    if isinstance(api_secret, str):
        api_secret = api_secret.encode()

    def generate_signature(timestamp, method, path, query_string, secret):
        message = f"{timestamp}{method}{path}{query_string}"
        signature = hmac.new(secret, message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def get_closed_positions():
        try:
            base_url = 'https://api.lnmarkets.com'
            path = '/v2/futures'
            method = 'GET'
            params = {'type': 'closed', 'limit': 1000}
            query_string = urllib.parse.urlencode(params)
            timestamp = str(int(time.time() * 1000))
            signature = generate_signature(timestamp, method, path, query_string, api_secret)

            headers = {
                'LNM-ACCESS-KEY': api_key,
                'LNM-ACCESS-SIGNATURE': signature,
                'LNM-ACCESS-PASSPHRASE': passphrase,
                'LNM-ACCESS-TIMESTAMP': timestamp,
            }

            url = f"{base_url}{path}?{query_string}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return pd.DataFrame(response.json())
            else:
                st.error(f"Erro na API: {response.status_code}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao acessar a API: {str(e)}")
            return pd.DataFrame()

    # Botão de atualização manual
    if st.button("🔄 Atualizar dados"):
        with st.spinner("Carregando dados..."):
            st.session_state.df = get_closed_positions()

    # Carregamento do dataframe da sessão
    if "df" not in st.session_state:
        with st.spinner("Carregando dados iniciais..."):
            st.session_state.df = get_closed_positions()

df = st.session_state.df

# Processamento
if not df.empty:
    if 'market_filled_ts' in df.columns and 'closed_ts' in df.columns:
        df = df[df['market_filled_ts'].notna() & df['closed_ts'].notna()]
        df['Entrada'] = pd.to_datetime(df['market_filled_ts'], unit='ms', errors='coerce').dt.strftime('%d/%m/%Y')
        df['Saida'] = pd.to_datetime(df['closed_ts'], unit='ms', errors='coerce').dt.strftime('%d/%m/%Y')
    else:
        st.error("Colunas de data não encontradas no DataFrame.")
        st.stop()

    df['Taxa'] = df['opening_fee'] + df['closing_fee'] + df['sum_carry_fees']
    df['Lucro'] = df['pl'] - df['Taxa']
    df['ROI'] = (df['Lucro'] / df['entry_margin']) * 100
    df = df[df['Lucro'] != 0]
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Nº"

    # Métricas
    total_investido = df['entry_margin'].sum()
    lucro_total = df['Lucro'].sum()
    roi_total = (lucro_total / total_investido) * 100 if total_investido != 0 else 0
    num_ordens = len(df)

    # Armazenar o lucro total na sessão para uso em outras páginas
    st.session_state.lucro_total = lucro_total

    # Métricas do dia atual
    fuso_brasil = get_brazil_timezone()
    agora = datetime.now(fuso_brasil)
    data_hoje = agora.date()
    df_hoje = df.copy()
    df_hoje['closed_ts_dt'] = pd.to_datetime(df_hoje['closed_ts'], unit='ms', errors='coerce').dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    df_hoje = df_hoje[df_hoje['closed_ts_dt'].dt.date == data_hoje]
    
    lucro_dia = df_hoje['Lucro'].sum()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Total Investido", f"฿ {int(total_investido):,}".replace(",", "."))
    col2.metric("📈 Lucro Total", f"฿ {int(lucro_total):,}".replace(",", "."))
    col3.metric("📊 ROI Total", f"{roi_total:.2f} %")
    col4.metric("📋 Total de Ordens", num_ordens)
    col5.metric("📆 Lucro do Dia", f"฿ {int(lucro_dia):,}".replace(",", "."))

    # Preparar dados para gráfico
    df_dashboard = df.copy()
    df_dashboard['Saida'] = pd.to_datetime(df_dashboard['Saida'], format='%d/%m/%Y')
    df_dashboard['Mes_dt'] = df_dashboard['Saida'].dt.to_period('M').dt.to_timestamp()
    df_dashboard['Dia'] = df_dashboard['Saida'].dt.strftime('%d/%m/%Y')
    df_dashboard['Lucro_int'] = df_dashboard['Lucro'].astype(int)

    meses_traducao = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio',
        6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro',
        10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    df_dashboard['Mes'] = df_dashboard['Mes_dt'].dt.month.map(meses_traducao) + ' ' + df_dashboard['Mes_dt'].dt.year.astype(str)

    lucro_mensal = (
        df_dashboard.groupby(['Mes_dt', 'Mes'])['Lucro_int']
        .sum()
        .reset_index()
        .sort_values('Mes_dt')
    )

    # Gráfico mensal
    fig1 = px.bar(
        lucro_mensal,
        x='Mes',
        y='Lucro_int',
        text='Lucro_int',
        title='Lucro mensal',
        labels={'Lucro_int': 'Lucro (฿)', 'Mes': 'Mês'},
        color_discrete_sequence=['cornflowerblue']
    )
    fig1.update_traces(texttemplate='฿%{text:,}', textposition='outside')
    fig1.update_layout(yaxis_title='Lucro (฿)', xaxis_title='Mês', bargap=0.3)
    st.plotly_chart(fig1, use_container_width=True)

    # Dropdown para gráfico diário
    meses_disponiveis = lucro_mensal['Mes'].tolist()
    mes_selecionado = st.selectbox("📅 Selecione um mês para ver o gráfico diário:", meses_disponiveis)

    if mes_selecionado:
        mes_dt_selecionado = lucro_mensal[lucro_mensal['Mes'] == mes_selecionado]['Mes_dt'].iloc[0]
        df_mes = df_dashboard[df_dashboard['Mes_dt'] == mes_dt_selecionado]

        lucro_diario = (
            df_mes.groupby('Dia')['Lucro_int']
            .sum()
            .reset_index()
            .sort_values('Dia')
        )

        fig2 = px.bar(
            lucro_diario,
            x='Dia',
            y='Lucro_int',
            text='Lucro_int',
            title=f"Lucro diário - {mes_selecionado}",
            labels={'Lucro_int': 'Lucro (฿)', 'Dia': 'Dia'},
            color_discrete_sequence=['mediumseagreen']
        )
        fig2.update_traces(texttemplate='฿%{text:,}', textposition='outside')
        fig2.update_layout(yaxis_title='Lucro (฿)', xaxis_title='Dia', bargap=0.3)
        st.plotly_chart(fig2, use_container_width=True)

    # Tabela de ordens
    st.subheader("📋 Ordens Fechadas")

    def formatar_tabela(df):
        styled_df = (
            df.style
            .format({
                'Margem': '฿ {:,.0f}'.format,
                'Preço de entrada': '$ {:,.1f}'.format,
                'Taxa': '฿ {:,.0f}'.format,
                'Lucro': '฿ {:,.0f}'.format,
                'ROI': '{:.2f}%'.format
            })
            .set_properties(**{
                'text-align': 'center',
                'vertical-align': 'middle'
            })
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center')]},
                {'selector': 'td', 'props': [('text-align', 'center')]}
            ])
        )
        return styled_df

    df_formatado = df[[ 'Entrada', 'entry_margin', 'price', 'Saida', 'Taxa', 'Lucro', 'ROI' ]].rename(columns={
        'entry_margin': 'Margem',
        'price': 'Preço de entrada'
    })

    df_formatado['Margem'] = df_formatado['Margem'].astype(int)
    df_formatado['Taxa'] = df_formatado['Taxa'].astype(int)
    df_formatado['Lucro'] = df_formatado['Lucro'].astype(int)
    df_formatado['ROI'] = df_formatado['ROI'].round(2)

    st.dataframe(formatar_tabela(df_formatado), use_container_width=True)

else:
    st.warning("Nenhuma ordem encontrada ou erro na API.")
