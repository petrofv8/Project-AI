import streamlit as st
from google import genai
from google.genai import types

# --- Configuração da Página ---
st.set_page_config(page_title="AI English Tutor", page_icon="🎓")
st.title("🎓 English Tutor Agent")

# --- Barra Lateral (Configurações) ---
with st.sidebar:
    st.header("Configuração")
    
    # Lógica Inteligente de Senha:
    # 1. Tenta ler dos Segredos do Streamlit (para os alunos não digitarem)
    # 2. Se não achar, abre a caixinha para digitar (para você testar)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Chave de Professor Ativada")
    else:
        api_key = st.text_input("Cole sua Google API Key:", type="password")
    
    st.divider()
    student_level = st.selectbox("Nível:", ["A1 (Iniciante)", "B1 (Intermediário)", "C1 (Avançado)"])
    student_goal = st.text_input("Objetivo:", "Travel and order food")
    
    if st.button("Reiniciar Conversa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- Conexão Cacheada (Evita o erro de desconexão) ---
@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)

if not api_key:
    st.warning("⬅️ Configure a chave nos 'Secrets' ou cole na barra lateral.")
    st.stop()

try:
    client = get_client(api_key)
except Exception as e:
    st.error(f"Erro na chave: {e}")
    st.stop()

# --- Lógica do Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    system_instruction = f"""
    Act as an English Teacher. Level: {student_level}. Goal: {student_goal}.
    Rules: Correct mistakes, be kind, ask questions.
    Start with a question.
    """
    
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.0-flash-exp",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        response = st.session_state.chat_session.send_message("Start class.")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")

# Interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Sua resposta em inglês..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro: {e}")