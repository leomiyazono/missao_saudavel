# -*- coding: utf-8 -*-
"""
Missão Alimentação Saudável - Versão Streamlit + Google Sheets
Autor: Leonardo Miyazono
"""

import streamlit as st
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Missão Saudável", page_icon="🍎")

# =========================
# GOOGLE SHEETS
# =========================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)
GSHEET_CLIENT = gspread.authorize(CREDS)
SHEET = GSHEET_CLIENT.open_by_key("COLE_AQUI_O_ID_DA_PLANILHA").worksheet("ranking")

# =========================
# PERGUNTAS
# =========================
perguntas = [
    {"pergunta": "Qual desses é mais saudável?", "opcoes": ["Refrigerante","Suco natural","Salgadinho"], "resposta": "Suco natural"},
    {"pergunta": "Qual alimento ajuda o intestino?", "opcoes": ["Bala","Pão integral","Chocolate"], "resposta": "Pão integral"}
]

# =========================
# SESSION STATE
# =========================
if "indice" not in st.session_state:
    st.session_state.indice = 0
if "pontuacao" not in st.session_state:
    st.session_state.pontuacao = 0
if "inicio_pergunta" not in st.session_state:
    st.session_state.inicio_pergunta = time.time()
if "email" not in st.session_state:
    st.session_state.email = ""

# =========================
# ESTILO INFANTIL
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#ffeaa7,#81ecec);
}
</style>
""", unsafe_allow_html=True)
st.markdown("<div style='font-size:70px'>🍎🥦🍌 🍓🍍🥕</div>", unsafe_allow_html=True)
st.title("Missão Alimentação Saudável")

# =========================
# EMAIL
# =========================
if st.session_state.email == "":
    email = st.text_input("Digite seu email para jogar:").strip().lower()
    if st.button("Começar 🎮") and email != "":
        st.session_state.email = email
        st.session_state.indice = 0
        st.session_state.pontuacao = 0
        st.session_state.inicio_pergunta = time.time()
        st.experimental_rerun()

# =========================
# JOGO
# =========================
elif st.session_state.indice < len(perguntas):
    pergunta = perguntas[st.session_state.indice]
    st.subheader(f"Pergunta {st.session_state.indice + 1}")

    tempo_limite = 10
    tempo_passado = time.time() - st.session_state.inicio_pergunta
    tempo_restante = max(0, tempo_limite - tempo_passado)

    st.progress(tempo_restante / tempo_limite)
    st.warning(f"⏳ {int(tempo_restante)} segundos")

    if tempo_restante <= 0:
        st.error("Tempo esgotado!")
        time.sleep(1)
        st.session_state.indice += 1
        st.session_state.inicio_pergunta = time.time()
        st.experimental_rerun()

    resposta = st.radio(pergunta["pergunta"], pergunta["opcoes"], key=f"radio_{st.session_state.indice}")

    if st.button("Responder"):
        if tempo_restante > 0 and resposta == pergunta["resposta"]:
            pontos = int(tempo_restante)
            st.session_state.pontuacao += pontos
            st.success(f"Ganhou {pontos} pontos! 🎉")
        else:
            st.error("Errado 😢")
        time.sleep(1)
        st.session_state.indice += 1
        st.session_state.inicio_pergunta = time.time()
        st.experimental_rerun()

    time.sleep(0.1)
    st.experimental_rerun()

# =========================
# FORMULÁRIO FINAL + RANKING
# =========================
else:
    st.success(f"Pontuação final: {st.session_state.pontuacao}")

    df_ranking = pd.DataFrame(SHEET.get_all_records())
    email_atual = st.session_state.email
    pontuacao_atual = st.session_state.pontuacao

    usuario_existente = df_ranking[df_ranking["email"] == email_atual]

    idade = st.selectbox("Idade:", ["10-20","21-30","31-40","Mais de 40"])
    consome_fruta = st.radio("Você consome frutas todos os dias?", ["Sim","Não"])

    if st.button("Finalizar 🏁"):
        if usuario_existente.empty:
            # Novo jogador
            df_ranking = df_ranking.append({
                "nome": email_atual.split("@")[0], 
                "email": email_atual, 
                "pontuacao": pontuacao_atual,
                "idade": idade,
                "consome_fruta": consome_fruta
            }, ignore_index=True)
        else:
            # Atualiza se a pontuação for maior
            pont_antiga = usuario_existente["pontuacao"].values[0]
            if pontuacao_atual > pont_antiga:
                idx = usuario_existente.index[0]
                df_ranking.loc[idx, ["pontuacao","idade","consome_fruta"]] = [pontuacao_atual, idade, consome_fruta]

        # Atualiza planilha
        SHEET.clear()
        SHEET.update([df_ranking.columns.values.tolist()] + df_ranking.values.tolist())

        st.success("Ranking atualizado! 🚀")
        st.session_state.indice = 0
        st.session_state.pontuacao = 0
        st.experimental_rerun()

# =========================
# RANKING VISUAL
# =========================
if st.session_state.indice == len(perguntas):
    df_ranking = pd.DataFrame(SHEET.get_all_records())
    df_ranking = df_ranking.sort_values(by="pontuacao", ascending=False)
    st.header("🏅 Ranking dos Campeões")
    for i, row in enumerate(df_ranking.head(5).itertuples(), start=1):
        st.write(f"{i}º 🥇 {row.nome} - {row.pontuacao} pontos")

    st.header("🏅 Ranking dos Campeões")
    for i,row in enumerate(df_ranking.head(5).itertuples(), start=1):

        st.write(f"{i}º 🥇 {row.nome} - {row.pontuacao} pontos")
