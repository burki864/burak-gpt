import streamlit as st
import requests
import os
from PIL import Image
from io import BytesIO

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# DARK MODE + CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0f1117;
    color: #e6e6eb;
    font-family: 'Inter', sans-serif;
}

.main {
    background-color: #0f1117;
}

input, textarea {
    background-color: #1a1d29 !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}

.stButton>button {
    background: linear-gradient(135deg, #6a5cff, #8b7bff);
    color: white;
    border-radius: 14px;
    padding: 0.6rem 1.4rem;
    border: none;
    font-weight: 600;
}

.stButton>button:hover {
    transform: scale(1.02);
    background: linear-gradient(135deg, #7a6cff, #9b8bff);
}

.chat-bubble-user {
    background-color: #1f2333;
    padding: 14px;
    border-radius: 16px;
    margin: 6px 0;
}

.chat-bubble-ai {
    background-color: #141826;
    padding: 14px;
    border-radius: 16px;
    margin: 6px 0;
    border-left: 3px solid #6a5cff;
}

.footer-note {
    opacity: 0.6;
    font-size: 0.85rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown("## 🧠 **BurakGPT**")
st.markdown("Profesyonel yapay zeka • Görsel üretim • Dark mode ⚡")

# --------------------------------------------------
# SECRETS
# --------------------------------------------------
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    st.error("❌ HF_TOKEN bulunamadı. Secrets kısmına eklemen gerekiyor.")
    st.stop()

# --------------------------------------------------
# SIDEBAR (MODE SELECT)
# --------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Mod Seçimi")
    mode = st.radio(
        "BurakGPT modu",
        ["🖼 Görsel Üretim", "💬 Sohbet (yakında)"],
        index=0
    )

    st.markdown("---")
    st.markdown("**Durum:** 🟢 Aktif")
    st.markdown("**Altyapı:** Hugging Face")
    st.markdown("**Tema:** Dark Mode")

# --------------------------------------------------
# IMAGE GENERATION MODE
# --------------------------------------------------
if mode.startswith("🖼"):

    st.markdown("### 🎨 Görsel Üretici")

    prompt = st.text_area(
        "Görseli tarif et",
        placeholder="Cyberpunk İstanbul, neon ışıklar, gece, sinematik, ultra detaylı...",
        height=120
    )

    col1, col2 = st.columns([6,1])
    with col2:
        generate = st.button("🚀 Oluştur")

    if generate and prompt.strip():

        with st.spinner("🧠 BurakGPT düşünüyor, görsel çiziliyor..."):
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}"
            }

            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt},
                timeout=120
            )

            if response.status_code != 200:
                st.error("❌ Görsel üretilemedi. Biraz sonra tekrar dene.")
            else:
                image = Image.open(BytesIO(response.content))
                st.image(image, caption="✨ BurakGPT tarafından üretildi", use_container_width=True)

# --------------------------------------------------
# CHAT PLACEHOLDER
# --------------------------------------------------
else:
    st.markdown("### 💬 Sohbet")
    st.info("Bu mod yakında aktif olacak. BurakGPT öğrenmeye devam ediyor 👀")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("""
<div class="footer-note">
BurakGPT © 2025 • Deneysel Yapay Zeka Platformu
</div>
""", unsafe_allow_html=True)
