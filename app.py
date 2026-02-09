import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
import os
import base64

# --- 1. Configuração da Página e Estilo ---
st.set_page_config(
    page_title="Petro AI English", 
    page_icon="🇬🇧", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS Seguro e Blindado
st.markdown("""
    <style>
    /* Forçar visibilidade da barra lateral */
    [data-testid="stSidebarNav"] { visibility: visible !important; }
    
    /* Estilização Geral */
    .stChatMessage { border-radius: 20px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #4CAF50; color: white; }
    
    /* Esconder elementos desnecessários para alunos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 English Tutor Agent")

# --- Funções de Apoio ---
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("voice.mp3")
        with open("voice.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
            st.markdown(md, unsafe_allow_html=True)
        os.remove("voice.mp3")
    except: pass

def reset_chat():
    st.session_state.chat_session = None
    st.session_state.messages = []

# --- 2. Barra Lateral ---
with st.sidebar:
    st.header("⚙️ Painel do Professor")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")

    st.divider()
    student_level = st.selectbox("Nível:", ["A1", "A2", "B1", "B2", "C1"], on_change=reset_chat)
    student_goal = st.text_input("Objetivo:", "Conversation", on_change=reset_chat)
    
    if st.button("📝 Gerar Exercícios"):
        st.session_state.request_exercise = True
    
    if st.button("🔄 Reiniciar"):
        reset_chat()
        st.rerun()

# --- 3. Inicialização e Conexão ---
if not api_key:
    st.info("Insira sua chave na lateral para começar.")
    st.stop()

@st.cache_resource
def get_client(key): return genai.Client(api_key=key)

client = get_client(api_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state: st.session_state.chat_session = None
if "request_exercise" not in st.session_state: st.session_state.request_exercise = False

if st.session_state.chat_session is None:
    prompt_base = f"You are a helpful English Teacher for Brazilians. Level: {student_level}. Goal: {student_goal}. Correct pronunciation and grammar."
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(temperature=0.7),
            history=[
                types.Content(role="user", parts=[types.Part(text=prompt_base)]),
                types.Content(role="model", parts=[types.Part(text="Understood! Let's start.")])
            ]
        )
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your teacher. Let's practice!"})
    except Exception as e:
        st.error(f"Erro na conexão: {e}")

# --- 4. Lógica de Exercícios ---
if st.session_state.request_exercise:
    with st.spinner("Preparing exercises..."):
        resp = st.session_state.chat_session.send_message("Create 3 quick exercises based on our current conversation.")
        st.session_state.messages.append({"role": "assistant", "content": f"🎯 **Practice!**\n\n{resp.text}"})
        st.session_state.request_exercise = False

# --- 5. Interface do Chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 🎤 Microfone e Entrada ---
st.write("---")
audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')

prompt = None
if audio_text:
    prompt = audio_text
elif input_text := st.chat_input("Ou digite aqui..."):
    prompt = input_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        final_prompt = prompt
        if audio_text:
            final_prompt = f"The student spoke: '{prompt}'. Correct it and respond."
        
        response = st.session_state.chat_session.send_message(final_prompt)
        st.markdown(response.text)
        text_to_speech(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})