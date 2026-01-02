import time
import requests
import threading
import re
import uuid
import streamlit as st
from openai import OpenAI
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime, timezone, timedelta

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
st.set_page_config(page_title="Burak GPT", page_icon="🤖", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp { background:#f2f3f7; }
.toast {
 position:fixed; bottom:20px; right:20px;
 background:#333;color:white;padding:14px 18px;
 border-radius:12px; animation:fade 3s forwards;
 z-index:9999;
}
@keyframes fade {0%{opacity:0}10%{opacity:1}90%{opacity:1}100%{opacity:0}}
</style>
""", unsafe_allow_html=True)

def toast(msg):
    st.markdown(f"<div class='toast'>⚠️ {msg}</div>", unsafe_allow_html=True)

# ================= SUPABASE =================
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ================= COOKIES =================
cookies = EncryptedCookieManager(prefix="burak_v5_", password=st.secrets["COOKIE_SECRET"])
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
        cookies["user"] = name.strip()
        cookies.save()
        st.rerun()
    st.stop()

user = st.session_state.user

# ================= CONVERSATIONS =================
def get_conversations():
    return supabase.table("conversations")\
        .select("*")\
        .eq("username", user)\
        .order("created_at", desc=True)\
        .execute().data

def new_conversation():
    cid = str(uuid.uuid4())
    supabase.table("conversations").insert({
        "id": cid,
        "username": user,
        "title": "Yeni Sohbet",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    st.session_state.conversation_id = cid
    st.session_state.chat = []

def load_messages(cid):
    r = supabase.table("chats")\
        .select("*")\
        .eq("conversation_id", cid)\
        .order("created_at")\
        .execute()
    return [{"role":m["role"],"content":m["content"]} for m in r.data]

# ================= SIDEBAR =================
st.sidebar.title("💬 Sohbetlerim")

if st.sidebar.button("➕ Yeni Sohbet"):
    new_conversation()
    st.rerun()

convos = get_conversations()
for c in convos:
    if st.sidebar.button(c["title"], key=c["id"]):
        st.session_state.conversation_id = c["id"]
        st.session_state.chat = load_messages(c["id"])
        st.rerun()

# ================= SESSION =================
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= MAIN =================
st.markdown("<h1 style='text-align:center'>BurakGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;opacity:.7'>Bugün ne yapalım?</p>", unsafe_allow_html=True)

for m in st.session_state.chat:
    st.markdown(f"**{'Sen' if m['role']=='user' else 'BurakGPT'}:** {m['content']}")

txt = st.text_input("Mesajın", key="input")

if st.button("Gönder") and txt.strip():

    if not st.session_state.conversation_id:
        new_conversation()

    st.session_state.chat.append({"role":"user","content":txt})
    supabase.table("chats").insert({
        "conversation_id": st.session_state.conversation_id,
        "username": user,
        "role": "user",
        "content": txt,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    r = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]).responses.create(
        model="gpt-4.1-mini",
        input=txt
    )
    reply = r.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    supabase.table("chats").insert({
        "conversation_id": st.session_state.conversation_id,
        "username": user,
        "role": "assistant",
        "content": reply,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.session_state.input = ""  # ✅ input temizlenir
    st.rerun()
