import streamlit as st
import os, json
from datetime import datetime
from PIL import Image
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config("Burak GPT", "🤖", "wide")

# ---------- COOKIES ----------
cookies = EncryptedCookieManager(
    prefix="burak_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ---------- USERS ----------
def load_users():
    if not os.path.exists("users.json"):
        return {}
    return json.load(open("users.json","r"))

def save_users(u):
    json.dump(u, open("users.json","w"), indent=2)

users = load_users()

# ---------- LOGIN ----------
if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

if not st.session_state.user:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın")
    if st.button("Devam") and name.strip():
        st.session_state.user = name.strip()
        cookies["user"] = name.strip()
        cookies.save()

        if name not in users:
            users[name] = {"banned":False,"deleted":False}
            save_users(users)

        st.rerun()
    st.stop()

# ---------- BAN CHECK ----------
u = users.get(st.session_state.user, {})
if u.get("deleted"):
    st.error("❌ Hesap devre dışı")
    st.stop()
if u.get("banned"):
    st.error("🚫 Banlandın")
    st.stop()

# ---------- API ----------
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------- SESSION ----------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------- UI ----------
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Gerçek AI")

for m in st.session_state.chat:
    st.markdown(f"**{m['role'].upper()}**: {m['content']}")

def wants_image(t):
    return any(k in t.lower() for k in ["çiz","resim","görsel","image","draw"])

def generate_image(prompt):
    c = Client("burak12321/burak-gpt-image", hf_token=st.secrets["HF_TOKEN"])
    return c.predict(prompt=prompt, api_name="/predict")

txt = st.text_input("Yaz veya görsel iste…")
send = st.button("➤")

if send and txt.strip():
    st.session_state.chat.append({"role":"user","content":txt})

    if wants_image(txt):
        st.info("🎨 Görsel oluşturuluyor")
        img = generate_image(txt)
        st.image(img, width=420)
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

# ---------- ADMIN BUTTON ----------
if st.session_state.user == "Burak":
    st.sidebar.markdown("---")
    if st.sidebar.button("🛠️ Admin Panel"):
        st.switch_page("admin.py")
