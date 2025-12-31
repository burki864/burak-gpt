import streamlit as st
import os, json, time
from datetime import datetime
from PIL import Image
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager

# ================= PAGE =================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burakgpt_",
    password=st.secrets.get("COOKIE_SECRET", "BURAK_GPT_SECRET")
)
if not cookies.ready():
    st.stop()

# ================= LOGIN (KALICI) =================
if "user_name" not in st.session_state:
    st.session_state.user_name = cookies.get("username")

if not st.session_state.user_name:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?", placeholder="örn: Burak")

    if st.button("Devam Et") and name.strip():
        cookies["username"] = name.strip()
        cookies.save()
        st.session_state.user_name = name.strip()
        st.rerun()

    st.stop()

# ================= API =================
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN   = st.secrets["HF_TOKEN"]

openai_client = OpenAI(api_key=OPENAI_KEY)

# ================= SESSION / CHATS =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    cid = str(int(time.time()))
    st.session_state.active_chat = cid
    st.session_state.chats[cid] = {
        "title": "Yeni Sohbet",
        "messages": []
    }

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")

    if st.button("🆕 Yeni Sohbet"):
        cid = str(int(time.time()))
        st.session_state.active_chat = cid
        st.session_state.chats[cid] = {
            "title": "Yeni Sohbet",
            "messages": []
        }
        st.rerun()

    st.markdown("---")

    for cid, chat in st.session_state.chats.items():
        if st.button(chat["title"], key=f"chat_{cid}"):
            st.session_state.active_chat = cid
            st.rerun()

    st.markdown("---")
    if st.button("🚪 Çıkış"):
        cookies["username"] = ""
        cookies.save()
        st.session_state.clear()
        st.rerun()

# ================= THEME / CSS =================
st.markdown("""
<style>
.stApp { background:#0e0e0e; color:#fff; }
.chat-user { background:#1c1c1c; padding:12px; border-radius:10px; margin-bottom:8px; }
.chat-bot { background:#2a2a2a; padding:12px; border-radius:10px; margin-bottom:12px; }

.image-frame {
    width:420px;
    height:420px;
    border-radius:14px;
    background:linear-gradient(90deg,#2a2a2a,#3a3a3a,#2a2a2a);
    background-size:400% 400%;
    animation: shimmer 1.4s infinite;
    margin-bottom:10px;
}

@keyframes shimmer {
    0% {background-position:0% 50%}
    100% {background-position:100% 50%}
}

button[kind="primary"] {
    border-radius:50%;
    height:42px;
}
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================
def wants_image(text: str) -> bool:
    triggers = [
        "çiz", "oluştur", "görsel", "resim", "fotoğraf",
        "draw", "image", "create image", "generate image"
    ]
    t = text.lower()
    return any(k in t for k in triggers)

def fix_prompt_tr(user_prompt: str) -> str:
    return f"""
Ultra realistic high quality photograph.

Subject:
{user_prompt}

Style:
photorealistic, correct anatomy, natural proportions,
DSLR photo, cinematic lighting, realistic textures.

Negative prompt:
cartoon, anime, illustration, fantasy, surreal,
deformed, extra limbs, bad anatomy,
low quality, blurry, watermark, text
"""

def generate_image(prompt):
    client = Client(
        "burak12321/burak-gpt-image",
        hf_token=HF_TOKEN
    )
    result = client.predict(prompt=prompt, api_name="/predict")
    if isinstance(result, str):
        return Image.open(result)
    return result

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Gerçek AI • Sohbet + Görsel • Otomatik Algılama")

chat = st.session_state.chats[st.session_state.active_chat]

# ================= CHAT VIEW =================
for m in chat["messages"]:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# ================= INPUT =================
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

col1, col2 = st.columns([12,1])
with col1:
    user_input = st.text_input(
        "",
        placeholder="Bir şey yaz veya görsel iste…",
        label_visibility="collapsed",
        key="input_text"
    )
with col2:
    send = st.button("➤", type="primary")

# ================= SEND =================
if send and user_input.strip():
    chat["messages"].append({"role": "user", "content": user_input})

    # otomatik başlık
    if chat["title"] == "Yeni Sohbet":
        chat["title"] = user_input[:30]

    # input temizle
    st.session_state.input_text = ""

    # -------- IMAGE --------
    if wants_image(user_input):
        st.markdown("<div class='image-frame'></div>", unsafe_allow_html=True)
        img = generate_image(fix_prompt_tr(user_input))
        if img:
            st.image(img, width=420)

    # -------- CHAT --------
    else:
        try:
            res = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=chat["messages"]
            )
            chat["messages"].append({
                "role": "assistant",
                "content": res.output_text
            })
        except Exception:
            chat["messages"].append({
                "role": "assistant",
                "content": "⚠️ Şu an yoğunluk var, tekrar dene."
            })

    # ===== PANEL / LOG HOOK =====
    # log_event(user, chat_id, message, type)

    st.rerun()
