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
st.divider()
st.markdown("### 📚 Cronograma de Aulas")
for aula, dados in CONTEUDO_AULAS.items():
    st.write(f"**{aula.capitalize()}**: {dados['cenario']}")
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
        "instrucao": "Scenario: You are a coworker in an elevator. Be brief, professional, and start with a casual greeting like 'Hey, going up?'."
    },
    "aula 2": {
        "cenario": "Conversa básica de trabalho",
        "instrucao": "Scenario: You are a new acquaintance at a professional event. Ask the student about their job and keep a basic, friendly conversation about their daily routine."
    },
    "aula 3": {
        "cenario": "Penn Station (New York)",
        "instrucao": "Scenario: You are a ticket agent at Penn Station, NYC. You are in a hurry because it is busy. Ask the student where they want to go and help them buy a ticket."
    },
    "aula 4": {
        "cenario": "Recepção de Empresa de Tech",
        "instrucao": "Scenario: You are a receptionist at a big tech company (like Google or Apple). Ask the student for their name and who they are here to see for their meeting."
    },
    "aula 5": {
        "cenario": "Networking Coffee",
        "instrucao": "Scenario: You are a professional having coffee with the student to discuss networking. Ask about their career goals and professional interests."
    },
    "aula 6": {
        "cenario": "Office Tour (Video Call)",
        "instrucao": "Scenario: You are a foreign colleague watching a video tour. The student is showing you their office. Ask questions about the desk, the equipment, and the people around."
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
# --- 6. INTERFACE DE CHAT E VOZ (Versão "Force Roleplay") ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.write("---")
audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')
input_text = st.chat_input("Digite 'Aula 1' ou sua resposta...")

prompt = audio_text if audio_text else input_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    texto_min = prompt.lower()
    foi_aula = False
    
    # 1. Checagem de Gatilho de Aula
    for aula, dados in CONTEUDO_AULAS.items():
        if aula in texto_min:
            foi_aula = True
            # REINICIALIZAÇÃO FORÇADA: Criamos um novo chat só para essa aula
            prompt_roleplay = (
                f"ACT NOW: {dados['instrucao']} "
                f"Student Level: {student_level}. "
                "CRITICAL RULE: Stay in character. Use brackets [ ] for corrections. "
                "DO NOT say 'Understood'. Just start the conversation NOW in English."
            )
            
            try:
                # Substituímos a sessão atual por uma focada apenas no cenário
                st.session_state.chat_session = client.chats.create(
                    model="gemma-3-27b-it",
                    config=types.GenerateContentConfig(temperature=0.9),
                    history=[
                        types.Content(role="user", parts=[types.Part(text=prompt_roleplay)]),
                    ]
                )
                st.toast(f"Cenário Ativado: {dados['cenario']}", icon="🎭")
            except Exception as e:
                st.error(f"Erro ao mudar cenário: {e}")
            break

    # 2. Define o que enviar para a IA
    # Se for aula, o primeiro comando já foi enviado na criação do chat acima.
    # Se não for aula, enviamos o prompt normal.
    with st.chat_message("assistant"):
        try:
            if foi_aula:
                # Pegamos a primeira resposta do novo chat de roleplay
                response = st.session_state.chat_session.send_message("GO!")
            else:
                contexto = f"Context: {student_goal}. " if student_goal else ""
                msg_envio = f"{contexto}Student Level: {student_level}. Correct in [ ]. Message: {prompt}"
                response = st.session_state.chat_session.send_message(msg_envio)
            
            st.markdown(response.text)
            text_to_speech(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro: {e}")