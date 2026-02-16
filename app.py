import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
import os
import base64

# --- 1. CONFIGURAÇÃO E DESIGN ---
st.set_page_config(
    page_title="BUILDERS AI ACADEMY", 
    page_icon="🎓", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stChatMessage { border-radius: 20px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #4CAF50; color: white; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CENTRAL DE CONTEÚDO ---
CONTEUDO_AULAS = {
    "aula 1": {
        "cenario": "Colega de trabalho no elevador",
        "instrucao": "Scenario: You are a coworker in an elevator. Be brief, professional, and start with a casual greeting."
    },
    "aula 2": {
        "cenario": "Entrevista com Recrutador",
        "instrucao": "Scenario: You are a professional recruiter. Ask about my profession and passions."
    }
}

# --- 3. FUNÇÕES DE APOIO ---
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

# --- 4. BARRA LATERAL (Recuperando o Campo de Tema) ---
with st.sidebar:
    st.header("⚙️ Painel do Aluno")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")

    st.divider()
    student_level = st.selectbox(
        "Seu Nível de Inglês:", 
        ["A1", "A2", "B1", "B2", "C1"],
        on_change=reset_chat
    )
    
    # RECOLOCANDO O CAMPO QUE VOCÊ SOLICITOU:
    student_goal = st.text_input(
        "O que quer praticar hoje?", 
        placeholder="Ex: Business, Travel, Pizza...",
        on_change=reset_chat
    )
    
    st.divider()
    if st.button("🔄 Reiniciar Conversa"):
        reset_chat()
        st.rerun()

# --- 5. INICIALIZAÇÃO DA IA ---
if not api_key:
    st.info("Insira sua chave na lateral para começar.")
    st.stop()

@st.cache_resource
def get_client(key): return genai.Client(api_key=key)
client = get_client(api_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state: st.session_state.chat_session = None

if st.session_state.chat_session is None:
    # O prompt mestre agora inclui o 'student_goal' da lateral
    master_prompt = (
        f"You are a motivating English Teacher. Student level: {student_level}. "
        f"Current Topic/Goal: {student_goal if student_goal else 'General Conversation'}. "
        "Rules: 1. Short sentences. 2. Correction in brackets [ ]. "
        "3. Translate Portuguese and encourage English. 4. Keep it flowing."
    )
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(temperature=0.8),
            history=[
                types.Content(role="user", parts=[types.Part(text=master_prompt)]),
                types.Content(role="model", parts=[types.Part(text="I am ready to teach.")])
            ]
        )
        if not st.session_state.messages:
            welcome_msg = f"Hello! I'm ready for our {student_level} session about {student_goal if student_goal else 'anything'}. How are you?"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    except Exception as e:
        st.error(f"Erro: {e}")

# --- 6. INTERFACE DE CHAT ---
# --- 6. INTERFACE DE CHAT E VOZ (Versão Estabilizada) ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.write("---")

# 1. Primeiro, criamos o componente de microfone
# Importante: a variável audio_text PRECISA existir, mesmo que vazia
audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')

# 2. Criamos a caixa de texto
input_text = st.chat_input("Digite 'Aula 1' ou sua resposta...")

# 3. Lógica de decisão: Prioriza o Áudio, depois o Texto
prompt = None
if audio_text:
    prompt = audio_text
elif input_text:
    prompt = input_text

# 4. Se houver alguma entrada, processamos
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    texto_min = prompt.lower()
    instrucao_final = prompt
    foi_aula = False
    
    # Checagem de Gatilhos de Aula
    for aula, dados in CONTEUDO_AULAS.items():
        if aula in texto_min:
            instrucao_final = (
                f"SYSTEM: Ignore everything before. START SCENARIO NOW. "
                f"Role: {dados['instrucao']} "
                f"Level: {student_level}. Correct using brackets [ ]."
            )
            foi_aula = True
            st.toast(f"Iniciando {dados['cenario']}...", icon="🚀")
            break
    
    if not foi_aula:
        contexto_tema = f"Topic: {student_goal}." if student_goal else "General chat."
        instrucao_final = (
            f"{contexto_tema} Student says: '{prompt}'. "
            f"Level: {student_level}. Correct using brackets [ ]."
        )

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(instrucao_final)
            texto_resposta = response.text
            st.markdown(texto_resposta)
            text_to_speech(texto_resposta)
            st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
        except Exception as e:
            st.error(f"Erro na conexão com a IA: {e}")