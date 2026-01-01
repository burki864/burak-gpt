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

/* ====== SAYFA ZEMİNİ (STREAMLIT ROOT) ====== */
.stApp {
    background: radial-gradient(circle at top, #1a1a1a, #0b0b0b);
    color: #f2f2f2;
}

/* ÜST BOŞLUKLARI TEMİZLE */
header, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 0 !important;
}

/* ====== CHAT ALANI ====== */
.chat-box {
    height: calc(100vh - 140px);
    overflow-y: auto;
    padding: 20px 24px 120px 24px;
}

/* Scroll */
.chat-box::-webkit-scrollbar {
    width: 6px;
}
.chat-box::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 10px;
}

/* ====== BALONLAR ====== */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin-bottom: 12px;
    border-radius: 16px;
    line-height: 1.5;
    box-shadow: 0 6px 16px rgba(0,0,0,.4);
    animation: fadeIn .15s ease-in;
}

/* USER */
.chat-bubble.user {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    margin-left: auto;
    border-bottom-right-radius: 4px;
}

/* BOT */
.chat-bubble.bot {
    background: #1e1e1e;
    margin-right: auto;
    border-bottom-left-radius: 4px;
}

/* ====== SABİT INPUT BAR ====== */
.input-fixed {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(10,10,10,.97);
    backdrop-filter: blur(10px);
    padding: 14px 24px;
    border-top: 1px solid #222;
    z-index: 9999;
}

/* Input */
.input-fixed input {
    background: #111 !important;
    color: #f2f2f2 !important;
    border-radius: 12px !important;
    border: 1px solid #333 !important;
    padding: 10px 14px !important;
}

/* Button */
.input-fixed button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
    height: 44px;
    font-weight: 600;
}

/* ====== ANİMASYON ====== */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

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
        img = generate_image(txt)
        reply = "🖼️ Görsel hazır" if img else "❌ Görsel üretilemedi"
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat]
        )
        reply = res.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    st.rerun()
