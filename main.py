# Importar as bibliotecas
import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Login
def authenticate_user(username, password):
    return username == "admin" and password == "admin"

# Criar as funções de carregamento de dados
@st.cache_data
def carregar_dados(empresa):
    dados_acao = yf.Ticker(empresa)
    cotacoes_acao = dados_acao.history(period="1d", start="2010-01-01", end="2024-07-01")
    cotacoes_acao = cotacoes_acao[["Close"]]
    return cotacoes_acao

# Função para buscar dados no Jira
@st.cache_data
def buscar_jira(jira_url, email, api_token, jql, max_results=100):
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(
        f"{jira_url}/rest/api/2/search",
        headers=headers,
        auth=HTTPBasicAuth(email, api_token),
        params={
            "jql": jql,
            "maxResults": max_results
        }
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Erro ao conectar ao Jira: " + response.text)
        return None

# Função para buscar todas as issues, lidando com paginação
def buscar_todas_issues(jira_url, email, api_token, jql):
    issues = []
    start_at = 0
    max_results = 100  # Pode-se definir até 1000, mas 100 é um bom limite para cada chamada
    while True:
        response = buscar_jira(jira_url, email, api_token, jql, max_results=max_results)
        if response and 'issues' in response:
            issues.extend(response['issues'])
            start_at += len(response['issues'])
            if start_at >= response['total']:  # Se alcançou o total de issues, sai do loop
                break
        else:
            break
    return issues

# Interface de login
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login")
    
    # Adicionando a imagem do logo centralizada
    st.markdown(
        f"""
        <style>
        .logo-container {{
            display: flex;
            justify-content: center;
        }}
        </style>
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s" width="150" height="150">
        </div>
        """, 
        unsafe_allow_html=True
    )

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.success("Login bem-sucedido!")
            
            # A conexão com o Jira após o login
            st.session_state.jira_url = "https://carboncars.atlassian.net"
            st.session_state.email = "henrique.degan@oatsolutions.com.br"
            st.session_state.api_token = "b4mAs0sXJCx3101YvgkhBD3F"

            # Filtragem por data de criação
            st.header("Filtrar por Data de Criação")
            data_inicial = st.date_input("Data Inicial", datetime.today())
            data_final = st.date_input("Data Final", datetime.today())

            if st.button("Pesquisar"):
                jql = f'created >= "{data_inicial}" AND created <= "{data_final}" AND project IN (AP, PB) AND type IN ("Produção Blindados", "Produção Blindados - QA", Recebimento) ORDER BY created DESC'
                issues = buscar_todas_issues(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
                total_issues = len(issues)
                st.write(f"Total de issues encontradas: {total_issues}")

                # Criar a tabela
                dados_tabela = []
                for issue in issues:
                    dados_tabela.append({
                        "KEY": issue['key'],
                        "SUMMARY": issue['fields']['summary'],
                        "Veículo Marca/Modelo": issue['fields'].get('customfield_11298', 'Não disponível')  # Substituir 'customfield_XXXXX' pelo campo correto
                    })

                # Criar um DataFrame do Pandas
                df = pd.DataFrame(dados_tabela)

                # Remover duplicados, mantendo o último caso baseado no campo 'SUMMARY'
                df = df.drop_duplicates(subset='SUMMARY', keep='last')

                # Exibir a tabela no Streamlit
                st.dataframe(df)

        else:
            st.error("Nome de usuário ou senha incorretos.")
else:
    # Exibir botão de deslogar no canto superior direito
    if st.button("Deslogar"):
        st.session_state.authenticated = False
        st.success("Deslogado com sucesso!")

    # Filtragem por data de criação
    st.header("Filtrar por Data de Criação")
    data_inicial = st.date_input("Data Inicial", datetime.today())
    data_final = st.date_input("Data Final", datetime.today())

    if st.button("Pesquisar"):
        jql = f'created >= "{data_inicial}" AND created <= "{data_final}" AND project IN (AP, PB) AND type IN ("Produção Blindados", "Produção Blindados - QA", Recebimento) ORDER BY created DESC'
        issues = buscar_todas_issues(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
        total_issues = len(issues)
        st.write(f"Total de issues encontradas: {total_issues}")

        # Criar a tabela
        dados_tabela = []
        for issue in issues:
            dados_tabela.append({
                "KEY": issue['key'],
                "SUMMARY": issue['fields']['summary'],
                "Veículo Marca/Modelo": issue['fields'].get('customfield_11298', 'Não disponível')  # Substituir 'customfield_XXXXX' pelo campo correto
            })

        # Criar um DataFrame do Pandas
        df = pd.DataFrame(dados_tabela)

        # Remover duplicados, mantendo o último caso baseado no campo 'SUMMARY'
        df = df.drop_duplicates(subset='SUMMARY', keep='last')

        # Exibir a tabela no Streamlit
        st.dataframe(df, use_container_width=True)