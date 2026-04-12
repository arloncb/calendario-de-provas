import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

# --- CONFIGURAÇÕES ---
ID_PASTA_DRIVE = "1-87YcfvIWdBm-c6YyZcfBT_Ms-aX-SKt"
SENHA_COORD = "coord123"
SENHA_PROF = "prof123"

st.set_page_config(page_title="Calendário Escolar", layout="wide")

# Conexão com a Planilha
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(ttl=0)
    except:
        return pd.DataFrame()

# Função de Upload (Otimizada para Drive Institucional)
def upload_to_drive(file, filename):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [ID_PASTA_DRIVE]
        }
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='application/pdf', resumable=True)
        
        file_drive = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True # Necessário para drives institucionais
        ).execute()
        
        return file_drive.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive da Escola: {e}")
        return None

df = get_data()

st.title("📌 Portal do Calendário de Avaliações")

# --- NAVEGAÇÃO E LOGIN ---
st.sidebar.header("🔐 Acesso")
perfil = st.sidebar.selectbox("Perfil", ["Pai/Aluno", "Coordenação", "Professor"])

acesso_liberado = False
if perfil in ["Coordenação", "Professor"]:
    senha = st.sidebar.text_input("Senha", type="password")
    if (perfil == "Coordenação" and senha == SENHA_COORD) or (perfil == "Professor" and senha == SENHA_PROF):
        acesso_liberado = True
    elif senha != "":
        st.sidebar.error("Senha incorreta")

# --- ÁREA DA COORDENAÇÃO ---
if perfil == "Coordenação" and acesso_liberado:
    st.header("🛠 Painel da Coordenação")
    
    with st.form("form_coord", clear_on_submit=True):
        st.subheader("📝 Agendar Nova Prova")
        col1, col2 = st.columns(2)
        with col1:
            bimestre = st.selectbox("Bimestre", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            turma = st.selectbox("Turma", ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"])
            disciplina = st.selectbox("Disciplina", ["Matemática", "Português", "História", "Geografia", "Ciências", "Inglês", "Física", "Química", "Biologia", "Sociologia", "Filosofia", "Ed. Física", "Artes"])
        with col2:
            data_p = st.date_input("Data", format="DD/MM/YYYY")
            aula = st.multiselect("Aulas", [f"{i}ª aula" for i in range(1, 9)])
        
        if st.form_submit_button("Agendar Prova"):
            prox_id = int(df['ID'].max() + 1) if not df.empty and 'ID' in df.columns else 1
            nova_linha = pd.DataFrame([{
                "ID": prox_id, "Bimestre": bimestre, "Turma": turma, "Disciplina": disciplina,
                "Data": data_p.strftime("%d-%m-%Y"), "Aula": ", ".join(aula),
                "Conteudo": "Pendente", "Status": "Pendente", "Link_Arquivo": ""
            }])
            conn.update(data=pd.concat([df, nova_linha], ignore_index=True))
            st.success("Agendado com sucesso!")
            st.rerun()

    st.divider()
    st.subheader("📂 Provas para Análise (Downloads)")
    if not df.empty and "Link_Arquivo" in df.columns:
        arquivos = df[df['Link_Arquivo'] != ""]
        if not arquivos.empty:
            for _, row in arquivos.iterrows():
                st.write(f"📄 **{row['Disciplina']} ({row['Turma']})**: [Baixar PDF da Prova]({row['Link_Arquivo']})")
        else:
            st.info("Nenhuma prova enviada pelos professores ainda.")

    st.divider()
    st.subheader("📅 Visão Mensal")
    events = []
    if not df.empty:
        for _, r in df.iterrows():
            try:
                d, m, y = r['Data'].split('-')
                events.append({
                    "title": f"{r['Turma']}: {r['Disciplina']}", 
                    "start": f"{y}-{m}-{d}", "end": f"{y}-{m}-{d}", 
                    "color": "#3D5AFE" if r['Status'] == 'Concluído' else "#FF9100"
                })
            except: continue
    calendar(events=events, options={"locale": "pt-br"})

# --- ÁREA DO PROFESSOR ---
elif perfil == "Professor" and acesso_liberado:
    st.header("👨‍🏫 Lançamento de Conteúdos")
    if not df.empty:
        disc_p = st.selectbox("1. Sua Disciplina", ["Selecione..."] + sorted(df['Disciplina'].unique()))
        if disc_p != "Selecione...":
            pends = df[(df['Disciplina'] == disc_p) & (df['Status'] == 'Pendente')]
            if pends.empty:
                st.info("Não há provas pendentes para esta disciplina.")
            else:
                opts = {f"{row['Turma']} (Dia {row['Data']})": row['ID'] for _, row in pends.iterrows()}
                id_sel = opts[st.selectbox("2. Selecione a Turma", list(opts.keys()))]
                
                with st.form("f_prof", clear_on_submit=True):
                    cont = st.text_area("3. Digite o conteúdo da prova")
                    arq = st.file_uploader("4. Upload da Prova (PDF)", type=["pdf"])
                    if st.form_submit_button("Salvar e Enviar"):
                        if cont and arq:
                            url = upload_to_drive(arq, f"Prova_{disc_p}_{id_sel}.pdf")
                            if url:
                                df.loc[df['ID'] == id_sel, ['Conteudo', 'Status', 'Link_Arquivo']] = [cont, 'Concluído', url]
                                conn.update(data=df)
                                st.success("Conteúdo e arquivo enviados com sucesso!")
                                st.rerun()
                        else:
                            st.error("Preencha o conteúdo e anexe o PDF.")

# --- ÁREA DOS PAIS ---
elif perfil == "Pai/Aluno":
    st.header("📅 Consulta de Provas")
    if not df.empty:
        t_f = st.selectbox("Escolha a Turma:", ["Selecione..."] + sorted(list(df['Turma'].unique())))
        if t_f != "Selecione...":
            exibir = df[df['Turma'] == t_f]
            if exibir.empty:
                st.warning("Nenhuma prova encontrada.")
            else:
                for _, r in exibir.iterrows():
                    status = "✅" if r['Status'] == 'Concluído' else "⏳"
                    with st.expander(f"{status} {r['Data']} - {r['Disciplina']}"):
                        st.write(f"**Aulas:** {r['Aula']}")
                        st.info(f"**Conteúdo:** {r['Conteudo']}")

else:
    st.warning("Selecione seu perfil e digite a senha na barra lateral.")
