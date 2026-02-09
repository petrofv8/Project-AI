import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
import os
import base64

# --- 1. Design & CSS (Aparência Moderna) ---
st.set_page_config(page_title="Petro AI English", page_icon="🇬🇧", layout="centered",initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Estilização das bolhas de chat */
    .stChatMessage { border-radius: 20px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    /* Botões da barra lateral */
    .stButton>button { border-radius: 10px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    /* Esconder o menu superior do Streamlit para parecer um App */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Funções de Áudio ---
def text_to_speech(text):
    """Transforma texto da IA em áudio (Pronúncia da Professora)"""
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

# --- 3. Configurações da Barra Lateral ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/197/197/197374.png", width=100) # Bandeira UK
    st.title("English Tutor Pro")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")

    st.divider()
    student_level = st.selectbox("Nível:", ["A1", "A2", "B1", "B2", "C1"], on_change=reset_chat)
    student_goal = st.text_input("Objetivo:", "Conversation", on_change=reset_chat)
    
    st.divider()
    if st.button("📝 Gerar Exercícios"):
        st.session_state.request_exercise = True
    
    if st.button("🔄 Reiniciar"):
        reset_chat()
        st.rerun()

# --- 4. Inicialização da IA ---
if not api_key:
    st.info("Por favor, insira sua chave na lateral para começar a aula.")
    st.stop()

@st.cache_resource
def get_client(key): return genai.Client(api_key=key)

client = get_client(api_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state: st.session_state.chat_session = None
if "request_exercise" not in st.session_state: st.session_state.request_exercise = False

if st.session_state.chat_session is None:
    prompt_base = f"You are a helpful English Teacher for Brazilians. Level: {student_level}. Goal: {student_goal}. Correct pronunciation and grammar."
    st.session_state.chat_session = client.chats.create(
        model="gemma-3-27b-it",
        config=types.GenerateContentConfig(temperature=0.7),
        history=[types.Content(role="user", parts=[types.Part(text=prompt_base)]),
                 types.Content(role="model", parts=[types.Part(text="Hello! Let's start.")])]
    )
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your teacher. How can I help you today?"})

# --- 5. Lógica de Exercícios ---
if st.session_state.request_exercise:
    with st.spinner("Preparing exercises..."):
        resp = st.session_state.chat_session.send_message("Create 3 quick exercises based on our current conversation.")
        st.session_state.messages.append({"role": "assistant", "content": f"🎯 **Practice Time!**\n\n{resp.text}"})
        st.session_state.request_exercise = False

# --- 6. Interface do Chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 🎙️ RECURSO DE FALA (NOVO!) ---
st.write("---")
col1, col2 = st.columns([1, 4])
with col1:
    # Botão de Microfone
    audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')

# Se o aluno falou algo pelo microfone ou digitou
prompt = None
if audio_text:
    prompt = audio_text
elif input_text := st.chat_input("Ou digite aqui sua resposta..."):
    prompt = input_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Se veio do áudio, pedimos para a IA avaliar a "pronúncia" (o texto capturado)
            final_prompt = prompt
            if audio_text:
                final_prompt = f"The student spoke this: '{prompt}'. If the words seem wrong or misspelled, it might be a pronunciation error. Correct it and respond."
            
            response = st.session_state.chat_session.send_message(final_prompt)
            st.markdown(response.text)
            text_to_speech(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro: {e}")