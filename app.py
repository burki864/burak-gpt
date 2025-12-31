import streamlit as st
import json
import uuid
from datetime import datetime
from openai import OpenAI

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

DATA_FILE = "chats.json"
client = OpenAI()

# ---------------- STORAGE ----------------
def load_chats():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_chats(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------- SESSION ----------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "mode" not in st.session_state:
    st.session_state.mode = "chat"

if "sending" not in st.session_state:
    st.session_state.sending = False

# ---------------- NEW CHAT ----------------
def new_chat():
    cid = str(uuid.uuid4())
    st.session_state.chats[cid] = {
        "title": "Yeni Sohbet",
        "created": datetime.now().isoformat(),
        "messages": []
    }
    st.session_state.chat_id = cid
    save_chats(st.session_state.chats)

if st.session_state.chat_id is None:
    new_chat()

chat = st.session_state.chats[st.session_state.chat_id]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("💬 Sohbetler")

    if st.button("➕ Yeni Sohbet", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()

    for cid, c in st.session_state.chats.items():
        if st.button(c["title"], key=cid, use_container_width=True):
            st.session_state.chat_id = cid
            st.rerun()

    st.divider()
    st.radio("Mod", ["chat", "image"], key="mode")

# ---------------- CHAT UI ----------------
for m in chat["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------------- INPUT BAR ----------------
col_img, col_input, col_send = st.columns([1, 8, 1])

with col_img:
    img_btn = st.button("🖼️")

with col_input:
    user_input = st.text_input(
        "",
        placeholder="Bir şey yaz...",
        label_visibility="collapsed"
    )

with col_send:
    send_btn = st.button("⬆️")

# ---------------- SEND LOGIC ----------------
if send_btn and user_input and not st.session_state.sending:
    st.session_state.sending = True

    chat["messages"].append({
        "role": "user",
        "content": user_input
    })

    if chat["title"] == "Yeni Sohbet":
        chat["title"] = user_input[:30]

    if st.session_state.mode == "chat":
        res = client.responses.create(
            model="gpt-4.1-mini",
            input=user_input
        )
        reply = res.output_text

    else:
        reply = "🖼️ Görsel modu aktif (image pipeline buraya bağlanır)"

    chat["messages"].append({
        "role": "assistant",
        "content": reply
    })

    save_chats(st.session_state.chats)
    st.session_state.sending = False
    st.rerun()
