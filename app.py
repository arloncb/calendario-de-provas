import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# 2. Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(ttl=0)
    except Exception as e:
        st.error("Erro ao carregar dados. Verifique o compartilhamento da planilha.")
        return pd.DataFrame()

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
            turmas_lista = ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"]
            turma = st.selectbox("Turma", turmas_lista)
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"])
        with col2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aula(s)", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        if st.form_submit_button("Agendar Prova"):
            # Garantir que o ID seja numérico e sequencial
            proximo_id = int(df['ID'].max() + 1) if not df.empty and 'ID' in df.columns else 1
            
            nova_linha = pd.DataFrame([{
                "ID": proximo_id, 
                "Bimestre": bimestre, 
                "Turma": turma, 
                "Disciplina": disciplina,
                "Data": data_p.strftime("%d-%m-%Y"), 
                "Aula": ", ".join(aula),
                "Conteudo": "Pendente", 
                "Status": "Pendente"
            }])
            
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("✅ Prova agendada com sucesso!")
            st.rerun()

    st.divider()
    st.subheader("📋 Provas Registradas")
    st.dataframe(df, use_container_width=True)

# --- ÁREA DO PROFESSOR ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    df = get_data()
    
    # Filtrar apenas o que está pendente
    pendentes = df[df['Status'] == 'Pendente']
    
    if pendentes.empty:
        st.info("Não há provas aguardando conteúdo no momento.")
    else:
        # Criamos um dicionário para o Selectbox mostrar um nome bonito mas guardar o ID
        dict_provas = {
            f"{row['Disciplina']} - {row['Turma']} (Dia {row['Data']})": row['ID'] 
            for _, row in pendentes.iterrows()
        }
        
        escolha_texto = st.selectbox("Selecione a Prova para lançar o conteúdo:", list(dict_provas.keys()))
        id_selecionado = dict_provas[escolha_texto]
        
        conteudo = st.text_area("Digite o conteúdo da prova:", height=200, help="Capítulos, páginas, temas...")
        
        if st.button("🚀 Salvar e Publicar para os Pais"):
            if conteudo.strip() == "":
                st.warning("O conteúdo não pode estar vazio.")
            else:
                # Localiza a linha pelo ID e atualiza
                df.loc[df['ID'] == id_selecionado, 'Conteudo'] = conteudo
                df.loc[df['ID'] == id_selecionado, 'Status'] = 'Concluído'
                
                conn.update(data=df)
                st.success("✅ Conteúdo salvo! Os pais já podem visualizar.")
                st.rerun()

# --- ÁREA DOS PAIS ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    df = get_data()
    
    if df.empty:
        st.info("O calendário ainda não possui provas agendadas.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            bim_f = st.selectbox("Filtrar por Bimestre", ["Todos", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        with col_b:
            turmas_existentes = sorted(df['Turma'].unique())
            turma_f = st.selectbox("Filtrar por Turma", ["Todas"] + list(turmas_existentes))
        
        exibir = df.copy()
        if bim_f != "Todos":
            exibir = exibir[exibir['Bimestre'] == bim_f]
        if turma_f != "Todas":
            exibir = exibir[exibir['Turma'] == turma_f]
        
        if exibir.empty:
            st.warning("Nenhuma prova encontrada para este filtro.")
        else:
            # Ordenar por data (opcional, mas ajuda)
            for _, row in exibir.iterrows():
                emoji = "✅" if row['Status'] == 'Concluído' else "⏳"
                with st.expander(f"{emoji} {row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                    st.write(f"**Bimestre:** {row['Bimestre']}")
                    st.write(f"**Horário:** {row['Aula']}")
                    st.markdown("---")
                    st.write("**Conteúdo para estudar:**")
                    st.write(row['Conteudo'])
