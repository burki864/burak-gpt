import streamlit as st
import os
import time
from openai import OpenAI
from gradio_client import Client

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ---------------- THEME STATE ----------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark = st.session_state.theme == "dark"

# ---------------- GLOBAL CSS ----------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0e0e0e" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}

input, textarea {{
    background-color: {"#1e1e1e" if dark else "#f2f2f2"} !important;
    color: {"#ffffff" if dark else "#000000"} !important;
}}

.chat-user {{
    background: {"#1c1c1c" if dark else "#eaeaea"};
    color: {"white" if dark else "black"};
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}}

.chat-bot {{
    background: {"#2a2a2a" if dark else "#dcdcdc"};
    color: {"white" if dark else "black"};
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}}

section[data-testid="stSidebar"] {{
    background-color: {"#141414" if dark else "#f5f5f5"};
    color: {"white" if dark else "black"};
}}
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]
os.environ["HF_TOKEN"] = HF_TOKEN

# ---------------- CLIENTS ----------------
openai_client = OpenAI(api_key=OPENAI_KEY)
hf_client = Client("burak12321/burak-gpt-image")

# ---------------- AUTH STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = {}

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")

    if st.button("🌙 / ☀️ Tema Değiştir"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    mode = st.radio(
        "Mod Seç",
        ["💬 Sohbet", "🎨 Görsel Üretim", "🔍 Araştırma"]
    )

    st.divider()

    if not st.session_state.logged_in:
        st.subheader("🔐 Giriş / Kayıt")

        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")

        if st.button("Giriş Yap"):
            st.session_state.logged_in = True
            st.session_state.user = {"email": email, "name": "Burak"}
            st.success("Giriş başarılı")
            st.rerun()

        st.markdown("---")
        name = st.text_input("Ad")
        surname = st.text_input("Soyad (opsiyonel)")

        if st.button("Kayıt Ol"):
            st.session_state.logged_in = True
            st.session_state.user = {
                "email": email,
                "name": name,
                "surname": surname
            }
            st.success("Kayıt başarılı")
            st.rerun()

    else:
        st.success("👤 Giriş Yapıldı")
        st.markdown(f"**{st.session_state.user.get('name','')}**")
        st.markdown(st.session_state.user.get("email",""))

        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.user = {}
            st.rerun()

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")

# ---------------- CHAT ----------------
if mode == "💬 Sohbet":
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(
                f"<div class='chat-user'><b>Sen:</b> {m['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-bot'><b>Burak GPT:</b> {m['content']}</div>",
                unsafe_allow_html=True
            )

    user_input = st.text_input("Mesaj yaz...")

    if st.button("Gönder") and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ---------------- IMAGE ----------------
elif mode == "🎨 Görsel Üretim":
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:
        progress = st.progress(0, text="Hazırlanıyor...")

        progress.progress(30, "Model yükleniyor")
        time.sleep(0.4)

        progress.progress(60, "Görsel çiziliyor")
        image = hf_client.predict(prompt)

        progress.progress(100, "Tamamlandı")
        st.image(image, width=320)

# ---------------- RESEARCH ----------------
else:
    query = st.text_input("Araştırma konusu yaz")

    if st.button("Araştır"):
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Araştır: {query}"}]
        )
        st.markdown(response.choices[0].message.content)
