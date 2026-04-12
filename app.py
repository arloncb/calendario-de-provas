def upload_to_drive(file, filename):
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [ID_PASTA_DRIVE]
        }
        
        # O segredo: MediaIoBaseUpload com resumable=True ajuda a evitar erros de cota em contas de serviço
        media = MediaIoBaseUpload(
            io.BytesIO(file.getvalue()), 
            mimetype='application/pdf', 
            resumable=True
        )
        
        # Adicionamos supportsAllDrives para garantir a compatibilidade
        file_drive = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True 
        ).execute()
        
        return file_drive.get('webViewLink')
    except Exception as e:
        # Se o erro 403 persistir, vamos dar uma instrução clara no log
        if "storageQuotaExceeded" in str(e):
            st.error("Erro de Cota: O Google Drive exige que esta pasta seja de um 'Drive Compartilhado' ou que o Robô tenha permissão total.")
        else:
            st.error(f"Erro no Drive: {e}")
        return None
