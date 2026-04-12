import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# O link exato da sua planilha
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1gPhMASo7yOsn5HhvLw6_rGkYbSkcBB_xUsgN8QgzhWw/edit?gid=0#gid=0"

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados da planilha
def get_data():
    return conn.read(spreadsheet=URL_PLANILHA, ttl="0")

st.title("📌 Portal do Calendário de Avaliações")

# --- NAVEGAÇÃO LATERAL ---
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
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"])
        with col2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aula(s)", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        if st.form_submit_button("Agendar Prova"):
            # Lógica para garantir que o ID siga uma sequência correta
            novo_id = len(df) + 1 if not df.empty else 1
            
            nova_linha = pd.DataFrame([{
                "ID": novo_id, 
                "Bimestre": bimestre, 
                "Turma": turma, 
                "Disciplina": disciplina,
                "Data": data_p.strftime("%d-%m-%Y"), 
                "Aula": ", ".join(aula),
                "Conteudo": "Aguardando Professor...", 
                "Status": "Pendente"
            }])
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            # Envia a atualização de volta para o link da planilha
            conn.update(data=df_atualizado, spreadsheet=URL_PLANILHA)
            st.success("Prova agendada com sucesso!")
            st.rerun()

# --- ÁREA DO PROFESSOR ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    df = get_data()
    
    # Verifica se a planilha está vazia ou se não há provas pendentes
    if df.empty or 'Status' not in df.columns or len(df[df['Status'] == 'Pendente']) == 0:
        st.info("Não há provas pendentes de preenchimento de conteúdo no momento.")
    else:
        # Filtro para o professor achar apenas as provas que estão sem conteúdo
        provas_pendentes = df[df['Status'] == 'Pendente']['ID'].tolist()
        prova_selecionada = st.selectbox(
            "Selecione a Prova para preencher o conteúdo", 
            provas_pendentes,
            format_func=lambda x: f"{df[df['ID']==x]['Disciplina'].values[0]} - {df[df['ID']==x]['Turma'].values[0]} ({df[df['ID']==x]['Data'].values[0]})"
        )
        
        if prova_selecionada:
            conteudo = st.text_area("Digite o conteúdo da prova (Capítulos, temas, links, etc):")
            if st.button("Salvar Conteúdo"):
                # Atualiza a linha específica na planilha
                df.loc[df['ID'] == prova_selecionada, 'Conteudo'] = conteudo
                df.loc[df['ID'] == prova_selecionada, 'Status'] = 'Concluído'
                conn.update(data=df, spreadsheet=URL_PLANILHA)
                st.success("Conteúdo salvo com sucesso!")
                st.rerun()

# --- ÁREA DOS PAIS ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    df = get_data()
    
    if df.empty:
        st.info("O calendário ainda está vazio. Aguarde a coordenação agendar as provas.")
    else:
        # Filtro para os pais não se perderem com tantas turmas
        turma_f = st.selectbox("Selecione a Turma do seu filho", ["Todas"] + list(df['Turma'].dropna().unique()))
        
        exibir = df[df['Turma'] == turma_f] if turma_f != "Todas" else df
        
        if exibir.empty:
            st.info("Nenhuma prova agendada para esta turma no momento.")
        else:
            for _, row in exibir.iterrows():
                with st.expander(f"{row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                    st.write(f"**Bimestre:** {row['Bimestre']}")
                    st.write(f"**Aulas:** {row['Aula']}")
                    st.write(f"**Conteúdo:** {row['Conteudo']}")
                    st.caption(f"Status: {row['Status']}")
