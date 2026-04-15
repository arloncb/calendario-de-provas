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

# Lista Oficial Atualizada e em Ordem Alfabética
LISTA_DISCIPLINAS = [
    "Arte", 
    "Biologia", 
    "Ciências", 
    "Ciências da Natureza na Cont.", 
    "Ciências Humanas e Sociedade", 
    "Ed. Física", 
    "Filosofia", 
    "Física", 
    "Geografia", 
    "História", 
    "Leitura e Produção de texto",
    "Letramento e raciocínio Matemático", 
    "Língua Inglesa", 
    "Língua Portuguesa", 
    "Literatura Arte Movimento", 
    "Matemática", 
    "Química", 
    "Sociologia", 
    "Tecnologia e Cidadania Digital"
]

st.set_page_config(page_title="Calendário Escolar", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_lido = conn.read(ttl=0)
        # Substitui valores nulos (NaN) por texto vazio
        df_lido = df_lido.fillna('')
        # Força colunas de texto para evitar erros de tipo
        for col in ['Conteudo', 'Status', 'Link_Arquivo']:
            if col in df_lido.columns:
                df_lido[col] = df_lido[col].astype(str)
        return df_lido
    except:
        return pd.DataFrame()

# --- FUNÇÃO DE UPLOAD PARA O DRIVE ---
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

# --- CABEÇALHO COM LOGO ---
col_logo, col_tit = st.columns([1, 6])
with col_logo:
    try:
        st.image(URL_LOGO, width=120)
    except:
        st.warning("Logo não encontrado")
with col_tit:
    st.title("Portal do Calendário de Avaliações")
    st.write("Sistema Integrado de Gestão Pedagógica")

# --- BARRA LATERAL (LOGIN) ---
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
        col1, col2 = st.columns(2)
        with col1:
            bimestre = st.selectbox("Bimestre", ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            turma = st.selectbox("Turma", ["4° A", "5° A", "6° A", "6° B", "6° C", "7° A", "8° A", "9° A", "1° A", "1° B", "2° A", "3° A"])
            disciplina = st.selectbox("Disciplina", LISTA_DISCIPLINAS)
        with col2:
            data_p = st.date_input("Data da Prova", format="DD/MM/YYYY")
            aula = st.multiselect("Aulas (1ª a 8ª)", [f"{i}ª aula" for i in range(1, 9)])
            
            # Bloqueio de Fim de Semana
            eh_fim_de_semana = data_p.weekday() >= 5
            if eh_fim_de_semana:
                st.error("❌ Sábados e Domingos não são permitidos para avaliações.")

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
