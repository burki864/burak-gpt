import streamlit as st
import os
import time
from openai import OpenAI
from gradio_client import Client

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ---------------- SESSION DEFAULTS ----------------
for key, value in {
    "logged_in": False,
    "user": {},
    "show_login": False,
    "show_register": False,
    "show_profile": False,
    "theme": "dark",
    "messages": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- THEME ----------------
bg = "#0e0e0e" if st.session_state.theme == "dark" else "#ffffff"
text = "#ffffff" if st.session_state.theme == "dark" else "#000000"
box = "#1e1e1e" if st.session_state.theme == "dark" else "#f2f2f2"

st.markdown(f"""
<style>
.stApp {{ background-color:{bg}; color:{text}; }}
input, textarea {{
    background-color:{box} !important;
    color:{text} !important;
}}
section[data-testid="stSidebar"] * {{
    color:{text} !important;
}}
.chat-user {{
    background:{box};
    padding:12px;
    border-radius:10px;
}}
.chat-bot {{
    background:#2a2a2a;
    padding:12px;
    border-radius:10px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]
os.environ["HF_TOKEN"] = HF_TOKEN

# ---------------- CLIENTS ----------------
openai_client = OpenAI(api_key=OPENAI_KEY)
hf_client = Client("burak12321/burak-gpt-image")

# ---------------- TOP BAR ----------------
top_l, top_r = st.columns([9,1])
with top_r:
    if st.session_state.logged_in:
        if st.button("👤"):
            st.session_state.show_profile = True
    else:
        if st.button("Giriş Yap"):
            st.session_state.show_login = True
        if st.button("Kayıt Ol"):
            st.session_state.show_register = True

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Menü")
    mode = st.radio("Mod Seç", ["💬 Sohbet", "🔍 Araştırma", "🎨 Görsel Üretim"])
    st.markdown("---")
    if st.button("🌙 / ☀️ Tema Değiştir"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.markdown("**Burak GPT**")

# ---------------- POPUPS ----------------
if st.session_state.show_login:
    with st.dialog("Giriş Yap"):
        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if email and password:
                st.session_state.logged_in = True
                st.session_state.user = {"email": email, "name": "Kullanıcı"}
                st.session_state.show_login = False
                st.rerun()
            else:
                st.error("Bilgiler eksik")

if st.session_state.show_register:
    with st.dialog("Kayıt Ol"):
        name = st.text_input("Ad *")
        surname = st.text_input("Soyad")
        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")
        if st.button("Kayıt Ol"):
            if not name or not email or not password:
                st.error("Zorunlu alanlar boş")
            else:
                st.session_state.logged_in = True
                st.session_state.user = {
                    "email": email,
                    "name": f"{name} {surname}"
                }
                st.session_state.show_register = False
                st.rerun()

if st.session_state.show_profile:
    with st.dialog("Profil"):
        st.write("👤", st.session_state.user.get("name"))
        st.write("📧", st.session_state.user.get("email"))
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.user = {}
            st.session_state.show_profile = False
            st.rerun()

# ---------------- MAIN ----------------
st.title("🤖 Burak GPT")
st.caption("Sohbet • Araştırma • Görsel Üretim")

# ---------------- CHAT ----------------
if mode == "💬 Sohbet":
    for m in st.session_state.messages:
        css = "chat-user" if m["role"] == "user" else "chat-bot"
        st.markdown(f"<div class='{css}'>{m['content']}</div>", unsafe_allow_html=True)

    msg = st.text_input("Bir şey yaz")
    if st.button("Gönder") and msg:
        st.session_state.messages.append({"role":"user","content":msg})
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        st.session_state.messages.append({
            "role":"assistant",
            "content":res.choices[0].message.content
        })
        st.rerun()

# ---------------- RESEARCH ----------------
elif mode == "🔍 Araştırma":
    q = st.text_input("Araştırma konusu")
    if st.button("Araştır"):
        with st.spinner("Araştırılıyor..."):
            res = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":f"Araştır: {q}"}]
            )
            st.write(res.choices[0].message.content)

# ---------------- IMAGE ----------------
else:
    prompt = st.text_input("Görsel açıklaması yaz")
    if st.button("Görsel Oluştur") and prompt:
        progress = st.progress(0)
        progress.progress(30, "Hazırlanıyor...")
        time.sleep(0.3)
        image = hf_client.predict(prompt)
        progress.progress(100, "Tamamlandı")
        st.image(image, width=320)
