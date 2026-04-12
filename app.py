import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

DB_FILE = "calendario_provas.csv"

# Função para carregar ou criar o banco de dados (agora com a coluna Bimestre)
def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["ID", "Bimestre", "Turma", "Disciplina", "Data", "Aula", "Conteudo", "Status"])

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
        # 1. NOVO: Seleção do Bimestre antes de tudo
        bimestre = st.selectbox("Referência", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 2. ATUALIZADO: Lista completa de turmas
            turmas_lista = ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"]
            turma = st.selectbox("Turma", turmas_lista)
            
            disciplinas_lista = ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"]
            disciplina = st.selectbox("Disciplina", disciplinas_lista)
        
        with col2:
            # 3. ATUALIZADO: Formato da data na tela (DD/MM/YYYY)
            data_prova = st.date_input("Data da Prova", datetime.now(), format="DD/MM/YYYY")
            aula = st.multiselect("Qual(is) aula(s)?", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        submit = st.form_submit_button("Agendar Prova")

    if submit:
        novo_id = len(st.session_state.dados) + 1
        nova_linha = {
            "ID": novo_id,
            "Bimestre": bimestre,
            "Turma": turma,
            "Disciplina": disciplina,
            # 3. ATUALIZADO: Salvando no formato dia-mês-ano com traços
            "Data": data_prova.strftime("%d-%m-%Y"),
            "Aula": ", ".join(aula),
            "Conteudo": "Aguardando preenchimento...",
            "Status": "Pendente"
        }
        
        # Salvar nos dados
        st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova_linha])], ignore_index=True)
        st.session_state.dados.to_csv(DB_FILE, index=False)
        st.success(f"Prova de {disciplina} para o {turma} ({bimestre}) agendada com sucesso!")

    st.divider()
    st.subheader("Provas Agendadas")
    st.dataframe(st.session_state.dados, use_container_width=True)

# --- ÁREA DOS PAIS (VISUALIZAÇÃO) ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    
    # Filtros para os pais acharem a prova mais fácil
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        bimestre_filtro = st.selectbox("Selecione o Bimestre", ["Todos", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
    with col_filtro2:
        turma_filtro = st.selectbox("Selecione a Turma do Aluno", ["Todas"] + ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"])
    
    dados_exibicao = st.session_state.dados.copy()
    
    # Aplicando os filtros
    if bimestre_filtro != "Todos":
        dados_exibicao = dados_exibicao[dados_exibicao['Bimestre'] == bimestre_filtro]
    if turma_filtro != "Todas":
        dados_exibicao = dados_exibicao[dados_exibicao['Turma'] == turma_filtro]
    
    if dados_exibicao.empty:
        st.info("Nenhuma prova agendada com estes filtros no momento.")
    else:
        for idx, row in dados_exibicao.iterrows():
            with st.expander(f"{row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                st.write(f"**Bimestre:** {row['Bimestre']}")
                st.write(f"**Aulas:** {row['Aula']}")
                st.write(f"**Conteúdo:** {row['Conteudo']}")
                st.caption(f"Status: {row['Status']}")

# --- ÁREA DO PROFESSOR (ESBOÇO) ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    st.info("Aqui o professor verá as provas da disciplina dele para preencher o conteúdo. (Em desenvolvimento)")
