import time
import requests
import threading
import re
import uuid
import streamlit as st
from openai import OpenAI
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime

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
@keyframes fade {
 0%{opacity:0}10%{opacity:1}
 90%{opacity:1}100%{opacity:0}
}
</style>
""", unsafe_allow_html=True)

def toast(msg):
    st.markdown(f"<div class='toast'>⚠️ {msg}</div>", unsafe_allow_html=True)

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= USERS =================
def get_user(username):
    r = supabase.table("users").select("*").eq("username", username).execute()
    return r.data[0] if r.data else None

def upsert_user(username):
    supabase.table("users").upsert({
        "username": username,
        "banned": False,
        "deleted": False,
        "warning_count": 0,
        "last_seen": datetime.utcnow().isoformat()
    }, on_conflict="username").execute()

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_v5_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= LOGIN CORE (TEK NOKTA) =================
def ensure_login():
    # 1️⃣ v5 cookie
    user = cookies.get("user")
    if user:
        st.session_state.user = user
        upsert_user(user)
        return True

    # 2️⃣ legacy cookie’ler
    for p in ["burak_v4_", "burak_v3_"]:
        legacy = EncryptedCookieManager(prefix=p, password=st.secrets["COOKIE_SECRET"])
        if legacy.ready():
            u = legacy.get("user")
            if u:
                st.session_state.user = u
                cookies["user"] = u
                cookies.save()
                upsert_user(u)
                return True

    return False

# ================= LOGIN UI =================
if "user" not in st.session_state:
    if not ensure_login():
        st.title("👋 Hoş Geldin")
        name = st.text_input("Adın nedir?")
        if st.button("Devam") and name.strip():
            st.session_state.user = name.strip()
            cookies["user"] = name.strip()
            cookies.save()
            upsert_user(name.strip())
            st.rerun()
        st.stop()

user = st.session_state.user
user_db = get_user(user)

if user_db and user_db.get("banned"):
    st.error("🚫 Hesabın banlandı.")
    st.stop()

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

# ================= SESSION =================
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= SIDEBAR =================
st.sidebar.title("💬 Sohbetlerim")

if st.sidebar.button("➕ Yeni Sohbet"):
    new_conversation()
    st.rerun()

for c in get_conversations():
    if st.sidebar.button(c["title"], key=c["id"]):
        st.session_state.conversation_id = c["id"]
        st.session_state.chat = load_messages(c["id"])
        st.rerun()

# ================= MAIN =================
st.markdown("<h1 style='text-align:center'>BurakGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;opacity:.6'>Bugün ne yapalım?</p>", unsafe_allow_html=True)

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

    st.session_state.input = ""  # input temizlenir
    st.rerun()
