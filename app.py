import streamlit as st
import os, json
from datetime import datetime
from PIL import Image
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- COOKIES (LOGIN) ----------------
cookies = EncryptedCookieManager(
    prefix="burakgpt_",
    password="CHANGE_THIS_SECRET_123"
)

if not cookies.ready():
    st.stop()

if "user_name" not in st.session_state:
    st.session_state.user_name = cookies.get("username")

# ---------------- LOGIN ----------------
if not st.session_state.user_name:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")

    if st.button("Devam Et") and name.strip():
        cookies["username"] = name.strip()
        cookies.save()
        st.session_state.user_name = name.strip()
        st.rerun()

    st.stop()

# ---------------- API KEYS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN   = st.secrets["HF_TOKEN"]

openai_client = OpenAI(api_key=OPENAI_KEY)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")

    if st.button("🆕 Yeni Sohbet"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🌙 / ☀️ Tema"):
        st.session_state.dark = not st.session_state.get("dark", True)
        st.rerun()

    if st.button("🚪 Çıkış"):
        cookies["username"] = ""
        cookies.save()
        st.session_state.clear()
        st.rerun()

# ---------------- THEME ----------------
dark = st.session_state.get("dark", True)

st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0e0e0e" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}
.chat-user {{
    background: {"#1c1c1c" if dark else "#ededed"};
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}}
.chat-bot {{
    background: {"#2a2a2a" if dark else "#dddddd"};
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}}
.image-frame {{
    width: 420px;
    height: 420px;
    background: linear-gradient(90deg,#2a2a2a,#3a3a3a,#2a2a2a);
    animation: shimmer 1.5s infinite;
    border-radius: 12px;
}}
@keyframes shimmer {{
    0% {{background-position: -400px 0;}}
    100% {{background-position: 400px 0;}}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- HELPERS ----------------
def wants_image(text: str) -> bool:
    triggers = ["çiz", "oluştur", "resim", "görsel", "fotoğraf", "draw", "image"]
    return any(t in text.lower() for t in triggers)

def fix_prompt_tr(user_prompt: str) -> str:
    return f"""
Ultra realistic high quality photograph.

Subject:
{user_prompt}

Style:
photorealistic, real world proportions, correct anatomy,
natural lighting, DSLR photo, sharp focus, realistic textures.

Negative prompt:
cartoon, anime, illustration, fantasy, surreal,
distorted, deformed, extra limbs, bad anatomy,
low quality, blurry, watermark, text
"""

def generate_image(prompt):
    client = Client(
        "burak12321/burak-gpt-image",
        hf_token=HF_TOKEN
    )

    result = client.predict(
        prompt=prompt,
        api_name="/predict"
    )

    if isinstance(result, str):
        return Image.open(result)

    if isinstance(result, Image.Image):
        return result

    return None

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Gerçekçi AI • Sohbet + Görsel")

# ---------------- CHAT HISTORY ----------------
for m in st.session_state.messages:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# ---------------- INPUT ----------------
user_input = st.text_input(
    "",
    placeholder="Bir şey yaz veya görsel iste…",
    label_visibility="collapsed"
)

send = st.button("➤")

if send and user_input.strip():
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # -------- IMAGE AUTO MODE --------
    if wants_image(user_input):
        st.markdown("<div class='image-frame'></div>", unsafe_allow_html=True)
        prompt = fix_prompt_tr(user_input)
        img = generate_image(prompt)
        if img:
            st.image(img, width=420)

    # -------- CHAT MODE --------
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": res.output_text
        })

    st.rerun()
