import os
import streamlit as st
from datetime import datetime
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client

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
    box-shadow: 0 0 20px rgba(0,198,255,0.55);
}}

.ai-frame img {{
    width:320px;
    border-radius:14px;
    display:block;
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
        user = name.strip()
        st.session_state.user = user
        cookies["user"] = user
        cookies.save()

        supabase.table("users").upsert({
            "username": user,
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

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "last_image" not in st.session_state:
    st.session_state.last_image = None

# ================= HELPERS =================
def wants_image(t):
    return any(k in t.lower() for k in ["çiz", "resim", "görsel", "image", "foto"])

def clean_image_prompt(p):
    return f"""
Ultra realistic high quality photograph.

Subject:
{p}

Style:
photorealistic, cinematic lighting, ultra detail.

Negative prompt:
cartoon, anime, illustration, watermark, low quality
"""

def generate_image(prompt):
    client = Client("burak12321/burak-gpt-image")
    result = client.predict(prompt)
    return result[0] if isinstance(result, list) else result

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Gerçek AI")

# CHAT
for m in st.session_state.chat:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# IMAGE OUTPUT (🔥 RERUN SAFE)
if st.session_state.last_image:
    st.markdown(
        f"""
        <div class="ai-frame">
            <img src="{st.session_state.last_image}">
        </div>
        """,
        unsafe_allow_html=True
    )

# ================= INPUT =================
c1, c2 = st.columns([10,1])
with c1:
    txt = st.text_input("", placeholder="Bir şey yaz…", label_visibility="collapsed")
with c2:
    send = st.button("➤")

if send and txt.strip():
    st.session_state.chat.append({"role":"user","content":txt})

    if wants_image(txt):
        st.info("🎨 Görsel oluşturuluyor…")
        img = generate_image(clean_image_prompt(txt))
        if img:
            st.session_state.last_image = img
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.chat
        )
        st.session_state.chat.append({
            "role":"assistant",
            "content":res.output_text
        })

    st.rerun()
