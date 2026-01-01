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
st.set_page_config(page_title="Burak GPT", page_icon="🤖", layout="wide")

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
    background-color: {"#0e0e0e" if dark else "#f5f5f5"};
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

@keyframes pulseGlow {{
    0% {{
        box-shadow: 0 0 6px rgba(180,180,180,0.2);
        opacity: .85;
    }}
    50% {{
        box-shadow: 0 0 22px rgba(220,220,220,0.7);
        opacity: 1;
    }}
    100% {{
        box-shadow: 0 0 6px rgba(180,180,180,0.2);
        opacity: .85;
    }}
}}

.image-frame {{
    display:inline-block;
    padding:14px;
    border-radius:10px;
    background: linear-gradient(135deg,#2b2b2b,#555,#2b2b2b);
    animation: pulseGlow 2.2s infinite;
    margin-top:14px;
}}

.image-frame img {{
    border-radius:6px;
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
        st.session_state.user = name.strip()
        cookies["user"] = st.session_state.user
        cookies.save()

        supabase.table("users").insert({
            "username": st.session_state.user,
            "last_seen": datetime.utcnow().isoformat()
        }).execute()
        st.rerun()

    st.stop()

user = st.session_state.user

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= IMAGE =================
def is_image_request(t):
    return any(k in t.lower() for k in ["çiz","resim","görsel","image","foto","art","manzara"])

def generate_image(prompt):
    client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])
    r = client.predict(prompt=prompt, width=768, height=768, api_name="/generate_image")
    return r[0]["url"] if isinstance(r, list) else None

# ================= GALLERY =================
def save_image(prompt, url):
    supabase.table("image_gallery").insert({
        "username": user,
        "prompt": prompt,
        "image_url": url,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

def load_gallery():
    return supabase.table("image_gallery") \
        .select("id,prompt,image_url") \
        .eq("username", user) \
        .order("created_at", desc=True) \
        .execute().data or []

def delete_image(i):
    supabase.table("image_gallery").delete().eq("id", i).execute()

# ================= SESSION =================
if "conversation_id" not in st.session_state:
    convs = supabase.table("conversations").select("id").eq("username",user).order("created_at",desc=True).execute().data
    if convs:
        st.session_state.conversation_id = convs[0]["id"]
    else:
        st.session_state.conversation_id = supabase.table("conversations").insert({
            "username": user,
            "title": "Yeni sohbet"
        }).execute().data[0]["id"]
    st.session_state.chat = []
    st.session_state.last_image = None

if "open_gallery" not in st.session_state:
    st.session_state.open_gallery = False

# ================= SIDEBAR =================
with st.sidebar:
    if st.button("🌗 Tema Değiştir"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    if st.button("🖼️ Galeri"):
        st.session_state.open_gallery = True

# ================= GALLERY POPUP =================
if st.session_state.open_gallery:
    with st.expander("🖼️ Görsel Galeri", expanded=True):
        imgs = load_gallery()
        if not imgs:
            st.info("Boş")
        else:
            cols = st.columns(3)
            for i,img in enumerate(imgs):
                with cols[i%3]:
                    st.markdown(f"""
                    <div class="image-frame">
                        <img src="{img['image_url']}" width="100%">
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(img["prompt"])
                    if st.button("❌", key=img["id"]):
                        delete_image(img["id"])
                        st.rerun()

        if st.button("Kapat"):
            st.session_state.open_gallery = False
            st.rerun()

# ================= UI =================
st.title("🤖 Burak GPT")

for m in st.session_state.chat:
    cls = "chat-user" if m["role"]=="user" else "chat-bot"
    st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)

if st.session_state.last_image:
    st.markdown(f"""
    <div class="image-frame">
        <img src="{st.session_state.last_image}" width="320">
    </div>
    """, unsafe_allow_html=True)

# ================= INPUT =================
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():
    st.session_state.chat.append({"role":"user","content":txt})

    if is_image_request(txt):
        img = generate_image(txt)
        if img:
            st.session_state.last_image = img
            save_image(txt,img)
            reply = "🖼️ Görsel hazır"
        else:
            reply = "❌ Hata"
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role":"user","content":txt}]
        )
        reply = res.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    st.rerun()
