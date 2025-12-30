import streamlit as st
import json, os, base64
from datetime import datetime
from io import BytesIO
from PIL import Image
from openai import OpenAI
from gradio_client import Client

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
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

# ---------------- LOGIN ----------------
if st.session_state.user_name is None:
    st.title("👋 Hoş Geldin")
    name_input = st.text_input("Adın nedir?")

    if st.button("Devam Et"):
        data = load_users()
        if name_input.strip() == "":
            data["counter"] += 1
            username = f"user{data['counter']}"
        else:
            username = name_input.strip()

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

# ---------------- API ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
Z_IMAGE_API = st.secrets["Z_IMAGE_API"]

client = OpenAI(api_key=OPENAI_KEY)
z_client = Client(Z_IMAGE_API)

# ---------------- IMAGE FUNC ----------------
def generate_image(prompt):
    try:
        result = z_client.predict(
            prompt,
            1024,
            1024,
            8,
            7.5,
            api_name="/predict"
        )
        return Image.open(result[0])
    except Exception as e:
        st.error(f"Görsel hata: {e}")
        return None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")
    st.write(f"👤 {st.session_state.user_name}")
    mode = st.radio("Mod Seç", ["💬 Sohbet", "🎨 Görsel Üretim"])

    if st.button("🚪 Çıkış"):
        st.session_state.user_name = None
        st.rerun()

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("HF Turbo • Sınırsıza Yakın • GPU Dostu")

# ---------------- CHAT ----------------
if mode == "💬 Sohbet":
    for m in st.session_state.messages:
        who = "🧑‍💻 Sen" if m["role"] == "user" else "🤖 Burak GPT"
        st.markdown(f"**{who}:** {m['content']}")

    user_input = st.text_input("Mesaj yaz")

    if st.button("Gönder") and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": resp.output_text
        })
        st.rerun()

# ---------------- IMAGE ----------------
else:
    prompt = st.text_input("Görsel açıklaması yaz")

    if st.button("Görsel Oluştur") and prompt:
        with st.spinner("⚡ Turbo çiziyor..."):
            img = generate_image(prompt)
            if img:
                st.image(img, use_container_width=True)
