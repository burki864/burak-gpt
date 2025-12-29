import streamlit as st
import os
import time
import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"  # menü AÇIK başlar
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

openai_client = OpenAI(api_key=OPENAI_KEY)

# ---------------- HF IMAGE API (HIZLI) ----------------
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def generate_image(prompt):
    response = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={
            "inputs": prompt,
            "options": {"wait_for_model": True}
        },
        timeout=120
    )

    if response.status_code != 200:
        raise Exception("HF görsel üretim hatası")

    return Image.open(BytesIO(response.content))

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")

    # Tema kontrolü (isteğe bağlı)
    if st.checkbox("🌙 / ☀️ Tema Değiştir", value=True):
        if st.button("Temayı Değiştir"):
            st.session_state.theme = "light" if dark else "dark"
            st.rerun()

    mode = st.radio(
        "Mod Seç",
        ["💬 Sohbet", "🎨 Görsel Üretim", "🔍 Araştırma"]
    )

    st.divider()
    st.markdown("**Burak GPT**")
    st.markdown("HF • OpenAI • Dark/Light")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Hızlı • Ücretsiz • Stabil")

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
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
        st.rerun()

# ---------------- IMAGE ----------------
elif mode == "🎨 Görsel Üretim":
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:
        progress = st.progress(0, text="Hazırlanıyor...")

        progress.progress(25, "Model hazırlanıyor")
        time.sleep(0.3)

        progress.progress(55, "Görsel çiziliyor")
        image = generate_image(prompt)

        progress.progress(100, "Tamamlandı ✔")
        st.image(image, width=320)

# ---------------- RESEARCH ----------------
else:
    query = st.text_input("Araştırma konusu yaz")

    if st.button("Araştır"):
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Araştır: {query}"}
            ]
        )
        st.markdown(response.choices[0].message.content)
