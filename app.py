import streamlit as st
import time
import requests
import json
import os
from datetime import datetime
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

# ---------------- USER DATA ----------------
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

# ---------------- LOGIN SCREEN ----------------
if st.session_state.user_name is None:
    st.title("👋 Hoş Geldin")
    name_input = st.text_input("Adın nedir?")

    col1, col2 = st.columns(2)

    if col1.button("Devam Et"):
        data = load_users()

        if name_input.strip() == "":
            data["counter"] += 1
            username = f"user{data['counter']}"
        else:
            username = name_input.strip()

        if username not in data["users"]:
            data["users"][username] = {
                "visits": 1,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            data["users"][username]["visits"] += 1
            data["users"][username]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_users(data)
        st.session_state.user_name = username
        st.rerun()

    if col2.button("Bu adımı geç"):
        data = load_users()
        data["counter"] += 1
        username = f"user{data['counter']}"

        data["users"][username] = {
            "visits": 1,
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_users(data)
        st.session_state.user_name = username
        st.rerun()

    st.stop()

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
HF_API_URL = "https://router.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt):
    try:
        response = requests.post(
            HF_API_URL,
            headers=HF_HEADERS,
            json={"inputs": prompt},
            timeout=120
        )

        if "image" not in response.headers.get("content-type", "").lower():
            return None

        return Image.open(BytesIO(response.content))
    except:
        return None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")
    st.markdown(f"👤 **{st.session_state.user_name}**")

    if st.button("🚪 Çıkış Yap"):
        st.session_state.user_name = None
        st.rerun()

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
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": response.output_text}
        )
        st.rerun()

# ---------------- IMAGE ----------------
elif mode == "🎨 Görsel Üretim":
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:
        image = generate_image(prompt)
        if image:
            st.image(image, width=350)
        else:
            st.info("ℹ️ Görsel üretilemedi")

# ---------------- RESEARCH ----------------
else:
    query = st.text_input("Araştırma konusu yaz")
    if st.button("Araştır") and query:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f"Araştır: {query}"
        )
        st.markdown(response.output_text)
