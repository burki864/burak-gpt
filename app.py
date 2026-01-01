import os
import threading
import time
import requests
import streamlit as st
from datetime import datetime
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client

# ================= KEEP AWAKE =================
def keep_awake():
    while True:
        try:
            requests.get("https://burakgpt.streamlit.app/")
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_awake, daemon=True).start()

# ================= PAGE =================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= STYLE =================
st.markdown("""
<style>

/* ===== GENEL ARKA PLAN ===== */
.stApp {
    background-color: #0b0b0b;
    color: #f2f2f2;
}

/* Streamlit üst boşlukları azalt */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

/* ===== CHAT METİNLERİ ===== */
.chat-line {
    margin-bottom: 8px;
    line-height: 1.6;
    font-size: 15px;
}

/* Kullanıcı */
.chat-user {
    color: #60a5fa;
}

/* Bot */
.chat-bot {
    color: #e5e7eb;
}

/* ===== INPUT NORMAL KALSIN ===== */
/* HİÇBİR position:fixed YOK */
/* HİÇBİR override YOK */

</style>
""", unsafe_allow_html=True)
# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= LOGIN =================
if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

if not st.session_state.user:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")
    if st.button("Devam") and name.strip():
        st.session_state.user = name.strip()
        cookies["user"] = st.session_state.user
        cookies.save()
        st.rerun()
    st.stop()

user = st.session_state.user

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= IMAGE =================
def is_image_request(t):
    return any(k in t.lower() for k in ["çiz","resim","görsel","image","photo","art","manzara"])

def generate_image(prompt):
    client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])
    r = client.predict(
        prompt=prompt,
        height=768,
        width=768,
        num_inference_steps=9,
        randomize_seed=True,
        api_name="/generate_image"
    )
    if isinstance(r, (list, tuple)) and r:
        return r[0] if isinstance(r[0], str) else r[0].get("url")
    return None

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= UI =================
st.title("🤖 Burak GPT")

st.markdown("<div class='chat-box'>", unsafe_allow_html=True)

for m in st.session_state.chat:
    cls = "user" if m["role"] == "user" else "bot"
    who = "Sen" if cls == "user" else "Burak GPT"
    st.markdown(
        f"<div class='chat-bubble {cls}'><b>{who}:</b><br>{m['content']}</div>",
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)

# ================= INPUT (SABİT) =================
st.markdown("<div class='input-fixed'>", unsafe_allow_html=True)
col1, col2 = st.columns([8,1])
with col1:
    txt = st.text_input("Mesajın", label_visibility="collapsed")
with col2:
    send = st.button("Gönder")
st.markdown("</div>", unsafe_allow_html=True)

if send and txt.strip():
    st.session_state.chat.append({"role":"user","content":txt})

    if is_image_request(txt):
    img = generate_image(clean_image_prompt(txt))

    if img:
        # 👇 GÖRSELİ CHAT'E EKLE
        st.session_state.chat.append({
            "role": "assistant",
            "content": "[IMAGE]"
        })

        st.session_state.last_image = img
        reply = "🖼️ Görsel hazır"
    else:
        reply = "❌ Görsel üretilemedi"

        )
        reply = res.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    st.rerun()
