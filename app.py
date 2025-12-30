import streamlit as st
import json
import os
import uuid
from datetime import datetime
from openai import OpenAI

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ---------------- FILE ----------------
USER_FILE = "user_data.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"users": {}}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- VISITOR ID (KAÇIŞ YOK) ----------------
if "visitor_id" not in st.session_state:
    st.session_state.visitor_id = str(uuid.uuid4())[:10]

visitor_id = f"visitor_{st.session_state.visitor_id}"

data = load_users()

# ZİYARETÇİ DAHA ÖNCE YOKSA KAYDET
if visitor_id not in data["users"]:
    data["users"][visitor_id] = {
        "name": "Ziyaretçi",
        "visits": 1,
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active": True,
        "banned": False
    }
else:
    data["users"][visitor_id]["visits"] += 1
    data["users"][visitor_id]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

save_users(data)

# ---------------- BAN KONTROL ----------------
if not data["users"][visitor_id]["active"] or data["users"][visitor_id]["banned"]:
    st.error("⛔ Hesabın kapatıldı")
    st.stop()

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("👋 Hoş Geldin")
    name = st.text_input("İsmin (isteğe bağlı)")

    if st.button("Devam Et"):
        if name.strip():
            data = load_users()
            data["users"][visitor_id]["name"] = name.strip()
            save_users(data)

        st.session_state.logged_in = True
        st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(f"👤 **{data['users'][visitor_id]['name']}**")
    st.markdown(f"🆔 `{visitor_id}`")

    if st.button("🚪 Çıkış"):
        st.session_state.logged_in = False
        st.rerun()

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Kaçışsız • Admin kontrollü • Stabil")

# ---------------- CHAT ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    who = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(f"**{who}:** {m['content']}")

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
