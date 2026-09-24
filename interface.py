import streamlit as st
import json
import random
import re
import urllib.parse
import base64
import asyncio
import edge_tts
from google import genai

# ==========================================
# 1. CONFIGURAÇÕES E FUNÇÕES DO SISTEMA
# ==========================================
st.set_page_config(page_title="Daggerheart VTT", page_icon="🗡️", layout="wide")

# --- COSMÉTICA: INJEÇÃO DE CSS ---
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #4A0E17;
        color: white;
        border: 1px solid #FF4B4B;
        border-radius: 8px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #FF4B4B;
        border-color: #4A0E17;
        color: white;
    }
    div[data-testid="metric-container"] {
        background-color: #1E1E24;
        border: 1px solid #444;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- CHAVE E IA ---
CHAVE_API = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=CHAVE_API)

def gerar_audio(texto):
    """Transforma texto em áudio neural com Edge-TTS e converte para base64"""
    async def _gerar():
        # Limpa o texto para a IA não tentar ler os asteriscos do negrito
        texto_limpo = texto.replace('*', '').replace('_', '').replace('#', '')
        # Usa a voz neural masculina em PT-BR (Antonio)
        communicate = edge_tts.Communicate(texto_limpo, "pt-BR-AntonioNeural")
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)

    try:
        # Cria um laço assíncrono isolado para funcionar bem com o Streamlit
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_gerar())
        loop.close()
        return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        return None

def processar_resposta_mestre(texto):
    url_imagem = None
    # Procura e gera a imagem
    match_img = re.search(r'\[IMAGEM\](.*)', texto, re.IGNORECASE)
    if match_img:
        prompt_imagem = match_img.group(1).strip()
        prompt_codificado = urllib.parse.quote(prompt_imagem)
        semente = random.randint(1, 10000)
        url_imagem = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=800&height=400&nologo=true&seed={semente}"
        texto = re.sub(r'\[IMAGEM\].*', '', texto, flags=re.IGNORECASE).strip()

    # Procura e atualiza os status
    match_status = re.search(r'\[STATUS\] HP:\s*(\d+)\s*\|\s*ESP:\s*(\d+)', texto, re.IGNORECASE)
    if match_status:
        st.session_state.hp = int(match_status.group(1))
        st.session_state.esperanca = int(match_status.group(2))
        texto = re.sub(r'\[STATUS\].*', '', texto, flags=re.IGNORECASE).strip()

    return texto, url_imagem

def gerar_resposta_ia(prompt_novo):
    historico = ""
    if "mensagens" in st.session_state:
        for msg in st.session_state.mensagens[-8:]:
            papel = "Mestre" if msg["role"] == "mestre" else "Jogador"
            historico += f"\n{papel}: {msg['content']}"

    prompt_sistema = f"""
    [SISTEMA: Você é o Mestre de Daggerheart. O herói é {st.session_state.heroi['nome']} ({st.session_state.heroi['classe']}).
    Vida atual: {st.session_state.hp} | Esperança atual: {st.session_state.esperanca}.
    
    REGRA 1 (STATUS): NO FINAL DE TODA MENSAGEM SUA, escreva: [STATUS] HP: X | ESP: Y
    REGRA 2 (IMAGEM): Ocasionalmente (para cenas impactantes ou monstros novos), insira no final: [IMAGEM] prompt in english dark fantasy
    
    O QUE JÁ ACONTECEU ANTES:{historico}
    ]
    
    MENSAGEM ATUAL DO JOGADOR:
    {prompt_novo}
    """
    
    resposta = client.models.generate_content(model="gemini-2.5-flash", contents=prompt_sistema)
    return resposta.text

# ==========================================
# 2. MENU LATERAL E NAVEGAÇÃO
# ==========================================
st.sidebar.title("🗡️ Daggerheart VTT")
aba = st.sidebar.radio("Navegação:", ["🎲 Jogar", "📝 Criar Personagem", "💾 Memory Card", "📖 Regras"])

if "heroi" in st.session_state:
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"🛡️ {st.session_state.heroi['nome']}")
    st.sidebar.caption(f"Classe: {st.session_state.heroi['classe']}")
    
    c1, c2 = st.sidebar.columns(2)
    c1.metric(label="❤️ Vida", value=st.session_state.hp)
    c2.metric(label="✨ Esperança", value=st.session_state.esperanca)
    
    st.sidebar.metric(label="🏃 Agilidade", value=f"+{st.session_state.heroi['agilidade']}")

# ==========================================
# 3. CONTEÚDO DAS PÁGINAS
# ==========================================

if aba == "📖 Regras":
    st.header("📖 Como Jogar Daggerheart")
    st.write("Daggerheart é movido pela dualidade entre Esperança e Medo. Toda vez que você faz uma ação arriscada, o sistema rola **2d12** (um Dado de Esperança e um Dado de Medo) e soma o seu modificador (Agilidade).")
    st.markdown("""
    * **Com Esperança:** Se o dado de Esperança for maior, você tem sucesso com benefícios e ganha **+1 Ponto de Esperança**.
    * **Com Medo:** Se o dado de Medo for maior, você pode até ter sucesso, mas sofrerá uma complicação séria ou tomará dano (perdendo HP). O Mestre narra a ameaça.
    * **Sucesso Crítico:** Se os dois dados derem o mesmo número, é um acerto espetacular!
    """)

