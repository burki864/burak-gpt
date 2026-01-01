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
input {{
    background-color: {"#1e1e1e" if dark else "#f2f2f2"} !important;
    color: {"#ffffff" if dark else "#000000"} !important;
}}
.ai-frame {{
    display:inline-block;
    padding:10px;
    margin-top:12px;
    border-radius:18px;
    background: linear-gradient(135deg,#6a5acd,#00c6ff);
    box-shadow: 0 0 22px rgba(0,198,255,0.6);
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

        # ❗ KULLANICI ADI KONTROLÜ
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

# ================= USER CHECK =================
res = supabase.table("users").select("*").eq("username", user).execute()
info = res.data[0] if res.data else {"banned": False, "deleted": False}

if info.get("deleted"):
    st.error("❌ Hesabın devre dışı")
    st.stop()

if info.get("banned"):
    st.error("🚫 Hesabın banlandı")
    st.stop()

# ================= ONLINE UPDATE =================
supabase.table("users").update({
    "is_online": True,
    "last_seen": datetime.utcnow().isoformat()
}).eq("username", user).execute()

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]

# ================= CHAT HELPERS =================
def save_message(username, role, content):
    supabase.table("chat_logs").insert({
        "username": username,
        "role": role,
        "content": content
    }).execute()

def load_last_messages(username, limit=20):
    res = (
        supabase
        .table("chat_logs")
        .select("role,content")
        .eq("username", username)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(res.data)) if res.data else []

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = load_last_messages(user)

if "last_image" not in st.session_state:
    st.session_state.last_image = None

# ================= IMAGE HELPERS =================
def wants_image(t: str) -> bool:
    return any(k in t.lower() for k in ["çiz", "resim", "görsel", "image", "foto"])

def clean_image_prompt(p: str) -> str:
    return f"""
Ultra realistic high quality photograph.

Subject:
{p}

Style:
photorealistic, cinematic lighting, ultra detail.

Negative prompt:
cartoon, anime, illustration, watermark, low quality
"""

def generate_image(prompt: str, progress):
    client = Client("burak12321/burak-gpt-image")
    progress.progress(30)
    result = client.predict(prompt)
    progress.progress(90)
    return result[0] if isinstance(result, list) else result

# ================= UI =================
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Loglu AI")

for m in st.session_state.chat:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

if st.session_state.last_image:
    st.markdown("<div class='ai-frame'>", unsafe_allow_html=True)
    st.image(st.session_state.last_image, width=320)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= INPUT =================
c1, c2 = st.columns([10, 1])
with c1:
    txt = st.text_input("", placeholder="Bir şey yaz…", label_visibility="collapsed")
with c2:
    send = st.button("➤")

if send and txt.strip():
    st.session_state.chat.append({"role": "user", "content": txt})
    save_message(user, "user", txt)

    if wants_image(txt):
        progress = st.progress(0, text="🎨 Görsel hazırlanıyor...")
        img = generate_image(clean_image_prompt(txt), progress)
        progress.progress(100)
        progress.empty()

        if img:
            st.session_state.last_image = img
            reply = "🖼️ Görsel hazır"
        else:
            reply = "❌ Görsel üretilemedi"
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.chat
        )
        reply = res.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    save_message(user, "assistant", reply)

    st.rerun()
