import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# 2. Conexão com o Google Sheets (Ele vai ler o link do Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados sempre atualizados
def get_data():
    try:
        # ttl=0 evita que o Streamlit use dados antigos guardados no cache
        return conn.read(ttl=0)
    except Exception as e:
        st.error("Erro ao conectar com a planilha. Verifique os Secrets.")
        return pd.DataFrame()

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
            turmas_lista = ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"]
            turma = st.selectbox("Turma", turmas_lista)
            
            disciplinas_lista = ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"]
            disciplina = st.selectbox("Disciplina", disciplinas_lista)
        with col2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aula(s)", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        if st.form_submit_button("Agendar Prova"):
            if not aula:
                st.warning("Por favor, selecione ao menos uma aula.")
            else:
                # Gerar ID novo
                novo_id = int(df['ID'].max() + 1) if not df.empty and 'ID' in df.columns else 1
                
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
                # Salva na planilha usando a conexão oficial
                conn.update(data=df_atualizado)
                st.success(f"Prova de {disciplina} agendada!")
                st.rerun()

    st.divider()
    st.subheader("Visualização da Planilha")
    st.dataframe(df, use_container_width=True)

# --- ÁREA DO PROFESSOR ---
elif menu == "Professor":
    st.header("👨‍🏫 Espaço do Professor")
    df = get_data()
    
    if df.empty or 'Status' not in df.columns or len(df[df['Status'] == 'Pendente']) == 0:
        st.info("Não há provas pendentes de conteúdo.")
    else:
        provas_pendentes = df[df['Status'] == 'Pendente']
        
        # Criar uma lista amigável para o professor escolher a prova
        opcoes_provas = provas_pendentes.apply(
            lambda r: f"ID:{r['ID']} | {r['Disciplina']} - {r['Turma']} ({r['Data']})", axis=1
        ).tolist()
        
        escolha = st.selectbox("Selecione a Prova para preencher o conteúdo", opcoes_provas)
        id_selecionado = int(escolha.split('|')[0].replace('ID:', '').strip())
        
        conteudo = st.text_area("Digite o conteúdo da prova:", placeholder="Ex: Capítulos 1 a 3 do livro didático...")
        
        if st.button("Salvar Conteúdo"):
            if conteudo:
                # Localiza e atualiza a linha
                df.loc[df['ID'] == id_selecionado, 'Conteudo'] = conteudo
                df.loc[df['ID'] == id_selecionado, 'Status'] = 'Concluído'
                conn.update(data=df)
                st.success("Conteúdo salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, digite o conteúdo antes de salvar.")

# --- ÁREA DOS PAIS ---
elif menu == "Pai/Aluno":
    st.header("📅 Calendário de Provas")
    df = get_data()
    
    if df.empty:
        st.info("Nenhuma prova agendada ainda.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            bim_f = st.selectbox("Bimestre", ["Todos", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        with col_f2:
            turma_f = st.selectbox("Sua Turma", ["Todas"] + sorted(list(df['Turma'].unique())))
        
        exibir = df.copy()
        if bim_f != "Todos":
            exibir = exibir[exibir['Bimestre'] == bim_f]
        if turma_f != "Todas":
            exibir = exibir[exibir['Turma'] == turma_f]
        
        if exibir.empty:
            st.warning("Nenhuma prova encontrada para os filtros selecionados.")
        else:
            for _, row in exibir.iterrows():
                cor_status = "🔵" if row['Status'] == 'Concluído' else "🟠"
                with st.expander(f"{cor_status} {row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                    st.write(f"**Bimestre:** {row['Bimestre']}")
                    st.write(f"**Aulas:** {row['Aula']}")
                    st.info(f"**Conteúdo para estudar:**\n\n{row['Conteudo']}")
