# 🗡️ Daggerheart VTT - Motor de RPG Solo com IA

Um Virtual Tabletop (VTT) leve, automatizado e focado em narrativa para jogar o sistema **Daggerheart** no modo solo. Construído com Python, Streamlit e alimentado pela inteligência artificial do Google Gemini.

Este projeto atua como um Mestre de Jogo (GM) automatizado que não apenas narra a história, mas também entende e aplica as regras matemáticas do sistema Daggerheart (Esperança, Medo e Agilidade), controla seus status e até ilustra os cenários em tempo real.

## ✨ Funcionalidades

* **🧠 Mestre de IA (Gemini 2.5 Flash):** Narração adaptativa que reage às suas ações e interpreta os resultados dos dados.
* **🎲 Motor de Regras Automático:** Rola 2d12 (Dado de Esperança vs Dado de Medo) + Agilidade em cada turno. Calcula sucessos críticos, sucessos com medo e sucessos com esperança automaticamente.
* **🖼️ Geração Dinâmica de Imagens:** Ilustrações de monstros, NPCs e cenários geradas instantaneamente através do [Pollinations.ai](https://pollinations.ai) diretamente no chat da partida.
* **📝 Ficha de Personagem Integrada:** Jogue com classes predefinidas (Guerreiro, Ladino, Mago) ou crie seu próprio herói do zero. HP e Esperança são atualizados automaticamente na barra lateral.
* **💾 Sistema "Memory Card":** Baixe o seu progresso em um arquivo `.json` e faça o upload mais tarde para continuar a campanha exatamente de onde parou, sem perder o histórico do chat.

## 🚀 Como jogar na Nuvem (Grátis)

Você pode hospedar este jogo gratuitamente usando o **Streamlit Community Cloud**:
1. Faça um fork (cópia) deste repositório no seu GitHub.
2. Acesse [share.streamlit.io](https://share.streamlit.io) e crie um "New app".
3. Aponte para o seu repositório e selecione o arquivo `interface.py`.
4. Em **Advanced settings**, adicione a sua chave do Google Gemini no formato:
   ```toml
   GEMINI_API_KEY = "Sua_Chave_Real_Aqui"
