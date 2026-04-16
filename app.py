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

acesso_lib
