def upload_to_drive(file, filename):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename, 
            'parents': [ID_PASTA_DRIVE]
        }
        
        # O pulo do gato: convertemos o arquivo para bytes de forma segura
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='application/pdf', resumable=True)
        
        # Criamos o arquivo na pasta onde o robô tem permissão de editor
        file_drive = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        return file_drive.get('webViewLink')
    except Exception as e:
        # Se o erro de cota persistir, é porque o Google exige que a pasta
        # esteja configurada para que o 'Editor' possa adicionar arquivos.
        st.error(f"Erro de permissão/cota no Drive: {e}")
        return None
