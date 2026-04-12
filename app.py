import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# Nome do arquivo que servirá como nosso banco de dados simples
DB_FILE = "calendario_provas.csv"

# Função para carregar ou criar o banco de dados
def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["ID", "Turma", "Disciplina", "Data", "Aula", "Conteudo", "Status"])

# Inicialização dos dados
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

st.title("📌 Portal do Calendário de Avaliações")

# --- SISTEMA DE NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Selecione seu Perfil", ["Pai/Aluno", "Coordenação", "Professor"])

# --- ÁREA DA COORDENAÇÃO ---
if menu == "Coordenação":
    st.header("🛠 Painel da Coordenação")
    st.subheader("Agendar Nova Prova")

    with st.form("form_coordenacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            turma = st.selectbox("Turma", ["6º Ano A", "6º Ano B", "7º Ano A", "8º Ano A", "9º Ano A"])
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês"])
        
        with col2:
            data_prova = st.date_input("Data da Prova", datetime.now())
            aula = st.multiselect("Qual(is) aula(s)?", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula"])
        
        submit = st.form_submit_button("Agendar Prova")

    if submit:
        # Criar novo registro
        novo_id = len(st.session_state.dados) + 1
        nova_linha = {
            "ID": novo_id,
            "Turma": turma,
            "Disciplina": disciplina,
            "Data": data_prova.strftime("%d/%m/%Y"),
            "Aula": ", ".join(aula),
            "Conteudo": "Aguardando preenchimento...",
            "Status": "Pendente"
        }
        
        # Salvar nos dados
        st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova_linha])], ignore_index=True)
        st.session_state.dados.to_csv(DB_FILE, index=False)
        st.success(f"Prova de {disciplina} para o {turma} agendada com sucesso!")

    st.divider()
    st.subheader("Provas Agendadas")
    st.dataframe(st.session_state.dados, use_container_width=True)

# --- ÁREA DOS PAIS (VISUALIZAÇÃO) ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    turma_filtro = st.selectbox("Selecione a Turma do Aluno", ["Todas"] + list(st.session_state.dados['Turma'].unique()))
    
    dados_exibicao = st.session_state.dados.copy()
    if turma_filtro != "Todas":
        dados_exibicao = dados_exibicao[dados_exibicao['Turma'] == turma_filtro]
    
    if dados_exibicao.empty:
        st.info("Nenhuma prova agendada para esta turma no momento.")
    else:
        for idx, row in dados_exibicao.iterrows():
            with st.expander(f"{row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                st.write(f"**Aulas:** {row['Aula']}")
                st.write(f"**Conteúdo:** {row['Conteudo']}")
                st.caption(f"Status: {row['Status']}")

# --- ÁREA DO PROFESSOR (ESBOÇO) ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    st.info("Aqui o professor verá as provas da disciplina dele para preencher o conteúdo. (Em desenvolvimento)")
