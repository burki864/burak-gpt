import streamlit as st
import json
import os
from datetime import datetime
from PIL import Image
from gradio_client import Client
from openai import OpenAI

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "chats.json"

# ---------------- STORAGE ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------- SESSION INIT ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

data = load_data()

# ---------------- LOGIN (ONCE) ----------------
if st.session_state.user is None:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir? (boş geçebilirsin)")

    if st.button("Devam Et"):
        user = name.strip() or f"user_{len(data)+1}"
        if user not in data:
            data[user] = {"chats": {}}
            save_data(data)
        st.session_state.user = user
        st.rerun()

    st.stop()

user = st.session_state.user

# ---------------- THEME ----------------
dark = st.session_state.theme == "dark"

st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0f0f0f" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}
.chat-user {{
    background: {"#1e1e1e" if dark else "#f0f0f0"};
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 8px;
}}
.chat-bot {{
    background: {"#2a2a2a" if dark else "#e6e6e6"};
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 12px;
}}
.skeleton {{
    background: linear-gradient(90deg,#2a2a2a,#3a3a3a,#2a2a2a);
    height: 120px;
    border-radius: 12px;
    animation: shimmer 1.5s infinite;
}}
@keyframes shimmer {{
    0% {{background-position:-200px}}
    100% {{background-position:200px}}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- API ----------------
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
hf_client = Client("burak12321/burak-gpt-image")

# ---------------- HELPERS ----------------
def new_chat():
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    data[user]["chats"][chat_id] = {
        "title": "Yeni Sohbet",
        "messages": []
    }
    save_data(data)
    st.session_state.chat_id = chat_id

def auto_title(text):
    return text[:40]

def is_image_prompt(text):
    keywords = ["çiz", "oluştur", "görsel", "resim", "fotoğraf"]
    return any(k in text.lower() for k in keywords)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(f"👤 **{user}**")

    if st.button("🆕 Yeni Sohbet"):
        new_chat()
        st.rerun()

    st.markdown("---")

    chats = data[user]["chats"]
    for cid, chat in sorted(chats.items(), reverse=True):
        if st.button(chat["title"], key=cid):
            st.session_state.chat_id = cid
            st.rerun()

    st.markdown("---")

    if st.button("🌙 / ☀️ Tema"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

# ---------------- CHAT INIT ----------------
if st.session_state.chat_id is None:
    new_chat()

chat = data[user]["chats"][st.session_state.chat_id]

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")

# ---------------- MESSAGES ----------------
for msg in chat["messages"]:
    cls = "chat-user" if msg["role"] == "user" else "chat-bot"
    name = "Sen" if msg["role"] == "user" else "Burak GPT"
    st.markdown(f"<div class='{cls}'><b>{name}:</b> {msg['content']}</div>", unsafe_allow_html=True)

# ---------------- INPUT ----------------
col1, col2 = st.columns([8,1])

with col1:
    user_input = st.text_input("Mesaj yaz…")

with col2:
    image_btn = st.button("🎨")

# ---------------- ACTION ----------------
if user_input:
    chat["messages"].append({"role": "user", "content": user_input})

    if chat["title"] == "Yeni Sohbet":
        chat["title"] = auto_title(user_input)

    save_data(data)

    with st.spinner("Düşünüyorum…"):
        if image_btn or is_image_prompt(user_input):
            st.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
            try:
                img = hf_client.predict(prompt=user_input, api_name="/predict")
                chat["messages"].append({"role": "assistant", "content": "🖼️ Görsel oluşturuldu"})
                st.image(Image.open(img), width=420)
            except:
                chat["messages"].append({"role": "assistant", "content": "❌ Görsel üretilemedi"})
        else:
            res = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=chat["messages"]
            )
            chat["messages"].append({
                "role": "assistant",
                "content": res.output_text
            })

    save_data(data)
    st.rerun()
