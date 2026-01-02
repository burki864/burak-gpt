import time
import requests
import threading
import re
import streamlit as st
from openai import OpenAI
from gradio_client import Client
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
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ================= STYLE + TOAST =================
st.markdown("""
<style>
.stApp { background-color:#0b0b0b; color:#f2f2f2; }
.block-container { padding-top:1rem; }

.toast {
    position: fixed;
    bottom: 20px;
    right: -400px;
    background: #1f1f1f;
    color: white;
    padding: 14px 18px;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(0,0,0,.6);
    animation: slidein 0.5s forwards, slideout 0.5s forwards 3s;
    z-index:9999;
}
@keyframes slidein {
    to { right: 20px; }
}
@keyframes slideout {
    to { right: -400px; }
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
        "is_online": True,
        "last_seen": datetime.utcnow().isoformat()
    }, on_conflict="username").execute()

def warn_user(username):
    u = get_user(username)
    count = (u.get("warning_count") or 0) + 1

    if count >= 2:
        supabase.table("users").update({
            "banned": True
        }).eq("username", username).execute()
        return "BAN"

    supabase.table("users").update({
        "warning_count": count
    }).eq("username", username).execute()
    return "WARN"

def save_chat(username, role, content, type_="text"):
    supabase.table("chats").insert({
        "username": username,
        "role": role,
        "content": content,
        "type": type_,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_v5_",  # global reset
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
        st.session_state.user = name.strip()
        cookies["user"] = st.session_state.user
        cookies.save()
        upsert_user(st.session_state.user)
        st.rerun()
    st.stop()

user = st.session_state.user
user_db = get_user(user)

if user_db["banned"]:
    st.markdown("""
    <div style="text-align:center;margin-top:100px">
        <h1>🚫 Hesabın Banlandı</h1>
        <p>Kurallara uymadığın için erişimin kapatıldı.</p>
        <p style="opacity:.6">İletişim: admin@burakgpt</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ================= MODERATION =================
def is_profanity(text):
    text = text.lower()
    patterns = [
        r"\b[a-zçğıöşü]{1,2}k[a-zçğıöşü]{1,3}\b",
        r"\bmal\b", r"\baptal\b",
        r"(.)\1{4,}"  # aaaaa, sssss
    ]
    return any(re.search(p, text) for p in patterns)

def is_spam():
    now = time.time()
    last = st.session_state.get("last_msg", 0)
    st.session_state.last_msg = now
    return now - last < 1.5

# ================= TIME =================
def get_time_reply():
    tr = datetime.now(timezone.utc) + timedelta(hours=3)
    return f"⏰ Saat **{tr.strftime('%H:%M')}** | 📅 {tr.strftime('%d.%m.%Y')}"

def is_time_question(t):
    return any(k in t.lower() for k in ["saat", "kaç", "tarih"])

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

st.title(f"🤖 Burak GPT | {user}")

for m in st.session_state.chat:
    if m["role"] == "user":
        st.markdown(f"**Sen:** {m['content']}")
    else:
        st.markdown(f"**Burak GPT:** {m['content']}")

txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():

    if is_spam():
        toast("Çok hızlı mesaj atıyorsun, yavaşla.")
        if warn_user(user) == "BAN":
            st.rerun()
        st.stop()

    if is_profanity(txt):
        toast("Kötü söz tespit edildi. Tekrarında ban.")
        if warn_user(user) == "BAN":
            st.rerun()
        st.stop()

    st.session_state.chat.append({"role":"user","content":txt})
    save_chat(user, "user", txt)

    if is_time_question(txt):
        reply = get_time_reply()
    else:
        r = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]).responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = r.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    save_chat(user, "assistant", reply)
    st.rerun()
