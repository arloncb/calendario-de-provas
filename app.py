import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

# --- CONFIGURAÇÕES DE IDENTIDADE E ACESSO ---
URL_LOGO = "Logo vermelho.png"
ID_PASTA_DRIVE = "1-87YcfvIWdBm-c6YyZcfBT_Ms-aX-SKt"
SENHA_COORD = "coord123"
SENHA_PROF = "prof123"

# Listas Oficiais Padronizadas
LISTA_DISCIPLINAS = [
    "Arte", "Biologia", "Ciências", "Ciências da Natureza na Cont.", 
    "Ciências Humanas e Sociedade", "Ed. Física", "Filosofia", "Física", 
    "Geografia", "História", "Leitura e Produção de texto",
    "Letramento e raciocínio Matemático", "Língua Inglesa", 
    "Língua Portuguesa", "Literatura Arte Movimento", "Matemática", 
    "Química", "Sociologia", "Tecnologia e Cidadania Digital"
]

LISTA_TURMAS = [
    "4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", 
    "9° A", "9° B", "9° C", "9° D", "1° A", "1° B", "2° A", "3° A"
]

st.set_page_config(page_title="Calendário Escolar", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_lido = conn.read(ttl=0)
        df_lido = df_lido.fillna('')
        for col in ['Conteudo', 'Status', 'Link_Arquivo']:
            if col in df_lido.columns:
                df_lido[col] = df_lido[col].astype(str)
        return df_lido
    except:
        return pd.DataFrame()

def upload_to_drive(file, filename):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': filename, 'parents': [ID_PASTA_DRIVE]}
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='application/pdf', resumable=True)
        file_drive = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        return file_drive.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

df = get_data()

# --- CABEÇALHO ---
col_logo, col_tit = st.columns([1, 6])
with col_logo:
    try:
        st.image(URL_LOGO, width=120)
    except:
        st.warning("Logo não encontrado")
with col_tit:
    st.title("Portal do Calendário de Avaliações")
    st.write("Sistema Integrado de Gestão Pedagógica")

# --- BARRA LATERAL ---
st.sidebar.header("🔐 Acesso Restrito")
perfil = st.sidebar.selectbox("Selecione seu Perfil", ["Pai/Aluno", "Coordenação", "Professor"])

acesso_liberado = False
if perfil in ["Coordenação", "Professor"]:
    senha = st.sidebar.text_input("Digite a senha", type="password")
    if (perfil == "Coordenação" and senha == SENHA_COORD) or (perfil == "Professor" and senha == SENHA_PROF):
        acesso_liberado = True
    elif senha != "":
        st.sidebar.error("Senha incorreta!")