elif aba == "📝 Criar Personagem":
    st.header("📝 Ficha do Herói")
    opcao_heroi = st.selectbox("Escolha um perfil:", ["Guerreiro (Hookton - Sobrevivência)", "Ladino (Foco em Agilidade)", "Mago (Foco em Esperança)", "Criar do Zero"])
    
    if opcao_heroi.startswith("Guerreiro"):
        nome_def, classe_def, hp_def, esp_def, agi_def = "Hookton", "Guerreiro", 6, 2, 1
    elif opcao_heroi.startswith("Ladino"):
        nome_def, classe_def, hp_def, esp_def, agi_def = "Kael", "Ladino", 5, 2, 3
    elif opcao_heroi.startswith("Mago"):
        nome_def, classe_def, hp_def, esp_def, agi_def = "Elara", "Maga", 4, 4, 0
    else:
        nome_def, classe_def, hp_def, esp_def, agi_def = "", "", 5, 2, 1

    with st.form("form_personagem"):
        nome = st.text_input("Nome do Personagem:", value=nome_def)
        classe = st.text_input("Classe / Subclasse:", value=classe_def)
        col1, col2, col3 = st.columns(3)
        with col1: hp = st.number_input("❤️ Vida Máxima", value=hp_def)
        with col2: esperanca = st.number_input("✨ Esperança Inicial", value=esp_def)
        with col3: agilidade = st.number_input("🏃 Modificador de Agilidade", value=agi_def)
        
        if st.form_submit_button("Começar Campanha"):
            st.session_state.heroi = {"nome": nome, "classe": classe, "agilidade": agilidade}
            st.session_state.hp = hp
            st.session_state.esperanca = esperanca
            st.session_state.mensagens = []
            st.success("Herói criado! Vá para a aba 'Jogar' no menu lateral.")

elif aba == "💾 Memory Card":
    st.header("💾 Salvar e Carregar")
    st.subheader("Fazer Backup (Salvar)")
    if "heroi" in st.session_state and "mensagens" in st.session_state:
        save_data = {
            "heroi": st.session_state.heroi,
            "hp": st.session_state.hp,
            "esperanca": st.session_state.esperanca,
            "mensagens": st.session_state.mensagens
        }
        json_save = json.dumps(save_data, ensure_ascii=False)
        st.download_button("⬇️ Baixar Save (Memory Card)", data=json_save, file_name=f"save_{st.session_state.heroi['nome']}.json", mime="application/json")
    else:
        st.write("Comece uma aventura primeiro para poder salvar o jogo.")
        
    st.markdown("---")
    st.subheader("Continuar Aventura (Carregar)")
    arquivo = st.file_uploader("⬆️ Suba o seu arquivo de save (.json)", type=["json"])
    if arquivo is not None:
        try:
            save_data = json.load(arquivo)
            st.session_state.heroi = save_data["heroi"]
            st.session_state.hp = save_data["hp"]
            st.session_state.esperanca = save_data["esperanca"]
            st.session_state.mensagens = save_data["mensagens"]
            st.success(f"Progresso de {st.session_state.heroi['nome']} carregado! Vá para a aba 'Jogar'.")
        except Exception as e:
            st.error("Arquivo inválido ou corrompido.")

elif aba == "🎲 Jogar":
    if "heroi" not in st.session_state:
        st.warning("⚠️ Você ainda não tem um personagem. Vá no menu lateral em 'Criar Personagem'!")
    else:
        if len(st.session_state.mensagens) == 0:
            with st.spinner("O Mestre está preparando a cena inicial (e gravando a voz)..."):
                prompt_abertura = f"Narre a cena inicial para {st.session_state.heroi['nome']} entrando na Caverna do Cão D'Água. Termine perguntando o que ele faz. INCLUA UMA TAG [IMAGEM] DO CENÁRIO!"
                texto_inicial = gerar_resposta_ia(prompt_abertura)
                texto_limpo, url_imagem = processar_resposta_mestre(texto_inicial)
                
                msg_inicial = {"role": "mestre", "content": texto_limpo}
                if url_imagem: msg_inicial["image"] = url_imagem
                
                audio_b64 = gerar_audio(texto_limpo)
                if audio_b64: msg_inicial["audio"] = audio_b64
                    
                st.session_state.mensagens.append(msg_inicial)
                st.rerun()

        for msg in st.session_state.mensagens:
            if msg["role"] == "mestre":
                with st.chat_message("assistant", avatar="🧙‍♂️"):
                    st.write(msg["content"])
                    if "audio" in msg:
                        st.audio(base64.b64decode(msg["audio"]), format="audio/mp3")
                    if "image" in msg:
                        st.image(msg["image"], use_container_width=True)
            else:
                with st.chat_message("user", avatar="🗡️"):
                    st.write(msg["content"])

        acao_jogador = st.chat_input("O que você faz?")
        if acao_jogador:
            st.session_state.mensagens.append({"role": "jogador", "content": acao_jogador})
            
            agilidade = st.session_state.heroi['agilidade']
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
            
            prompt_turno = f"A ação do jogador foi: '{acao_jogador}'. Mecânica rolada: {texto_dados}. Narre o resultado, aplique perdas de HP se foi Com Medo, ou dê ganhos se foi Com Esperança. Termine com a tag [STATUS]."
            resposta = gerar_resposta_ia(prompt_turno)
            texto_limpo, url_imagem = processar_resposta_mestre(resposta)
            
            nova_msg = {"role": "mestre", "content": texto_limpo}
            if url_imagem: nova_msg["image"] = url_imagem
            
            audio_b64 = gerar_audio(texto_limpo)
            if audio_b64: nova_msg["audio"] = audio_b64
                
            st.session_state.mensagens.append(nova_msg)
            
            st.rerun()
