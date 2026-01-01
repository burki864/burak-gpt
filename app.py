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

# ================= THEME =================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark = st.session_state.theme == "dark"

# ================= STYLE =================
st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0e0e0e" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}
.chat-user {{
    background: {"#1c1c1c" if dark else "#eaeaea"};
    padding:12px;
    border-radius:12px;
    margin-bottom:8px;
}}
.chat-bot {{
    background: {"#2a2a2a" if dark else "#dcdcdc"};
    padding:12px;
    border-radius:12px;
    margin-bottom:12px;
}}
.ai-frame {{
    display:inline-block;
    padding:10px;
    margin-top:12px;
    border-radius:18px;
    background: linear-gradient(135deg,#6a5acd,#00c6ff);
}}
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
        username = name.strip()

        check = supabase.table("users").select("username").eq("username", username).execute()
        if check.data:
            st.error("❌ Bu isim zaten alınmış")
            st.stop()

        st.session_state.user = username
        cookies["user"] = username
        cookies.save()

        supabase.table("users").insert({
            "username": username,
            "banned": False,
            "deleted": False,
            "is_online": True,
            "last_seen": datetime.utcnow().isoformat()
        }).execute()

        st.rerun()

    st.stop()

user = st.session_state.user

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= CONVERSATION HELPERS =================
def auto_title(text):
    return " ".join(text.split()[:5]).capitalize()

def create_conversation(username):
    res = supabase.table("conversations").insert({
        "username": username,
        "title": "Yeni sohbet",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    return res.data[0]["id"]

def load_conversations(username):
    res = supabase.table("conversations") \
        .select("id,title") \
        .eq("username", username) \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []

def load_messages(conv_id):
    res = supabase.table("chat_logs") \
        .select("role,content") \
        .eq("conversation_id", conv_id) \
        .order("created_at") \
        .execute()
    return res.data or []

def delete_conversation(conv_id):
    supabase.table("chat_logs").delete().eq("conversation_id", conv_id).execute()
    supabase.table("conversations").delete().eq("id", conv_id).execute()

def save_message(username, role, content, conv_id):
    supabase.table("chat_logs").insert({
        "username": username,
        "conversation_id": conv_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# ================= SESSION =================
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = create_conversation(user)
    st.session_state.chat = []

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 💬 Sohbetler")

    for c in load_conversations(user):
        col1, col2 = st.columns([8,1])
        if col1.button(c["title"], key=c["id"]):
            st.session_state.conversation_id = c["id"]
            st.session_state.chat = load_messages(c["id"])
            st.rerun()
        if col2.button("🗑️", key=f"del_{c['id']}"):
            delete_conversation(c["id"])
            st.rerun()

    st.divider()

    if st.button("➕ Yeni Sohbet"):
        st.session_state.conversation_id = create_conversation(user)
        st.session_state.chat = []
        st.rerun()

# ================= UI =================
st.title("🤖 Burak GPT")

for m in st.session_state.chat:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# ================= INPUT =================
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():
    if len(st.session_state.chat) == 0:
        supabase.table("conversations").update({
            "title": auto_title(txt)
        }).eq("id", st.session_state.conversation_id).execute()

    st.session_state.chat.append({"role": "user", "content": txt})
    save_message(user, "user", txt, st.session_state.conversation_id)

    res = openai_client.responses.create(
        model="gpt-4.1-mini",
        input=st.session_state.chat
    )
    reply = res.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    save_message(user, "assistant", reply, st.session_state.conversation_id)

    st.rerun()
