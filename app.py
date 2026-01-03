import time, requests, threading, uuid, base64
from io import BytesIO
import streamlit as st
from openai import OpenAI
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime
from gradio_client import Client
from zoneinfo import ZoneInfo

# ================= PAGE =================
st.set_page_config(page_title="BurakGPT", page_icon="🤖", layout="wide")

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= BAN CHECK =================
def is_banned(username):
    r = supabase.table("banned_users") \
        .select("*") \
        .eq("username", username) \
        .execute()
    return bool(r.data)

def ban_screen():
    st.error("⛔ Bu hesaba erişim engellendi.")
    st.stop()

# ================= MODELS =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
hf_client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_v5_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= USERS =================
def upsert_user(username):
    r = supabase.table("users").select("username").eq("username", username).execute()
    if not r.data:
        supabase.table("users").insert({
            "username": username,
            "created_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat()
        }).execute()
    else:
        supabase.table("users").update({
            "last_seen": datetime.utcnow().isoformat()
        }).eq("username", username).execute()

# ================= LOGIN =================
if "user" not in st.session_state:
    u = cookies.get("user")
    if u:
        if is_banned(u):
            ban_screen()
        st.session_state.user = u
        upsert_user(u)
    else:
        st.title("👋 Hoş Geldin")
        name = st.text_input("Adın nedir?")
        if st.button("Devam") and name.strip():
            if is_banned(name.strip()):
                ban_screen()
            cookies["user"] = name.strip()
            cookies.save()
            st.session_state.user = name.strip()
            upsert_user(name.strip())
            st.rerun()
        st.stop()

user = st.session_state.user

# ================= SESSION DEFAULTS =================
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= CONVERSATIONS =================
def new_conversation(title="Yeni Sohbet"):
    cid = str(uuid.uuid4())
    supabase.table("conversations").insert({
        "id": cid,
        "username": user,
        "title": title,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    st.session_state.conversation_id = cid
    st.session_state.chat = []

def get_conversations():
    return supabase.table("conversations") \
        .select("*").eq("username", user) \
        .order("created_at", desc=True).execute().data

def load_messages(cid):
    return supabase.table("chats") \
        .select("*").eq("conversation_id", cid) \
        .order("created_at").execute().data

# ================= SIDEBAR =================
st.sidebar.title("👤 " + user)
st.sidebar.success("🟢 Ban sistemi aktif")

if st.sidebar.button("➕ Yeni Sohbet"):
    new_conversation()
    st.rerun()

for c in get_conversations():
    if st.sidebar.button(c["title"], key=c["id"]):
        st.session_state.conversation_id = c["id"]
        st.session_state.chat = load_messages(c["id"])
        st.rerun()

# ================= TIME FEATURE =================
def get_time_answer(text):
    if "saat" not in text.lower():
        return None
    now = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%H:%M")
    return f"🕒 Türkiye’de şu an saat **{now}**"

def is_image(t):
    return any(k in t.lower() for k in ["çiz", "resim", "image", "draw", "görsel"])

# ================= MAIN =================
st.markdown("<h1 style='text-align:center'>BurakGPT</h1>", unsafe_allow_html=True)

for m in st.session_state.chat:
    if m["role"] == "user":
        st.markdown(f"<div style='background:#1e88e5;color:white;padding:12px;border-radius:14px;margin:6px'>🧑 {m['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#ede7f6;padding:12px;border-radius:14px;margin:6px'>🤖 {m['content']}</div>", unsafe_allow_html=True)

# ================= INPUT =================
with st.form("chat_form", clear_on_submit=True):
    txt = st.text_input("Mesajın")
    send = st.form_submit_button("Gönder")

# ================= SEND =================
if send and txt.strip():

    if is_banned(user):
        ban_screen()

    if not st.session_state.conversation_id:
        new_conversation(txt[:30])

    st.session_state.chat.append({"role": "user", "content": txt})

    supabase.table("chats").insert({
        "conversation_id": st.session_state.conversation_id,
        "username": user,
        "role": "user",
        "content": txt,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    reply = get_time_answer(txt)

    if not reply and is_image(txt):
        img = hf_client.predict(prompt=txt, api_name="/generate_image")
        reply = "🖼️ Görsel oluşturuldu."

    if not reply:
        try:
            r = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=txt
            )
            reply = r.output_text
        except:
            reply = "⚠️ Şu an cevap veremiyorum."

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
