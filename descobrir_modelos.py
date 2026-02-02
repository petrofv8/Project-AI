from google import genai

# Cole sua chave aqui dentro das aspas
api_key = "AIzaSyDQr5-cPnB5SUD--cDuYSo15YkeBn7Gd_U"

print("--- CONECTANDO AO GOOGLE ---")

try:
    client = genai.Client(api_key=api_key)
    print("Sucesso! Listando modelos disponíveis para você:")
    
    # Lista todos os modelos e filtra os que servem para chat
    for m in client.models.list():
        if "generateContent" in m.supported_actions:
            # Mostra apenas nomes limpos (ex: gemini-1.5-flash)
            print(f"✅ {m.name.replace('models/', '')}")
            
except Exception as e:
    print(f"Erro: {e}")