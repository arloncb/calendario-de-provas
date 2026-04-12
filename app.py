import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar

# --- CONFIGURAÇÕES DE ACESSO ---
SENHA_COORD = "coord123"
SENHA_PROF = "prof123"

st.set_page_config(page_title="Calendário Escolar", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try: return conn.read(ttl=0)
    except: return pd.DataFrame()

df = get_data()

st.title("📌 Portal do Calendário de Avaliações")

# --- LOGIN NA BARRA LATERAL ---
st.sidebar.header("🔐 Acesso Restrito")
perfil = st.sidebar.selectbox("Selecione seu Perfil", ["Pai/Aluno", "Coordenação", "Professor"])

acesso_liberado = False
if perfil in ["Coordenação", "Professor"]:
    senha = st.sidebar.text_input("Digite a senha", type="password")
    if perfil == "Coordenação" and senha == SENHA_COORD:
        acesso_liberado = True
    elif perfil == "Professor" and senha == SENHA_PROF:
        acesso_liberado = True
    elif senha != "":
        st.sidebar.error("Senha incorreta!")

# --- ÁREA DA COORDENAÇÃO ---
if perfil == "Coordenação" and acesso_liberado:
    st.header("🛠 Painel da Coordenação")
    
    # 1. AGENDAR PROVA (No Topo agora)
    with st.form("form_coord", clear_on_submit=True):
        st.subheader("📝 Agendar Nova Prova")
        bimestre = st.selectbox("Bimestre", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        col1, col2 = st.columns(2)
        with col1:
            turmas_lista = ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"]
            turma = st.selectbox("Turma", turmas_lista)
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"])
        with col2:
            data_p = st.date_input("Data", format="DD/MM/YYYY")
            # Atualizado: 1ª até a 8ª aula
            aula = st.multiselect("Aulas", [f"{i}ª aula" for i in range(1, 9)])
        
        if st.form_submit_button("Agendar Prova"):
            proximo_id = int(df['ID'].max() + 1) if not df.empty else 1
            nova_linha = pd.DataFrame([{"ID": proximo_id, "Bimestre": bimestre, "Turma": turma, "Disciplina": disciplina, "Data": data_p.strftime("%d-%m-%Y"), "Aula": ", ".join(aula), "Conteudo": "Pendente", "Status": "Pendente"}])
            conn.update(data=pd.concat([df, nova_linha], ignore_index=True))
            st.success("Agendado com sucesso! Limpando campos...")
            st.rerun()

    # 2. VISÃO MENSAL (Abaixo do agendamento)
    st.divider()
    st.subheader("📅 Visão Mensal de Provas")
    calendar_events = []
    if not df.empty:
        for _, row in df.iterrows():
            try:
                d, m, y = row['Data'].split('-')
                calendar_events.append({
                    "title": f"{row['Turma']}: {row['Disciplina']}",
                    "start": f"{y}-{m}-{d}",
                    "end": f"{y}-{m}-{d}",
                    "color": "#3D5AFE" if row['Status'] == 'Concluído' else "#FF9100"
                })
            except: continue
    
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialView": "dayGridMonth",
        "locale": "pt-br",
    }
    calendar(events=calendar_events, options=calendar_options)

# --- ÁREA DO PROFESSOR (OU COORDENAÇÃO) ---
elif (perfil == "Professor" or perfil == "Coordenação") and acesso_liberado:
    st.header("👨‍🏫 Lançamento de Conteúdos")
    pendentes = df[df['Status'] == 'Pendente'] if perfil == "Professor" else df
    
    if pendentes.empty:
        st.info("Nenhuma prova disponível para edição.")
    else:
        dict_provas = {f"{row['Disciplina']} - {row['Turma']} ({row['Data']})": row['ID'] for _, row in pendentes.iterrows()}
        escolha = st.selectbox("Selecione a Prova para preencher:", list(dict_provas.keys()))
        id_sel = dict_provas[escolha]
        
        # O formulário ajuda a limpar os campos após o submit
        with st.form("form_professor", clear_on_submit=True):
            conteudo = st.text_area("Digite o conteúdo da prova:", height=150)
            if st.form_submit_button("Salvar e Publicar"):
                df.loc[df['ID'] == id_sel, 'Conteudo'] = conteudo
                df.loc[df['ID'] == id_sel, 'Status'] = 'Concluído'
                conn.update(data=df)
                st.success("Publicado com sucesso! Campos limpos.")
                st.rerun()

# --- ÁREA DOS PAIS (VISUALIZAÇÃO POR TURMA) ---
elif perfil == "Pai/Aluno":
    st.header("📅 Consulta de Provas")
    if df.empty:
        st.info("Aguardando agendamentos da coordenação.")
    else:
        # Foco principal por Turma
        turmas_existentes = sorted(df['Turma'].unique())
        turma_f = st.selectbox("Escolha a Turma do Aluno:", ["Selecione..."] + list(turmas_existentes))
        
        if turma_f != "Selecione...":
            # Filtro secundário por bimestre
            bim_f = st.radio("Filtrar por Bimestre:", ["Todos", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"], horizontal=True)
            
            exibir = df[df['Turma'] == turma_f]
            if bim_f != "Todos":
                exibir = exibir[exibir['Bimestre'] == bim_f]
            
            st.divider()
            if exibir.empty:
                st.warning(f"Não há provas registradas para o {turma_f} neste período.")
            else:
                for _, row in exibir.iterrows():
                    emoji = "✅" if row['Status'] == 'Concluído' else "⏳"
                    with st.expander(f"{emoji} {row['Data']} - {row['Disciplina']}"):
                        st.write(f"**Bimestre:** {row['Bimestre']}")
                        st.write(f"**Aulas:** {row['Aula']}")
                        st.info(f"**Conteúdo:**\n\n{row['Conteudo']}")
        else:
            st.write("Por favor, selecione a turma acima para visualizar o calendário.")

else:
    st.warning("Selecione seu perfil e digite a senha na lateral para acessar as funções de edição.")
