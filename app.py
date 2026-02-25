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

# --- 2. CENTRAL DE CONTEÚDO (Definida ANTES de ser usada) ---
CONTEUDO_AULAS = {
    "aula 1": {
        "cenario": "Colega de trabalho no elevador",
        "instrucao": "Scenario: You are a coworker in an elevator. Be brief and professional."
    },
    "aula 2": {
        "cenario": "Conversa básica de trabalho",
        "instrucao": "Scenario: New acquaintance. Ask about their job and keep it basic/friendly."
    },
    "aula 3": {
        "cenario": "Penn Station (New York) - Bilheteria",
        "instrucao": "Scenario: You are a ticket agent at Penn Station. The student wants to buy a ticket. Focus on MONEY and PRICES. Tell the student the price of the ticket (e.g., $15.50) and ask how they want to pay. Use simple present questions."
    },
    "aula 4": {
        "cenario": "Recepção de Empresa de Tech",
        "instrucao": "Scenario: Receptionist at a big tech company. Ask for their name and meeting info."
    },
    "aula 5": {
        "cenario": "Networking Coffee",
        "instrucao": "Scenario: Professional having coffee. Ask about career goals."
    },
    "aula 6": {
        "cenario": "Office Tour (Video Call)",
        "instrucao": "Scenario: Foreign colleague on video tour. Ask questions about their office environment."
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

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Painel do Aluno")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")

    st.divider()
    student_level = st.selectbox("Seu Nível:", ["A1", "A2", "B1", "B2", "C1"], on_change=reset_chat)
    student_goal = st.text_input("Tema Livre:", placeholder="Ex: Business, Travel...", on_change=reset_chat)
    
    if st.button("🔄 Reiniciar Conversa"):
        reset_chat()
        st.rerun()

    # LISTA DE AULAS (Agora funciona porque o dicionário já existe acima)
    st.divider()
    st.markdown("### 📚 Cronograma de Aulas")
    for aula, dados in CONTEUDO_AULAS.items():
        st.write(f"**{aula.capitalize()}**: {dados['cenario']}")

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
    master_prompt = (
        f"You are a motivating English Teacher. Student level: {student_level}. "
        "Rules: 1. Short sentences. 2. Correction in brackets [ ]. 3. Stay in character."
    )
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(temperature=0.9),
            history=[types.Content(role="user", parts=[types.Part(text=master_prompt)])]
        )
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your teacher. Choose a lesson below or type anything!"})
    except: st.error("Erro na API")

# --- 6. INTERFACE DE CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

st.write("---")
audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')
input_text = st.chat_input("Digite 'Aula 1', 'Aula 2'...")

prompt = audio_text if audio_text else input_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    texto_min = prompt.lower()
    foi_aula = False
    
    for aula, dados in CONTEUDO_AULAS.items():
        if aula in texto_min:
            foi_aula = True
            # Força o reinício do personagem para não confundir a IA
            instrucao_aula = f"SYSTEM: START NEW SCENARIO NOW. {dados['instrucao']} Level: {student_level}. Correct in [ ]."
            st.session_state.chat_session = client.chats.create(
                model="gemma-3-27b-it", 
                history=[types.Content(role="user", parts=[types.Part(text=instrucao_aula)])]
            )
            st.toast(f"Iniciando {dados['cenario']}...")
            break

    with st.chat_message("assistant"):
        try:
            # Se for aula, enviamos o gatilho "GO" para ela começar falando
            msg_envio = "GO!" if foi_aula else f"Topic: {student_goal}. Level: {student_level}. Message: {prompt}"
            response = st.session_state.chat_session.send_message(msg_envio)
            st.markdown(response.text)
            text_to_speech(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except: st.error("Erro ao gerar resposta.")