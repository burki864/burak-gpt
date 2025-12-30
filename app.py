import streamlit as st
import requests
import json
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
from openai import OpenAI
import base64

# ================= PAGE =================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ================= USER DATA =================
USER_FILE = "user_data.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"counter": 0, "users": {}}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

if "user_name" not in st.session_state:
    st.session_state.user_name = None

# ================= LOGIN =================
if st.session_state.user_name is None:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir? (boş bırakabilirsin)")

    if st.button("Devam Et"):
        data = load_users()

        if name.strip() == "":
            data["counter"] += 1
            username = f"user{data['counter']}"
        else:
            username = name.strip()

        if username not in data["users"]:
            data["users"][username] = {
                "visits": 1,
                "last_seen": str(datetime.now()),
                "active": True,
                "banned": False
            }
        else:
            data["users"][username]["visits"] += 1
            data["users"][username]["last_seen"] = str(datetime.now())

        save_users(data)
        st.session_state.user_name = username
        st.rerun()

    st.stop()

# ================= THEME =================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark = st.session_state.theme == "dark"

st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0f0f0f" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}
input, textarea {{
    background-color: {"#1e1e1e" if dark else "#f2f2f2"} !important;
    color: {"#ffffff" if dark else "#000000"} !important;
}}
.chat-user {{
    background:#2a2a2a; padding:12px; border-radius:10px; margin-bottom:6px;
}}
.chat-bot {{
    background:#1c1c1c; padding:12px; border-radius:10px; margin-bottom:10px;
}}
</style>
""", unsafe_allow_html=True)

# ================= SECRETS =================
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
Z_IMAGE_API = st.secrets["Z_IMAGE_API"]

client = OpenAI(api_key=OPENAI_KEY)

# ================= PROMPT FIX =================
def fix_prompt_tr(text):
    return f"""
Ultra realistic photo.

Subject:
{text}

Style:
realistic photography, correct anatomy, natural lighting,
cinematic, DSLR, sharp focus, real world.

Negative:
cartoon, anime, illustration, surreal, fantasy, deformed,
extra limbs, bad anatomy, text, watermark, low quality
"""

# ================= IMAGE =================
def generate_image(prompt):
    payload = {
        "data": [
            prompt,
            1024,
            1024,
            20,
            7.5
        ]
    }

    r = requests.post(Z_IMAGE_API, json=payload, timeout=180)

    if r.status_code != 200:
        st.error("❌ Görsel API hata")
        return None

    img_b64 = r.json()["data"][0].split(",")[1]
    img_bytes = base64.b64decode(img_b64)
    return Image.open(BytesIO(img_bytes))

# ================= SIDEBAR =================
with st.sidebar:
    st.title("⚙️ Menü")
    st.markdown(f"👤 **{st.session_state.user_name}**")

    if st.button("🌙 / ☀️ Tema"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    if st.button("🚪 Çıkış"):
        st.session_state.user_name = None
        st.rerun()

    mode = st.radio("Mod", ["💬 Sohbet", "🎨 Görsel"])

# ================= SESSION =================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Basit Türkçe → Stabil Yapay Zeka")

# ================= CHAT =================
if mode == "💬 Sohbet":
    for m in st.session_state.messages:
        cls = "chat-user" if m["role"] == "user" else "chat-bot"
        name = "Sen" if m["role"] == "user" else "Burak GPT"
        st.markdown(
            f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
            unsafe_allow_html=True
        )

    msg = st.text_input("Mesaj yaz")

    if st.button("Gönder") and msg:
        st.session_state.messages.append({"role": "user", "content": msg})

        res = client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": res.output_text}
        )
        st.rerun()

# ================= IMAGE =================
else:
    prompt = st.text_input("Görseli basit Türkçe anlat")

    if st.button("Görsel Oluştur") and prompt:
        img = generate_image(fix_prompt_tr(prompt))
        if img:
            st.image(img, width=400)
