import streamlit as st
import pandas as pd
import plotly.express as px
from utils import (
    check_authentication, 
    format_btc
)

# Configuração da página
st.set_page_config(page_title="Configurações", layout="wide")

# Verificar autenticação
if not check_authentication():
    st.warning("Você precisa fazer login para acessar esta página.")
    st.stop()

st.title("⚙️ Configurações")

# Opção para logout
if st.button("🔒 Fazer Logout"):
    # Limpar o estado de autenticação
    st.session_state.authenticated = False
    st.success("Logout realizado com sucesso!")
    st.info("Redirecionando para a página de login...")
    st.experimental_rerun()

# Informações sobre o dashboard
st.subheader("📋 Sobre o Dashboard")
st.markdown("""
Este dashboard foi desenvolvido para ajudar no controle financeiro e acompanhamento de operações.

**Funcionalidades principais:**
- Autenticação segura com senha única por sessão
- Dashboard de operações com métricas e gráficos
- Controle financeiro com persistência de dados
- Resumo financeiro com análises gráficas
- Exportação de dados para CSV

**Versão:** 2.0
""")

# Explicação sobre a persistência de dados
st.subheader("💾 Persistência de Dados")
st.markdown("""
Todas as transações financeiras são armazenadas em um banco de dados SQLite local.
Isso garante que seus dados não sejam perdidos ao fechar ou reiniciar a aplicação.

O arquivo do banco de dados (`dashboard.db`) é criado automaticamente na primeira execução
e armazena todo o histórico de depósitos e saques.
""")

# Dicas de uso
st.subheader("💡 Dicas de Uso")
st.markdown("""
1. **Navegação:** Use a barra lateral para navegar entre as diferentes páginas do dashboard.
2. **Controle Financeiro:** Registre todos os depósitos e saques para manter seu saldo atualizado.
3. **Dashboard Principal:** Atualize os dados regularmente para obter informações atualizadas sobre suas operações.
4. **Resumo Financeiro:** Consulte os gráficos para análises detalhadas do seu fluxo financeiro.
5. **Segurança:** Faça logout ao terminar de usar o dashboard em dispositivos compartilhados.
""")

# Contato e suporte
st.subheader("📞 Contato e Suporte")
st.markdown("""
Para suporte ou sugestões de melhorias, entre em contato através dos canais disponíveis.

**Lembre-se:** Mantenha sua senha segura e não a compartilhe com terceiros.
""")
