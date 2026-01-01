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

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= SESSION INIT =================
if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

# ================= LOGIN =================
if not st.session_state.user:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")

    if st.button("Devam") and name.strip():
        username = name.strip()

        # 🔍 İSİM KONTROLÜ
        exists = (
            supabase
            .table("users")
            .select("username")
            .eq("username", username)
            .execute()
        )

        if exists.data:
            st.error("❌ Bu isim zaten alınmış, başka bir isim dene")
            st.stop()

        # ✅ KAYIT
        supabase.table("users").insert({
            "username": username,
            "banned": False,
            "deleted": False,
            "is_online": True,
            "last_seen": datetime.utcnow().isoformat()
        }).execute()

        st.session_state.user = username
        cookies["user"] = username
        cookies.save()
        st.rerun()

    st.stop()

# ================= USER GUARANTEED =================
user = st.session_state.user

# ================= USER CHECK =================
res = supabase.table("users").select("*").eq("username", user).execute()
info = res.data[0] if res.data else None

if not info:
    st.error("❌ Kullanıcı bulunamadı")
    st.stop()

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

# ================= SESSION CHAT =================
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
Subject: {p}
Style: photorealistic, cinematic lighting, ultra detail.
Negative prompt: cartoon, anime, illustration, watermark, low quality
"""

def generate_image(prompt: str):
    client = Client("burak12321/burak-gpt-image")
    result = client.predict(prompt)
    if isinstance(result, list) and result:
        return result[0]
    if isinstance(result, str):
        return result
    return None

# ================= UI =================
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Loglu AI")

for m in st.session_state.chat:
    role = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(f"**{role}:** {m['content']}")

# ================= INPUT =================
txt = st.text_input("Mesajın")
if st.button("Gönder") and txt.strip():
    st.session_state.chat.append({"role": "user", "content": txt})
    save_message(user, "user", txt)

    if wants_image(txt):
        reply = "🖼️ Görsel hazır" if generate_image(clean_image_prompt(txt)) else "❌ Görsel üretilemedi"
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.chat
        )
        reply = res.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    save_message(user, "assistant", reply)
    st.rerun()
