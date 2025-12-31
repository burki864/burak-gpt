import streamlit as st
import os, json
from datetime import datetime
from PIL import Image
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager

# ================= PAGE =================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ================= THEME =================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark = st.session_state.theme == "dark"

st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0e0e0e" if dark else "#ffffff"};
    color: {"#ffffff" if dark else "#000000"};
}}
.chat-user {{
    background: {"#1c1c1c" if dark else "#eaeaea"};
    padding:12px;
    border-radius:10px;
    margin-bottom:8px;
}}
.chat-bot {{
    background: {"#2a2a2a" if dark else "#dcdcdc"};
    padding:12px;
    border-radius:10px;
    margin-bottom:12px;
}}
input {{
    background-color: {"#1e1e1e" if dark else "#f2f2f2"} !important;
    color: {"#ffffff" if dark else "#000000"} !important;
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

# ================= USERS =================
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(u):
    with open(USERS_FILE, "w") as f:
        json.dump(u, f, indent=2)

users = load_users()

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

        if name not in users:
            users[name] = {
                "banned": False,
                "deleted": False,
                "last_seen": None
            }
            save_users(users)

        st.rerun()

    st.stop()

# ================= USER CHECK =================
user = st.session_state.user
info = users.get(user)

if not info:
    users[user] = {"banned": False, "deleted": False, "last_seen": None}
    save_users(users)
    info = users[user]

if info.get("deleted"):
    st.error("❌ Hesabın devre dışı bırakıldı")
    st.stop()

if info.get("banned"):
    st.error("🚫 Hesabın banlandı")
    st.stop()

# ================= ONLINE TRACK =================
users[user]["last_seen"] = datetime.utcnow().isoformat()
save_users(users)

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ================= HELPERS =================
def wants_image(t: str) -> bool:
    return any(k in t.lower() for k in [
        "çiz", "resim", "görsel", "image", "draw", "foto"
    ])

def clean_image_prompt(p: str) -> str:
    return f"""
Ultra realistic high quality photograph.

Subject:
{p}

Style:
photorealistic, correct anatomy, cinematic lighting,
DSLR, realistic textures, ultra detail.

Negative prompt:
cartoon, anime, illustration, deformed,
extra limbs, bad anatomy, blurry, watermark, text
"""

def generate_image(prompt):
    c = Client(
        "burak12321/burak-gpt-image",
        hf_token=st.secrets["HF_TOKEN"]
    )
    return c.predict(prompt=prompt, api_name="/predict")

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown(f"👤 **{user}**")

    if st.button("🌙 / ☀️ Tema Değiştir"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    st.markdown("---")

    if user == "Burak":
        ADMIN_URL = "https://burak-gpt-adm1n.streamlit.app"
        st.markdown(
            f"""
            <a href="{ADMIN_URL}" target="_blank">
            <button style="width:100%;padding:10px;border-radius:8px;">
            🛠️ Admin Panel
            </button>
            </a>
            """,
            unsafe_allow_html=True
        )

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Gerçek AI")

# ================= CHAT VIEW =================
for m in st.session_state.chat:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# ================= INPUT =================
col1, col2 = st.columns([10,1])

with col1:
    txt = st.text_input(
        "",
        placeholder="Bir şey yaz veya görsel iste…",
        label_visibility="collapsed",
        key="input_text"
    )

with col2:
    send = st.button("➤")

# ================= SEND =================
if send and txt.strip():
    st.session_state.chat.append({"role": "user", "content": txt})
    st.session_state.input_text = ""

    if wants_image(txt):
        st.info("🎨 Görsel oluşturuluyor…")
        img = generate_image(clean_image_prompt(txt))
        if img:
            st.image(img, width=420)
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.chat
        )
        st.session_state.chat.append({
            "role": "assistant",
            "content": res.output_text
        })

    st.rerun()
