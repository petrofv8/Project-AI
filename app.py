import streamlit as st
from google import genai
from google.genai import types

# --- 1. Configuração da Página ---
st.set_page_config(page_title="AI English Tutor", page_icon="🎓")
st.title("🎓 English Tutor Agent")

# --- Função para Resetar o Chat (Evita o erro NoneType) ---
def reset_chat():
    st.session_state.chat_session = None
    st.session_state.messages = []

# --- 2. Barra Lateral Inteligente ---
with st.sidebar:
    st.header("Configuração")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Chave Ativada")
    else:
        api_key = st.text_input("Cole sua Google API Key:", type="password")
    
    st.divider()
    
    # IMPORTANTE: O on_change=reset_chat faz o app "acordar" quando você muda o nível
    student_level = st.selectbox(
        "Nível do Aluno:", 
        ["A1 (Iniciante)", "A2 (Básico)", "B1 (Intermediário)", "B2 (Intermediário Superior)", "C1 (Avançado)"],
        on_change=reset_chat
    )
    
    student_goal = st.text_input(
        "Objetivo da Aula:", 
        "Conversação e correções",
        on_change=reset_chat
    )
    
    if st.button("Reiniciar Conversa"):
        reset_chat()
        st.rerun()

# --- 3. Conexão ---
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

# --- 4. Cérebro da IA (Inicialização Segura) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Se o chat estiver vazio (ou foi resetado), criamos de novo
if st.session_state.chat_session is None:
    
    # --- O SEGREDO ESTÁ AQUI: PROMPT MELHORADO ---
    prompt_do_professor = (
        f"Context: You are a friendly bilingual English Teacher for Brazilian students. "
        f"Student Level: {student_level}. "
        f"Current Goal: {student_goal}. "
        "Instructions: "
        "1. Prioritize English, but ALWAYS explain in Portuguese if the student is A1/A2 or confused. "
        "2. If the student speaks Portuguese, answer in Portuguese explaining the English equivalent. "
        "3. Correct mistakes gently. "
        "4. Keep the conversation flowing with short questions."
    )

    try:
        # Iniciamos a Gemma
        st.session_state.chat_session = client.chats.create(
            model="gemma-3-27b-it",
            config=types.GenerateContentConfig(
                temperature=0.7, 
                max_output_tokens=1000
            ),
            history=[
                types.Content(role="user", parts=[types.Part(text=prompt_do_professor)]),
                types.Content(role="model", parts=[types.Part(text="Entendido! Serei um professor atencioso e usarei português quando necessário.")])
            ]
        )
        
        # Mensagem inicial automática (baseada no nível)
        if len(st.session_state.messages) == 0:
            if "A1" in student_level or "A2" in student_level:
                msg_inicial = "Hello! Eu sou seu professor. Podemos falar em Inglês, mas explicarei em Português se precisar. Let's start?"
            else:
                msg_inicial = "Hello! I'm ready to help you practice. Shall we begin?"
                
            st.session_state.messages.append({"role": "assistant", "content": msg_inicial})
            
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")

# --- 5. Interface do Chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Sua resposta..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Verificação de segurança para não dar o erro NoneType
    if st.session_state.chat_session is not None:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            if st.button("Tentar Reconectar"):
                st.rerun()
    else:
        st.warning("A conexão caiu. Clique em 'Reiniciar Conversa' na barra lateral.")