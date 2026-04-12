import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar

# --- CONFIGURAÇÕES DE ACESSO (Mude aqui se quiser) ---
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
    
    # --- NOVO: CALENDÁRIO VISUAL ---
    st.subheader("📅 Visão Mensal de Provas")
    calendar_events = []
    if not df.empty:
        for _, row in df.iterrows():
            # Converter data dd-mm-yyyy para yyyy-mm-dd para o calendário
            d, m, y = row['Data'].split('-')
            calendar_events.append({
                "title": f"{row['Turma']}: {row['Disciplina']}",
                "start": f"{y}-{m}-{d}",
                "end": f"{y}-{m}-{d}",
                "color": "#3D5AFE" if row['Status'] == 'Concluído' else "#FF9100"
            })
    
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialView": "dayGridMonth",
        "locale": "pt-br",
    }
    calendar(events=calendar_events, options=calendar_options)

    # --- FORMULÁRIO DE AGENDAMENTO ---
    st.divider()
    with st.form("form_coord", clear_on_submit=True):
        st.subheader("📝 Agendar Nova Prova")
        bimestre = st.selectbox("Bimestre", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
        col1, col2 = st.columns(2)
        with col1:
            turma = st.selectbox("Turma", ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"])
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia"])
        with col2:
            data_p = st.date_input("Data", format="DD/MM/YYYY")
            aula = st.multiselect("Aulas", ["1ª aula", "2ª aula", "3ª aula", "4ª aula", "5ª aula", "6ª aula"])
        
        if st.form_submit_button("Agendar Prova"):
            proximo_id = int(df['ID'].max() + 1) if not df.empty else 1
            nova_linha = pd.DataFrame([{"ID": proximo_id, "Bimestre": bimestre, "Turma": turma, "Disciplina": disciplina, "Data": data_p.strftime("%d-%m-%Y"), "Aula": ", ".join(aula), "Conteudo": "Pendente", "Status": "Pendente"}])
            conn.update(data=pd.concat([df, nova_linha], ignore_index=True))
            st.success("Agendado!")
            st.rerun()

# --- ÁREA DO PROFESSOR (OU COORDENAÇÃO EDITANDO) ---
elif (perfil == "Professor" or perfil == "Coordenação") and acesso_liberado:
    st.header("👨‍🏫 Lançamento de Conteúdos")
    pendentes = df[df['Status'] == 'Pendente'] if perfil == "Professor" else df
    
    if pendentes.empty:
        st.info("Nenhuma prova disponível para edição.")
    else:
        dict_provas = {f"{row['Disciplina']} - {row['Turma']} ({row['Data']})": row['ID'] for _, row in pendentes.iterrows()}
        escolha = st.selectbox("Selecione a Prova:", list(dict_provas.keys()))
        id_sel = dict_provas[escolha]
        conteudo = st.text_area("Conteúdo da prova:", height=150)
        
        if st.button("Salvar Conteúdo"):
            df.loc[df['ID'] == id_sel, 'Conteudo'] = conteudo
            df.loc[df['ID'] == id_sel, 'Status'] = 'Concluído'
            conn.update(data=df)
            st.success("Publicado!")
            st.rerun()

# --- ÁREA DOS PAIS (VISUALIZAÇÃO LIVRE) ---
elif perfil == "Pai/Aluno":
    st.header("📅 Consulta de Provas")
    if df.empty:
        st.info("Aguardando agendamentos.")
    else:
        turma_f = st.selectbox("Selecione a Turma", ["Todas"] + sorted(list(df['Turma'].unique())))
        exibir = df[df['Turma'] == turma_f] if turma_f != "Todas" else df
        for _, row in exibir.iterrows():
            emoji = "✅" if row['Status'] == 'Concluído' else "⏳"
            with st.expander(f"{emoji} {row['Data']} - {row['Disciplina']} ({row['Turma']})"):
                st.write(f"**Bimestre:** {row['Bimestre']} | **Aulas:** {row['Aula']}")
                st.info(f"Conteúdo: {row['Conteudo']}")

else:
    st.warning("Por favor, selecione seu perfil e digite a senha na barra lateral para acessar.")
