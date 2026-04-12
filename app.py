import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

# --- CONFIGURAÇÕES GERAIS ---
ID_PASTA_DRIVE = "1YJKNhOFygcscaZe74jrEkkysRIYUs49-"
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

# Função de Upload para o Drive (Corrigida)
def upload_to_drive(file, filename):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [ID_PASTA_DRIVE]
        }
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='application/pdf')
        
        file_drive = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file_drive.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

df = get_data()

# --- INTERFACE ---
st.title("📌 Portal do Calendário de Avaliações")

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
            proximo_id = int(df['ID'].max() + 1) if not df.empty and 'ID' in df.columns else 1
            nova_linha = pd.DataFrame([{
                "ID": proximo_id, "Bimestre": bimestre, "Turma": turma, 
                "Disciplina": disciplina, "Data": data_p.strftime("%d-%m-%Y"), 
                "Aula": ", ".join(aula), "Conteudo": "Pendente", 
                "Status": "Pendente", "Link_Arquivo": ""
            }])
            conn.update(data=pd.concat([df, nova_linha], ignore_index=True))
            st.success("Agendado!")
            st.rerun()

    st.divider()
    st.subheader("📂 Provas para Análise")
    if not df.empty and "Link_Arquivo" in df.columns:
        provas_arquivos = df[df['Link_Arquivo'] != ""]
        if not provas_arquivos.empty:
            for _, row in provas_arquivos.iterrows():
                st.write(f"📄 **{row['Disciplina']} ({row['Turma']})**: [Ver PDF da Prova]({row['Link_Arquivo']})")
        else:
            st.info("Nenhuma prova enviada ainda.")

    st.divider()
    st.subheader("📅 Visão Mensal")
    events = []
    if not df.empty:
        for _, row in df.iterrows():
            try:
                d, m, y = row['Data'].split('-')
                events.append({"title": f"{row['Turma']}: {row['Disciplina']}", "start": f"{y}-{m}-{d}", "end": f"{y}-{m}-{d}", "color": "#3D5AFE" if row['Status'] == 'Concluído' else "#FF9100"})
            except: continue
    calendar(events=events, options={"locale": "pt-br"})

# --- ÁREA DO PROFESSOR ---
elif perfil == "Professor" and acesso_liberado:
    st.header("👨‍🏫 Lançamento de Conteúdos")
    if not df.empty:
        disciplinas = sorted(df['Disciplina'].unique())
        disc_f = st.selectbox("1. Sua Disciplina", ["Selecione..."] + disciplinas)
        
        if disc_f != "Selecione...":
            pendentes = df[(df['Disciplina'] == disc_f) & (df['Status'] == 'Pendente')]
            if pendentes.empty:
                st.info("Sem provas pendentes.")
            else:
                dict_provas = {f"{row['Turma']} ({row['Data']})": row['ID'] for _, row in pendentes.iterrows()}
                escolha = st.selectbox("2. Selecione a Turma", list(dict_provas.keys()))
                id_sel = dict_provas[escolha]
                
                with st.form("form_prof", clear_on_submit=True):
                    conteudo = st.text_area("3. Conteúdo da Prova")
                    arquivo = st.file_uploader("4. Upload da Prova (PDF)", type=["pdf"])
                    if st.form_submit_button("Salvar e Enviar"):
                        if conteudo and arquivo:
                            url = upload_to_drive(arquivo, f"Prova_{disc_f}_{id_sel}.pdf")
                            if url:
                                df.loc[df['ID'] == id_sel, 'Conteudo'] = conteudo
                                df.loc[df['ID'] == id_sel, 'Status'] = 'Concluído'
                                df.loc[df['ID'] == id_sel, 'Link_Arquivo'] = url
                                conn.update(data=df)
                                st.success("Enviado com sucesso!")
                                st.rerun()
                        else:
                            st.error("Preencha o conteúdo e anexe o PDF.")

# --- ÁREA DOS PAIS ---
elif perfil == "Pai/Aluno":
    st.header("📅 Consulta de Provas")
    if not df.empty:
        turma_f = st.selectbox("Escolha a Turma:", ["Selecione..."] + sorted(list(df['Turma'].unique())))
        if turma_f != "Selecione...":
            exibir = df[df['Turma'] == turma_f]
            for _, row in exibir.iterrows():
                emoji = "✅" if row['Status'] == 'Concluído' else "⏳"
                with st.expander(f"{emoji} {row['Data']} - {row['Disciplina']}"):
                    st.write(f"**Aulas:** {row['Aula']}")
                    st.info(f"**Conteúdo:** {row['Conteudo']}")
