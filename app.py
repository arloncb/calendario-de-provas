import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados da planilha
def get_data():
    return conn.read(ttl="0")

st.title("📌 Portal do Calendário de Avaliações")

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Selecione seu Perfil", ["Pai/Aluno", "Coordenação", "Professor"])

# --- ÁREA DA COORDENAÇÃO ---
if menu == "Coordenação":
    st.header("🛠 Painel da Coordenação")
    df = get_data()
    
    with st.form("form_coord", clear_on_submit=True):
        bimestre = st.selectbox("Referência", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        col1, col2 = st.columns(2)
        with col1:
            turma = st.selectbox("Turma", ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"])
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia"])
        with col2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aula(s)", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        if st.form_submit_button("Agendar Prova"):
            nova_linha = pd.DataFrame([{
                "ID": len(df) + 1, "Bimestre": bimestre, "Turma": turma, "Disciplina": disciplina,
                "Data": data_p.strftime("%d-%m-%Y"), "Aula": ", ".join(aula),
                "Conteudo": "Aguardando Professor...", "Status": "Pendente"
            }])
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("Prova agendada!")
            st.rerun()

# --- ÁREA DO PROFESSOR ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    df = get_data()
    
    # Filtro para o professor achar a prova
    prova_selecionada = st.selectbox("Selecione a Prova para preencher o conteúdo", 
                                    df[df['Status'] == 'Pendente']['ID'].tolist(),
                                    format_func=lambda x: f"{df[df['ID']==x]['Disciplina'].values[0]} - {df[df['ID']==x]['Turma'].values[0]} ({df[df['ID']==x]['Data'].values[0]})")
    
    if prova_selecionada:
        conteudo = st.text_area("Digite o conteúdo da prova (Capítulos, temas, etc):")
        if st.button("Salvar Conteúdo"):
            df.loc[df['ID'] == prova_selecionada, 'Conteudo'] = conteudo
            df.loc[df['ID'] == prova_selecionada, 'Status'] = 'Concluído'
            conn.update(data=df)
            st.success("Conteúdo salvo com sucesso!")
            st.rerun()

# --- ÁREA DOS PAIS ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    df = get_data()
    turma_f = st.selectbox("Turma", ["Todas"] + list(df['Turma'].unique()))
    
    exibir = df[df['Turma'] == turma_f] if turma_f != "Todas" else df
    for _, row in exibir.iterrows():
        with st.expander(f"{row['Data']} - {row['Disciplina']} ({row['Turma']})"):
            st.write(f"**Conteúdo:** {row['Conteudo']}")
            st.caption(f"Status: {row['Status']}")
