import json
import pandas as pd
import streamlit as st
from google import genai

# --- Carregamento da Base de Conhecimento ---
@st.cache_data
def carregar_dados():
    with open("data/perfil_cliente.json", "r", encoding="utf-8") as f:
        perfil = json.load(f)
    transacoes = pd.read_csv("data/transacoes.csv")
    return perfil, transacoes

perfil, transacoes = carregar_dados()

# --- Montagem do Contexto e System Prompt ---
cliente = perfil["cliente"]
metas_formatadas = "\n".join(
    [
        f"- {m['nome_meta']}: Objetivo R${m['valor_objetivo']:.2f}, "
        f"Poupado R${m['valor_atual_poupado']:.2f}, Prazo: {m['prazo_meses']} meses"
        for m in cliente["metas"]
    ]
)

transacoes_texto = transacoes.to_string(index=False)

SYSTEM_PROMPT = f"""
Você é a Mia, uma mentora financeira motivadora, empática e didática.
O seu objetivo é ajudar a pessoa usuária a organizar o orçamento mensal para atingir as suas metas.

DADOS DA CLIENTE:
Nome: {cliente['nome']}
Renda Mensal: R${cliente['renda_mensal']:.2f}
Perfil de Risco: {cliente['perfil_investidor']}
Metas:
{metas_formatadas}

HISTÓRICO RECENTE DE TRANSAÇÕES:
{transacoes_texto}

REGRAS RÍGIDAS:
1. Baseie-se EXCLUSIVAMENTE nos dados fornecidos acima.
2. Nunca julgue os gastos. Seja sempre encorajadora, empática e prática.
3. NUNCA faça recomendações de investimentos ou ativos específicos.
4. Jamais responda a tópicos fora do âmbito de finanças pessoais e planejamento de metas.
5. Se não souber ou os dados não informarem algo, admita que não tem essa informação.
"""

# --- Interface com Streamlit ---
st.set_page_config(page_title="Mia - Mentora de Metas", page_icon="🎯")
st.title("🎯 Mia, a Mentora de Metas")
st.caption("A sua parceira inteligente para organizar finanças e conquistar sonhos.")

# Menu lateral para a pessoa usuária colocar a própria API Key
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("Insira a sua API Key do Google Gemini:", type="password")
    st.markdown("[Crie a sua API Key gratuita no Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.info("A chave não é salva. Serve apenas para esta sessão ativa.")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": f"Olá, {cliente['nome']}! Sou a Mia, a sua mentora de metas. Como posso ajudar a organizar o seu orçamento hoje?"}
    ]

# Exibe histórico do chat na tela
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Entrada da usuária
if user_input := st.chat_input("Escreva a sua dúvida sobre as suas metas ou gastos..."):
    if not api_key:
        st.error("⚠️ Por favor, insira a sua chave de API no menu lateral para conversar com a Mia.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("A Mia está pensando..."):
                try:
                    # Inicializa o cliente com o novo SDK google-genai
                    client = genai.Client(api_key=api_key)
                    
                    # Junta as regras (System Prompt) com a pergunta atual
                    prompt_completo = f"{SYSTEM_PROMPT}\n\nUsuária: {user_input}\nMia:"
                    
                    # Chama o modelo (gemini-3.1-flash-lite é rápido e gratuito no AI Studio)
                    response = client.models.generate_content(
                        model='gemini-3.1-flash-lite',
                        contents=prompt_completo
                    )
                    resposta = response.text
                    
                    st.write(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                
                except Exception as e:
                    st.error(f"Ocorreu um erro ao conectar com o Gemini: {e}")