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

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "guest_images" not in st.session_state:
    st.session_state.guest_images = 0

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ---------------- THEME ----------------
if st.session_state.theme == "dark":
    bg = "#0e0e0e"
    fg = "#ffffff"
    card = "#1e1e1e"
else:
    bg = "#f5f5f5"
    fg = "#000000"
    card = "#ffffff"

# ---------------- GLOBAL CSS ----------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {bg};
    color: {fg};
}}

input, textarea {{
    background-color: {card} !important;
    color: {fg} !important;
}}

.chat-user {{
    background: #1c1c1c;
    color: white;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}}

.chat-bot {{
    background: #2a2a2a;
    color: white;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}}

section[data-testid="stSidebar"] {{
    background-color: #141414;
    color: white;
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

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")

    if st.button("🌗 Dark / Light"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    mode = st.radio(
        "Mod Seç",
        ["💬 Sohbet", "🔍 Araştırma", "🎨 Görsel Üretim"]
    )

    st.markdown("---")

    if not st.session_state.logged_in:
        st.subheader("🔐 Giriş / Kayıt")

        name = st.text_input("Ad (zorunlu)")
        surname = st.text_input("Soyad (isteğe bağlı)")
        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")

        if st.button("Giriş Yap / Kayıt Ol"):
            if not name:
                st.error("Ad zorunlu")
            elif not email or not password:
                st.error("Email ve şifre gerekli")
            else:
                st.session_state.logged_in = True
                st.success(f"Hoş geldin {name} 👋")
                st.rerun()

        st.caption("Hesapsız kullanım: 2 görsel")

    else:
        st.success("Giriş yapıldı ✔️")
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")
    st.markdown("**Burak GPT**\n\nDark Mode • HF • OpenAI")

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Sohbet • Araştırma • Görsel Üretim")

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

    user_input = st.text_input("Bir şey yaz")

    if st.button("Gönder") and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ---------------- RESEARCH ----------------
elif mode == "🔍 Araştırma":
    query = st.text_input("Araştırma konusu yaz")

    if st.button("Araştır"):
        with st.spinner("Bilgi toplanıyor..."):
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Detaylı ve anlaşılır araştırma yap"},
                    {"role": "user", "content": query}
                ]
            )
            st.markdown(response.choices[0].message.content)

# ---------------- IMAGE ----------------
else:
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:

        if not st.session_state.logged_in and st.session_state.guest_images >= 2:
            st.warning("Sınırsız görsel için giriş yap 🔐")
            st.stop()

        progress = st.progress(0, text="Görsel hazırlanıyor...")

        try:
            progress.progress(20, "Model yükleniyor...")
            time.sleep(0.3)

            progress.progress(50, "Görsel oluşturuluyor...")
            image = hf_client.predict(prompt)

            progress.progress(90, "Son dokunuşlar...")
            time.sleep(0.2)

            progress.progress(100, "Tamamlandı ✔️")
            st.image(image, width=320)

            if not st.session_state.logged_in:
                st.session_state.guest_images += 1

        except Exception as e:
            st.error(f"Hata: {e}")
