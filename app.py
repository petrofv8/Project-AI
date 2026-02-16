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

# --- 2. CENTRAL DE CONTEÚDO (Adicione novas aulas aqui) ---
CONTEUDO_AULAS = {
    "aula 1": {
        "cenario": "Colega de trabalho no elevador",
        "instrucao": "Scenario: You are a coworker in an elevator. Be brief, professional, and start with a casual greeting like 'Hey, going up?'."
    },
    "aula 2": {
        "cenario": "Entrevista com Recrutador",
        "instrucao": "Scenario: You are a professional recruiter. Ask about my profession and my passions. Be polite but formal."
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
    # Nível dinâmico que a IA irá seguir
    student_level = st.selectbox(
        "Seu Nível de Inglês:", 
        ["A1 (Iniciante)", "A2 (Básico)", "B1 (Intermediário)", "B2 (Intermediário Superior)", "C1 (Avançado)"],
        on_change=reset_chat
    )
    
    st.divider()
    if st.button("🔄 Reiniciar Conversa"):
        reset_chat()
        st.rerun()

# --- 5. CONEXÃO E INICIALIZAÇÃO ---
if not api_key:
    st.info("Insira sua chave na lateral para começar.")
    st.stop()

@st.cache_resource
def get_client(key): return genai.Client(api_key=key)

client = get_client(api_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state: st.session_state.chat_session = None

# Inicializa o chat com as regras pedagógicas de 20 anos de experiência
if st.session_state.chat_session is None:
    master_prompt = (
        f"You are a motivating English Teacher. Student level: {student_level}. "
        "Rules: 1. Use short sentences. 2. If the student makes a mistake, respond naturally "
        "and put the correction in brackets [ ]. Example: 'I'm fine too [I am fine too]'. "
        "3. If the student speaks Portuguese, translate it and encourage English. "
        "4. Never give grammar lectures, just keep the conversation flowing."
    )
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(temperature=0.8),
            history=[
                types.Content(role="user", parts=[types.Part(text=master_prompt)]),
                types.Content(role="model", parts=[types.Part(text="Understood Teacher Petro. I am ready.")])
            ]
        )
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": f"Hello! I'm ready. Digite 'Aula 1' ou 'Aula 2' para começarmos o cenário!"})
    except Exception as e:
        st.error(f"Erro: {e}")

# --- 6. INTERFACE DE CHAT E VOZ ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.write("---")
audio_text = speech_to_text(start_prompt="🎤 Falar", stop_prompt="⏹️ Parar", language='en-US', key='speech')

prompt = None
if audio_text:
    prompt = audio_text
elif input_text := st.chat_input("Digite 'Aula 1' ou 'Aula 2'..."):
    prompt = input_text

if prompt:
    # 1. Adiciona a mensagem do aluno na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    # 2. Lógica de Gatilho (Verifica se é comando de aula)
    texto_min = prompt.lower()
    foi_aula = False
    
    for aula, dados in CONTEUDO_AULAS.items():
        if aula in texto_min:
            # Comando "Bravo": Forçamos a IA a ignorar o texto e assumir o papel
            instrucao_final = (
                f"INSTRUCTION: Ignore previous context. Start NEW SCENARIO NOW. "
                f"Role: {dados['instrucao']}. Level: {student_level}. "
                "Correction Rule: Use brackets [ ] for every mistake. "
                "Start the conversation in character now."
            )
            foi_aula = True
            st.toast(f"Iniciando {dados['cenario']}...", icon="🚀")
            break
    
    # Se não for aula, é apenas conversa normal
    if not foi_aula:
        instrucao_final = prompt

    # 3. Resposta da IA
    with st.chat_message("assistant"):
        try:
            # Enviamos o comando forçado para a IA
            response = st.session_state.chat_session.send_message(instrucao_final)
            
            # Limpamos a resposta caso ela venha com "Understood" ou confirmações chatas
            texto_resposta = response.text
            
            st.markdown(texto_resposta)
            text_to_speech(texto_resposta)
            st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            
        except Exception as e:
            st.error(f"Erro: {e}")