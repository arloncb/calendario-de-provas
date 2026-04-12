import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Calendário de Provas", layout="wide")

# Colocamos o link exato da sua planilha direto aqui!
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1gPhMASo7yOsn5HhvLw6_rGkYbSkcBB_xUsgN8QgzhWw/edit?gid=0#gid=0"

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados usando a URL direta
def get_data():
    return conn.read(spreadsheet=URL_PLANILHA, ttl="0")

st.title("📌 Portal do Calendário de Avaliações")

# ... (O resto do código daqui para baixo continua igualzinho!) ...
