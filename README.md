# Dashboard de Ordens - Versão Melhorada

Este é um dashboard para controle de ordens e finanças, com autenticação segura e persistência de dados.

## Funcionalidades

- Autenticação centralizada (senha solicitada apenas uma vez por sessão)
- Persistência de dados com SQLite para controle financeiro
- Dashboard de operações com métricas e gráficos
- Controle financeiro com histórico persistente
- Resumo financeiro com análises gráficas
- Configurações e opção de logout

## Requisitos

```
streamlit
streamlit-aggrid
pandas
plotly
requests
python-dotenv
pytz
sqlite3
```

## Instalação

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Configure as variáveis de ambiente em um arquivo `.env`:
   ```
   SENHA_DASHBOARD=sua_senha_aqui
   API_KEY=sua_api_key
   API_SECRET=seu_api_secret
   PASSPHRASE=seu_passphrase
   ```

## Execução

```
streamlit run app.py
```

## Estrutura do Projeto

- `app.py`: Página principal do dashboard
- `utils.py`: Funções utilitárias e de banco de dados
- `pages/`: Páginas adicionais do dashboard
  - `1_Controle.py`: Controle financeiro
  - `2_Resumo.py`: Resumo financeiro
  - `3_Configuracoes.py`: Configurações e logout
- `dashboard.db`: Banco de dados SQLite (criado automaticamente)