# --- ÁREA DA COORDENAÇÃO ---
if perfil == "Coordenação" and acesso_liberado:
    st.header("🛠 Painel da Coordenação")
    
    with st.form("form_coord", clear_on_submit=True):
        st.subheader("📝 Agendar Nova Prova")
        c1, c2 = st.columns(2)
        with c1:
            bimestre = st.selectbox("Bimestre", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            turma = st.selectbox("Turma", LISTA_TURMAS)
            disciplina = st.selectbox("Disciplina", LISTA_DISCIPLINAS)
        with c2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aulas (1ª a 8ª)", [f"{i}ª aula" for i in range(1, 9)])
            
            eh_fim_de_semana = data_p.weekday() >= 5
            if eh_fim_de_semana:
                st.error("❌ Sábados e Domingos não são permitidos.")

        if st.form_submit_button("Agendar Prova"):
            if eh_fim_de_semana:
                st.error("Selecione um dia útil.")
            elif not aula:
                st.error("Selecione pelo menos uma aula.")
            else:
                prox_id = int(pd.to_numeric(df['ID'], errors='coerce').max() + 1) if not df.empty and 'ID' in df.columns else 1
                nova = pd.DataFrame([{
                    "ID": prox_id, "Bimestre": bimestre, "Turma": turma, "Disciplina": disciplina,
                    "Data": data_p.strftime("%d-%m-%Y"), "Aula": ", ".join(aula),
                    "Conteudo": "Pendente", "Status": "Pendente", "Link_Arquivo": ""
                }])
                conn.update(data=pd.concat([df, nova], ignore_index=True))
                st.success("✅ Prova agendada!")
                st.rerun()

    st.divider()
    st.subheader("📂 Provas para Análise (Downloads)")
    if not df.empty and "Link_Arquivo" in df.columns:
        arquivos = df[(df['Link_Arquivo'] != "") & (df['Link_Arquivo'] != "nan")]
        if not arquivos.empty:
            for _, row in arquivos.iterrows():
                st.write(f"📄 **{row['Disciplina']} ({row['Turma']})**: [Baixar PDF]({row['Link_Arquivo']})")
        else:
            st.info("Aguardando envios dos professores.")

    st.divider()
    st.subheader("📅 Gestão Visual das Avaliações")
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        turmas_filtradas = st.multiselect(
            "Filtrar por Turma (Deixe vazio para ver todas)", 
            options=LISTA_TURMAS,
            help="Selecione turmas específicas para limpar o visual do calendário."
        )
    with col_f2:
        modo_visao = st.radio("Modo de Exibição", ["Calendário", "Lista (Agenda)"], horizontal=True)

    events = []
    if not df.empty:
        df_view = df.copy()
        if turmas_filtradas:
            df_view = df_view[df_view['Turma'].isin(turmas_filtradas)]

        for _, r in df_view.iterrows():
            try:
                data_str = str(r['Data']).replace('/', '-')
                if '-' in data_str:
                    partes = data_str.split('-')
                    if len(partes) == 3:
                        d, m, y = partes
                        if len(y) == 2: y = f"20{y}"
                        cor_evento = "#3D5AFE" if r['Status'] == 'Concluído' else "#FF9100"
                        events.append({
                            "title": f"[{r['Turma']}] {r['Disciplina']}", 
                            "start": f"{y}-{m}-{d}", 
                            "end": f"{y}-{m}-{d}", 
                            "color": cor_evento,
                            "allDay": True
                        })
            except: 
                continue
    
    visao_inicial = "dayGridMonth" if modo_visao == "Calendário" else "listMonth"

    calendar(events=events, options={
        "locale": "pt-br",
        "initialView": visao_inicial,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
        "buttonText": {"today": "Hoje", "month": "Mês", "list": "Agenda"},
        "editable": False,
        "navLinks": True
    })

# --- ÁREA DO PROFESSOR ---
elif perfil == "Professor" and acesso_liberado:
    st.header("👨‍🏫 Lançamento de Conteúdos")
    if not df.empty:
        disc_p = st.selectbox("1. Sua Disciplina", ["Selecione..."] + LISTA_DISCIPLINAS)
        if disc_p != "Selecione...":
            pends = df[(df['Disciplina'] == disc_p) & (df['Status'] == 'Pendente')]
            if pends.empty:
                st.info(f"Não há pendências para {disc_p}.")
            else:
                opts = {f"{row['Turma']} (Dia {row['Data']})": row['ID'] for _, row in pends.iterrows()}
                id_sel = opts[st.selectbox("2. Selecione a Turma", list(opts.keys()))]
                
                with st.form("f_prof", clear_on_submit=True):
                    cont = st.text_area("3. Conteúdo Programático")
                    arq = st.file_uploader("4. Anexar Prova em PDF", type=["pdf"])
                    if st.form_submit_button("Salvar e Enviar"):
                        if cont and arq:
                            url = upload_to_drive(arq, f"Prova_{disc_p}_{id_sel}.pdf")
                            if url:
                                idx = df[df['ID'] == id_sel].index
                                df.at[idx[0], 'Conteudo'] = str(cont)
                                df.at[idx[0], 'Status'] = 'Concluído'
                                df.at[idx[0], 'Link_Arquivo'] = str(url)
                                conn.update(data=df)
                                st.success("✅ Publicado com sucesso!")
                                st.rerun()
                        else:
                            st.error("Preencha o conteúdo e anexe o arquivo.")

# --- ÁREA DOS PAIS/ALUNOS ---
elif perfil == "Pai/Aluno":
    st.header("📅 Consulta de Provas")
    if not df.empty:
        turmas_existentes = sorted([t for t in df['Turma'].unique() if t])
        t_f = st.selectbox("Escolha a Turma do Aluno:", ["Selecione..."] + turmas_existentes)
        if t_f != "Selecione...":
            exibir = df[df['Turma'] == t_f]
            if exibir.empty:
                st.warning("Nenhuma avaliação encontrada.")
            else:
                for _, r in exibir.iterrows():
                    status_icon = "✅" if r['Status'] == 'Concluído' else "⏳"
                    with st.expander(f"{status_icon} {r['Data']} - {r['Disciplina']}"):
                        st.write(f"**Bimestre:** {r['Bimestre']}")
                        st.write(f"**Aula(s):** {r['Aula']}")
                        st.info(f"**Conteúdo para Estudar:**\n\n{r['Conteudo']}")
        else:
            st.write("Selecione uma turma para visualizar o calendário.")
else:
    if perfil != "Pai/Aluno":
        st.warning("⚠️ Selecione o perfil e insira a senha na barra lateral.")
