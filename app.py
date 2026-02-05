import streamlit as st
from google import genai
from google.genai import types

# --- Configuração da Página ---
st.set_page_config(page_title="AI English Tutor", page_icon="🎓")
st.title("🎓 English Tutor Agent")

# --- Barra Lateral (Configurações) ---
with st.sidebar:
    st.header("Configuração")
    
    # Lógica de Senha
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Chave de Professor Ativada")
    else:
        api_key = st.text_input("Cole sua Google API Key:", type="password")
    
    st.divider()
    # Opções Pedagógicas
    student_level = st.selectbox(
        "Nível do Aluno:", 
        ["A1 (Iniciante)", "A2 (Básico)", "B1 (Intermediário)", "B2 (Intermediário Superior)", "C1 (Avançado)"]
    )
    student_goal = st.text_input("Objetivo da Aula:", "Conversation and corrections")
    
    # Botão de Reset
    if st.button("Reiniciar Conversa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- Conexão Cacheada ---
@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)

if not api_key:
    st.warning("⬅️ Configure a chave para começar.")
    st.stop()

try:
    client = get_client(api_key)
except Exception as e:
    st.error(f"Erro na chave: {e}")
    st.stop()

# --- Inicialização do Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Se o chat ainda não existe, criamos agora com a "Personalidade" injetada no histórico
if "chat_session" not in st.session_state:
    
    # Montamos o prompt inicial baseado no que você escolheu na barra lateral
    prompt_do_professor = (
        f"You are an expert English Teacher. The student level is {student_level}. "
        f"Goal: {student_goal}. "
        "Interact naturally. Always finish with a question to keep conversation flowing. "
        "Correct mistakes gently if necessary."
    )

    try:
        # Criamos o chat já com um histórico "falso" para a Gemma saber quem ela é
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000
            ),
            history=[
                # Ensinamos a Gemma quem ela é através desse histórico inicial
                types.Content(role="user", parts=[types.Part(text=prompt_do_professor)]),
                types.Content(role="model", parts=[types.Part(text="Understood! I am ready to be your English Teacher.")])
            ]
        )
        
        # Opcional: A IA dá a primeira saudação
        if len(st.session_state.messages) == 0:
            boas_vindas = st.session_state.chat_session.send_message("Hello! I'm your teacher. How are you today?")
            st.session_state.messages.append({"role": "assistant", "content": boas_vindas.text})
            
    except Exception as e:
        st.error(f"Erro ao conectar com a Gemma: {e}")

# --- Interface do Chat ---

# 1. Mostra as mensagens antigas
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Caixa de entrada do aluno
if prompt := st.chat_input("Sua resposta em inglês..."):
    # Mostra a mensagem do aluno
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Busca a resposta da IA
    try:
        response = st.session_state.chat_session.send_message(prompt)
        
        # Mostra a resposta da IA
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        # Se der erro, tenta reconectar recarregando a página (opcional)
        if st.button("Tentar Novamente"):
            st.rerun()