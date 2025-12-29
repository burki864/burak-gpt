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

# ---------------- GLOBAL DARK CSS ----------------
st.markdown("""
<style>
/* Genel arka plan */
.stApp {
    background-color: #0e0e0e;
    color: #ffffff;
}

/* Yazı input */
input, textarea {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
}

/* Chat balonları */
.chat-user {
    background: #1c1c1c;
    color: white;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}

.chat-bot {
    background: #2a2a2a;
    color: white;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #141414;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

os.environ["HF_TOKEN"] = HF_TOKEN

# ---------------- CLIENTS ----------------
openai_client = OpenAI(api_key=OPENAI_KEY)

hf_client = Client("burak12321/burak-gpt-image")

# ---------------- SIDEBAR MENU ----------------
with st.sidebar:
    st.title("⚙️ Menü")
    mode = st.radio(
        "Mod Seç",
        ["💬 Sohbet", "🎨 Görsel Üretim"]
    )
    st.markdown("---")
    st.markdown("**Burak GPT**\n\nDark Mode • HF • OpenAI")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN UI ----------------
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel Üretim")

# ---------------- CHAT HISTORY ----------------
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

# ---------------- IMAGE MODE ----------------
else:
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:
        progress = st.progress(0, text="Görsel hazırlanıyor...")

        try:
            progress.progress(15, text="Model yükleniyor...")
            time.sleep(0.3)

            progress.progress(35, text="GPU hazırlanıyor...")
            time.sleep(0.3)

            progress.progress(60, text="Görsel oluşturuluyor...")
            image = hf_client.predict(prompt)

            progress.progress(90, text="Son dokunuşlar...")
            time.sleep(0.2)

            progress.progress(100, text="Tamamlandı ✔️")
            st.image(image, width=320)

        except Exception as e:
            st.error(f"Hata: {e}")
