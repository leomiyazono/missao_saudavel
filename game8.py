# -*- coding: utf-8 -*-
"""
Missão Alimentação Saudável - Streamlit Cloud + Google Sheets
Autor: Leonardo Miyazono
"""

import streamlit as st
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG GOOGLE SHEETS
# =========================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)
GSHEET_CLIENT = gspread.authorize(CREDS)

# COLE AQUI O ID DA SUA PLANILHA
SHEET = GSHEET_CLIENT.open_by_key("13U2gYEMQEhK9rVO67fFgX3lgmOOBBsHbRANxwVcTAH4").worksheet("ranking")

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
if "fase" not in st.session_state: st.session_state.fase = "login"
if "indice" not in st.session_state: st.session_state.indice = 0
if "pontuacao" not in st.session_state: st.session_state.pontuacao = 0
if "inicio_pergunta" not in st.session_state: st.session_state.inicio_pergunta = time.time()

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#ffeaa7,#81ecec); }
</style>
""", unsafe_allow_html=True)
st.markdown("<div style='font-size:70px'>🍎🥦🍌 🍓🍍🥕</div>", unsafe_allow_html=True)
st.title("Missão Alimentação Saudável")

# =========================
# FUNÇÃO AUXILIAR
# =========================
def carregar_ranking():
    dados = SHEET.get_all_records()
    if dados:
        return pd.DataFrame(dados)
    else:
        return pd.DataFrame(columns=["nome","email","senha","pontuacao","idade","consome_fruta"])

# =========================
# LOGIN / CADASTRO
# =========================
if st.session_state.fase == "login":
    opcao = st.radio("Escolha:", ["Login", "Cadastro"])
    nome = st.text_input("Nome")
    email = st.text_input("Email").strip().lower()
    senha = st.text_input("Senha", type="password").strip()

    df_ranking = carregar_ranking()

    if opcao == "Cadastro":
        if st.button("Cadastrar 🚀"):
            if email in df_ranking["email"].values:
                st.error("Email já cadastrado!")
            else:
                novo = {"nome": nome, "email": email, "senha": senha, "pontuacao": 0, "idade": "", "consome_fruta": ""}
                df_ranking = pd.concat([df_ranking, pd.DataFrame([novo])], ignore_index=True)
                SHEET.update([df_ranking.columns.tolist()] + df_ranking.values.tolist())
                st.success("Cadastro realizado!")

    else:  # LOGIN
        if st.button("Entrar 🎮"):
            user = df_ranking[(df_ranking["email"]==email) & (df_ranking["senha"]==senha)]
            if user.empty:
                st.error("Email ou senha incorretos!")
            else:
                st.session_state.nome = user["nome"].values[0]
                st.session_state.email = email
                st.session_state.fase = "jogo"
                st.session_state.indice = 0
                st.session_state.pontuacao = 0
                st.session_state.inicio_pergunta = time.time()
                st.rerun()

# =========================
# JOGO
# =========================
elif st.session_state.fase == "jogo":
    if st.session_state.indice >= len(perguntas):
        st.session_state.fase = "formulario"
        st.rerun()

    pergunta = perguntas[st.session_state.indice]
    st.subheader(f"Pergunta {st.session_state.indice+1}")

    tempo_restante = max(0, 10 - (time.time() - st.session_state.inicio_pergunta))
    st.progress(tempo_restante / 10)
    st.warning(f"⏳ {int(tempo_restante)} segundos")

    if tempo_restante <= 0:
        st.error("Tempo esgotado!")
        time.sleep(1)
        st.session_state.indice += 1
        st.session_state.inicio_pergunta = time.time()
        st.rerun()

    resposta = st.radio(pergunta["pergunta"], pergunta["opcoes"], key=f"radio_{st.session_state.indice}")
    if st.button("Responder"):
        if tempo_restante > 0 and resposta == pergunta["resposta"]:
            st.session_state.pontuacao += int(tempo_restante)
            st.success(f"Ganhou {int(tempo_restante)} pontos! 🎉")
        else:
            st.error("Errado 😢")
        time.sleep(1)
        st.session_state.indice += 1
        st.session_state.inicio_pergunta = time.time()
        st.rerun()

# =========================
# FORMULÁRIO
# =========================
elif st.session_state.fase == "formulario":
    df_ranking = carregar_ranking()
    email_atual = st.session_state.email
    usuario_existente = df_ranking[df_ranking["email"]==email_atual]

    st.success(f"Pontuação final: {st.session_state.pontuacao}")
    idade = st.selectbox("Idade:", ["10-20","21-30","31-40","Mais de 40"])
    consome_fruta = st.radio("Você consome frutas todos os dias?", ["Sim","Não"])

    if st.button("Finalizar 🏁"):
        if usuario_existente.empty:
            novo = {"nome": st.session_state.nome, "email": email_atual, "senha": "",
                    "pontuacao": st.session_state.pontuacao, "idade": idade, "consome_fruta": consome_fruta}
            df_ranking = pd.concat([df_ranking, pd.DataFrame([novo])], ignore_index=True)
        else:
            pont_antiga = usuario_existente["pontuacao"].values[0]
            if st.session_state.pontuacao > pont_antiga:
                df_ranking.loc[df_ranking["email"]==email_atual,
                               ["pontuacao","idade","consome_fruta"]] = [st.session_state.pontuacao,idade,consome_fruta]

        SHEET.update([df_ranking.columns.tolist()] + df_ranking.values.tolist())
        st.session_state.fase = "final"
        st.rerun()

# =========================
# FINAL
# =========================
elif st.session_state.fase == "final":
    st.markdown("<div style='font-size:100px'>🏆</div>", unsafe_allow_html=True)
    st.success("Parabéns!")
    df_ranking = carregar_ranking().sort_values(by="pontuacao", ascending=False)

    st.header("🏅 Ranking dos Campeões")
    for i,row in enumerate(df_ranking.head(5).itertuples(), start=1):
        st.write(f"{i}º 🥇 {row.nome} - {row.pontuacao} pontos")