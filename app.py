# --- CÓDIGO DA VISÃO MENSAL ATUALIZADO ---
    st.divider()
    st.subheader("📅 Visão Mensal")
    events = []
    if not df.empty:
        for _, r in df.iterrows():
            try:
                # Limpa a data e tenta converter de forma robusta
                data_str = str(r['Data']).replace('/', '-')
                if data_str and '-' in data_str:
                    partes = data_str.split('-')
                    if len(partes) == 3:
                        d, m, y = partes
                        # Garante que o ano tenha 4 dígitos (ex: 2026)
                        if len(y) == 2: y = f"20{y}"
                        
                        events.append({
                            "title": f"{r['Turma']}: {r['Disciplina']}", 
                            "start": f"{y}-{m}-{d}", 
                            "end": f"{y}-{m}-{d}", 
                            "color": "#3D5AFE" if r['Status'] == 'Concluído' else "#FF9100"
                        })
            except Exception as e:
                continue # Pula linhas com erro sem travar o calendário
    
    calendar(events=events, options={
        "locale": "pt-br",
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "buttonText": {"today": "Hoje", "month": "Mês", "week": "Semana"}
    })
