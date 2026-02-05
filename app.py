import streamlit as st
from google import genai
from google.genai import types

# --- 1. Configuração da Página (Sempre a primeira coisa) ---
st.set_page_config(page_title="AI English Tutor", page_icon="🎓")
st.title("🎓 English Tutor Agent")

# --- 2. Barra Lateral e Variáveis (Cria o 'student_level' aqui) ---
with st.sidebar:
    st.header("Configuração")
    
    # Senha / API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Chave de Professor Ativada")
    else:
        api_key = st.text_input("Cole sua Google API Key:", type="password")
    
    st.divider()
    
    # DEFINIÇÃO DAS VARIÁVEIS DO ALUNO (Aqui que estava o problema antes)
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

# --- 3. Conexão com o Google (Gemma) ---
if not api_key:
    st.warning("⬅️ Configure a chave para começar.")
    st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

try:
    client = get_client(api_key)
except Exception as e:
    st.error(f"Erro na chave: {e}")
    st.stop()

# --- 4. Inicialização do Chat e da Personalidade ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Só cria o chat se ele ainda não existir
if "chat_session" not in st.session_state:
    
    # Monta o prompt usando as variáveis que criamos lá em cima na barra lateral
    prompt_do_professor = (
        f"You are an expert English Teacher. The student level is {student_level}. "
        f"Goal: {student_goal}. "
        "Interact naturally. Always finish with a question to keep conversation flowing. "
        "Correct mistakes gently if necessary."
    )

    try:
        # Cria o chat com o histórico "falso" para ensinar a Gemma
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000
            ),
            history=[
                types.Content(role="user", parts=[types.Part(text=prompt_do_professor)]),
                types.Content(role="model", parts=[types.Part(text="Understood! I am ready to be your English Teacher.")])
            ]
        )
        
        # Mensagem de boas-vindas automática
        if len(st.session_state.messages) == 0:
            msg_inicial = f"Hello! I see you are level **{student_level}**. Let's start! {student_goal}."
            st.session_state.messages.append({"role": "assistant", "content": msg_inicial})
            
    except Exception as e:
        st.error(f"Erro ao conectar com a Gemma: {e}")

# --- 5. Interface do Chat (Loop Principal) ---

# Mostra mensagens antigas
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Captura nova mensagem do aluno
if prompt := st.chat_input("Sua resposta em inglês..."):
    # Mostra a mensagem do aluno
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Busca a resposta da IA
    if st.session_state.chat_session:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            if st.button("Tentar Novamente"):
                st.rerun()