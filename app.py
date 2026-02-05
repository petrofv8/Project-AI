import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import os
import base64

# --- 1. Configuração da Página e Estilo ---
st.set_page_config(page_title="AI English Tutor Pro", page_icon="🎓", layout="centered")

# CSS para melhorar a aparência
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #4CAF50; color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7d32, #1b5e20); }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 English Tutor Agent")
st.caption("Seu professor particular de inglês com IA e áudio.")

# --- Funções de Apoio ---
def reset_chat():
    st.session_state.chat_session = None
    st.session_state.messages = []

def text_to_speech(text):
    """Gera áudio da resposta em inglês."""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")
        with open("response.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
            st.markdown(md, unsafe_allow_html=True)
        os.remove("response.mp3")
    except:
        pass

# --- 2. Barra Lateral ---
with st.sidebar:
    st.header("⚙️ Painel do Professor")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")
    
    st.divider()
    
    student_level = st.selectbox(
        "Nível do Aluno:", 
        ["A1 (Iniciante)", "A2 (Básico)", "B1 (Intermediário)", "B2 (Intermediário Superior)", "C1 (Avançado)"],
        on_change=reset_chat
    )
    
    student_goal = st.text_input("Foco da Aula:", "Conversação Geral", on_change=reset_chat)

    st.divider()
    
    # BOTÃO DE EXERCÍCIO
    if st.button("📝 Gerar Exercício de Fixação"):
        if st.session_state.chat_session:
            st.session_state.request_exercise = True
        else:
            st.warning("Comece uma conversa primeiro!")

    if st.button("🔄 Reiniciar Conversa"):
        reset_chat()
        st.rerun()

# --- 3. Conexão e Inicialização ---
if not api_key:
    st.warning("Configure a chave para começar.")
    st.stop()

@st.cache_resource
def get_client(key): return genai.Client(api_key=key)

client = get_client(api_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state: st.session_state.chat_session = None
if "request_exercise" not in st.session_state: st.session_state.request_exercise = False

# Criar Sessão de Chat
if st.session_state.chat_session is None:
    prompt_base = (
        f"You are a friendly bilingual English Teacher for Brazilians. Student Level: {student_level}. Goal: {student_goal}. "
        "Instructions: Prioritize English, explain in Portuguese if needed. Correct gently. Be conversational."
    )
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(temperature=0.7),
            history=[
                types.Content(role="user", parts=[types.Part(text=prompt_base)]),
                types.Content(role="model", parts=[types.Part(text="Understood! Let's start the class.")])
            ]
        )
        if not st.session_state.messages:
            welcome = "Hello! I'm your teacher. Let's practice! How are you feeling today?"
            st.session_state.messages.append({"role": "assistant", "content": welcome})
    except Exception as e:
        st.error(f"Erro: {e}")

# --- 4. Lógica de Exercício ---
if st.session_state.request_exercise:
    with st.spinner("Gerando exercício personalizado..."):
        exercise_prompt = "Based on our conversation, create a short exercise (3 questions) with translations. Focus on the vocabulary we just used."
        response = st.session_state.chat_session.send_message(exercise_prompt)
        st.session_state.messages.append({"role": "assistant", "content": f"📝 **EXERCISE TIME!**\n\n{response.text}"})
        st.session_state.request_exercise = False # Reseta o gatilho

# --- 5. Chat Interface ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type in English..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            # GERA O ÁUDIO PARA A RESPOSTA
            text_to_speech(response.text)
            
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro: {e}")