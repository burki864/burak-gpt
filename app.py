import streamlit as st
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
    initial_sidebar_state="expanded"
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
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}}

.chat-bot {{
    background: {"#2a2a2a" if dark else "#dcdcdc"};
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}}

section[data-testid="stSidebar"] {{
    background-color: {"#141414" if dark else "#f5f5f5"};
}}
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

client = OpenAI(api_key=OPENAI_KEY)

# ---------------- HF IMAGE API ----------------
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def generate_image(prompt):
    try:
        response = requests.post(
            HF_API_URL,
            headers=HF_HEADERS,
            json={"inputs": prompt},
            timeout=120
        )

        if response.status_code != 200:
            st.warning("⚠️ HF API yanıt vermedi")
            return None

        content_type = response.headers.get("content-type", "").lower()

        if "image" not in content_type:
            try:
                error_data = response.json()
                error_message = error_data.get("error", "HF görsel üretim hatası")
            except Exception:
                error_message = "HF bilinmeyen hata"

            st.warning(f"⚠️ Görsel üretilemedi: {error_message}")
            return None

        return Image.open(BytesIO(response.content))

    except Exception as e:
        st.error(f"❌ Görsel üretim hatası: {e}")
        return None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")

    if st.button("🌙 / ☀️ Tema Değiştir"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    mode = st.radio("Mod Seç", ["💬 Sohbet", "🎨 Görsel Üretim", "🔍 Araştırma"])

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Hızlı • Stabil • Güncel API")

# ---------------- CHAT ----------------
if mode == "💬 Sohbet":
    for m in st.session_state.messages:
        role_class = "chat-user" if m["role"] == "user" else "chat-bot"
        name = "Sen" if m["role"] == "user" else "Burak GPT"
        st.markdown(
            f"<div class='{role_class}'><b>{name}:</b> {m['content']}</div>",
            unsafe_allow_html=True
        )

    user_input = st.text_input("Mesaj yaz...")

    if st.button("Gönder") and user_input:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )

        reply = response.output_text

        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
        st.rerun()

# ---------------- IMAGE ----------------
elif mode == "🎨 Görsel Üretim":
    prompt = st.text_input(
        "Görsel açıklaması yaz",
        placeholder="ör: pastel tonlarda çiçekli kumaş deseni"
    )

    if st.button("Görsel Oluştur") and prompt:
        progress = st.progress(0, "Hazırlanıyor...")
        time.sleep(0.3)

        progress.progress(50, "Görsel üretiliyor, biraz sürebilir")
        image = generate_image(prompt)

        progress.progress(100, "Tamamlandı ✔")

        if image:
            st.image(image, width=350)
        else:
            st.info("ℹ️ Bir sorun oluştu, tekrar deneyebilirsin")

# ---------------- RESEARCH ----------------
else:
    query = st.text_input("Araştırma konusu yaz")

    if st.button("Araştır") and query:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f"Araştır: {query}"
        )
        st.markdown(response.output_text)
