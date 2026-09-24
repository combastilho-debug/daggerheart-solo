import streamlit as st
import json
import random
import re
import urllib.parse
from google import genai

# 1. Configuração da página
st.set_page_config(page_title="Daggerheart VTT", page_icon="🗡️")
CHAVE_API = st.secrets["GEMINI_API_KEY"]

# 2. Carrega a ficha
if "hookton" not in st.session_state:
    with open("hookton.json", "r", encoding="utf-8") as arquivo:
        st.session_state.hookton = json.load(arquivo)
    
    st.session_state.hp = st.session_state.hookton['resources']['hp']
    st.session_state.esperanca = st.session_state.hookton['resources']['hope']

agilidade = st.session_state.hookton.get("stats", {}).get("agility", 1)

# 3. Menu Lateral
with st.sidebar:
    st.title("🗡️ Ficha do Herói")
    st.subheader(st.session_state.hookton['name'])
    st.write(f"**Classe:** {st.session_state.hookton['class']}")
    st.write("---")
    st.write(f"❤️ **Vida:** {st.session_state.hp}")
    st.write(f"✨ **Esperança:** {st.session_state.esperanca}")
    st.write(f"🏃 **Agilidade:** +{agilidade}")

# Função mágica atualizada para pescar Imagem E Status!
def processar_resposta_mestre(texto):
    url_imagem = None
    
    # 1. Procura pela tag de IMAGEM
    match_img = re.search(r'\[IMAGEM\](.*)', texto, re.IGNORECASE)
    if match_img:
        # Pega a descrição, limpa espaços e converte para link
        prompt_imagem = match_img.group(1).strip()
        prompt_codificado = urllib.parse.quote(prompt_imagem)
        # Cria a URL com um formato cinemático (800x400)
        semente = random.randint(1, 1000) # Para a imagem não repetir
        url_imagem = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=800&height=400&nologo=true&seed={semente}"
        
        # Apaga a tag de imagem do texto
        texto = re.sub(r'\[IMAGEM\].*', '', texto, flags=re.IGNORECASE).strip()

    # 2. Procura pela tag de STATUS (a que já fizemos antes)
    match_status = re.search(r'\[STATUS\] HP:\s*(\d+)\s*\|\s*ESP:\s*(\d+)', texto, re.IGNORECASE)
    if match_status:
        st.session_state.hp = int(match_status.group(1))
        st.session_state.esperanca = int(match_status.group(2))
        texto = re.sub(r'\[STATUS\].*', '', texto, flags=re.IGNORECASE).strip()

    return texto, url_imagem

# 4. Inicializa o Cérebro da IA
if "chat" not in st.session_state:
    client = genai.Client(api_key=CHAVE_API)
    st.session_state.chat = client.chats.create(model="gemini-2.5-flash")
    
    # Adicionamos a instrução da [IMAGEM] no prompt
    prompt_abertura = f"""
    [SISTEMA: Você é o Mestre de Daggerheart. O herói é {st.session_state.hookton['name']}.
    Vida atual: {st.session_state.hp} | Esperança atual: {st.session_state.esperanca}.
    
    REGRA 1 (STATUS): NO FINAL DE TODA MENSAGEM, escreva: [STATUS] HP: X | ESP: Y
    
    REGRA 2 (IMAGEM): Ocasionalmente, quando um monstro novo aparecer ou o cenário for impactante, crie uma imagem inserindo no final: 
    [IMAGEM] prompt of the scene in dark fantasy style, highly detailed in english
    
    Narre: Hookton em frente à Caverna do Cão D'Água após a explosão. Termine perguntando o que ele faz. 
    INCLUA UMA TAG [IMAGEM] DESTA CAERNA AGORA!]
    """
    resposta = st.session_state.chat.send_message(prompt_abertura)
    
    # Processa as duas tags secretas
    texto_limpo, url_imagem = processar_resposta_mestre(resposta.text)
    
    msg_inicial = {"role": "mestre", "content": texto_limpo}
    if url_imagem:
        msg_inicial["image"] = url_imagem
        
    st.session_state.mensagens = [msg_inicial]

# 5. Exibe o histórico de mensagens (Agora renderizando imagens!)
for msg in st.session_state.mensagens:
    if msg["role"] == "mestre":
        with st.chat_message("assistant", avatar="🧙‍♂️"):
            st.write(msg["content"])
            # Se a mensagem do Mestre tiver uma imagem atrelada, ela aparece aqui!
            if "image" in msg:
                st.image(msg["image"], use_container_width=True)
    else:
        with st.chat_message("user", avatar="🗡️"):
            st.write(msg["content"])

# 6. Caixa de texto para o jogador
acao_jogador = st.chat_input(f"O que {st.session_state.hookton['name']} faz?")

if acao_jogador:
    st.session_state.mensagens.append({"role": "jogador", "content": acao_jogador})
    
    dado_esperanca = random.randint(1, 12)
    dado_medo = random.randint(1, 12)
    total = dado_esperanca + dado_medo + agilidade
    
    if dado_esperanca == dado_medo:
        resultado_tipo = "SUCESSO CRÍTICO"
    elif dado_esperanca > dado_medo:
        resultado_tipo = "COM ESPERANÇA"
    else:
        resultado_tipo = "COM MEDO"
        
    texto_dados = f"🎲 **Rolagem:** Esp ({dado_esperanca}) | Medo ({dado_medo}) | Agi (+{agilidade}) = **Total: {total} ({resultado_tipo})**"
    st.session_state.mensagens.append({"role": "mestre", "content": texto_dados})
    
    prompt_turno = f"Ação: '{acao_jogador}'. Mecânica: {texto_dados}. Narre as consequências, atualize o HP/Esperança e use a tag [STATUS]. Se algo novo e visualmente impactante aparecer, inclua a tag [IMAGEM]."
    
    resposta = st.session_state.chat.send_message(prompt_turno)
    
    # Processa e guarda a nova mensagem com possível imagem
    texto_limpo, url_imagem = processar_resposta_mestre(resposta.text)
    nova_msg = {"role": "mestre", "content": texto_limpo}
    if url_imagem:
        nova_msg["image"] = url_imagem
        
    st.session_state.mensagens.append(nova_msg)
    
    st.rerun()