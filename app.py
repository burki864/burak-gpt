import streamlit as st
import requests
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
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= API =================
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN   = st.secrets["HF_TOKEN"]
PANEL_API  = st.secrets["PANEL_API"]
PANEL_KEY  = st.secrets["PANEL_KEY"]

openai_client = OpenAI(api_key=OPENAI_KEY)

# ================= BAN CHECK =================
def is_banned(username):
    try:
        r = requests.get(
            f"{PANEL_API}/api/ban-check",
            params={"username": username},
            headers={"Authorization": f"Bearer {PANEL_KEY}"},
            timeout=5
        )
        return r.json().get("banned", False)
    except:
        return False

# ================= LOGIN =================
if "user_name" not in st.session_state:
    st.session_state.user_name = cookies.get("username")

if st.session_state.user_name:
    if is_banned(st.session_state.user_name):
        st.error("🚫 Hesabınız yasaklanmıştır.")
        st.stop()

if not st.session_state.user_name:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")

    if st.button("Devam Et") and name.strip():
        if is_banned(name.strip()):
            st.error("🚫 Bu hesap banlı.")
            st.stop()

        cookies["username"] = name.strip()
        cookies.save()
        st.session_state.user_name = name.strip()
        st.rerun()

    st.stop()

# ================= SESSION =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    cid = str(datetime.now().timestamp())
    st.session_state.active_chat = cid
    st.session_state.chats[cid] = {
        "title": "Yeni Sohbet",
        "messages": []
    }

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")

    if st.button("🆕 Yeni Sohbet"):
        cid = str(datetime.now().timestamp())
        st.session_state.active_chat = cid
        st.session_state.chats[cid] = {
            "title": "Yeni Sohbet",
            "messages": []
        }
        st.rerun()

    st.markdown("---")
    for cid, chat in st.session_state.chats.items():
        if st.button(chat["title"], key=cid):
            st.session_state.active_chat = cid
            st.rerun()

    st.markdown("---")
    if st.button("🚪 Çıkış"):
        cookies["username"] = ""
        cookies.save()
        st.session_state.clear()
        st.rerun()

# ================= STYLE =================
st.markdown("""
<style>
.stApp { background:#0e0e0e; color:white; }
.chat-user { background:#1c1c1c; padding:12px; border-radius:10px; margin-bottom:8px; }
.chat-bot { background:#2a2a2a; padding:12px; border-radius:10px; margin-bottom:12px; }
.image-frame {
    width:420px;height:420px;
    background:linear-gradient(90deg,#2a2a2a,#3a3a3a,#2a2a2a);
    animation:shimmer 1.4s infinite;
    border-radius:14px;
}
@keyframes shimmer {
    0%{background-position:-400px 0}
    100%{background-position:400px 0}
}
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================
def wants_image(text):
    keys = ["çiz", "oluştur", "görsel", "resim", "fotoğraf", "image", "draw"]
    return any(k in text.lower() for k in keys)

def fix_prompt_tr(prompt):
    return f"""
Ultra realistic photograph.

Subject:
{prompt}

Style:
photorealistic, correct anatomy, natural proportions,
DSLR photo, cinematic lighting, realistic textures.

Negative:
cartoon, anime, illustration, fantasy,
deformed, extra limbs, bad anatomy,
low quality, blurry, watermark, text
"""

def generate_image(prompt):
    client = Client("burak12321/burak-gpt-image", hf_token=HF_TOKEN)
    result = client.predict(prompt=prompt, api_name="/predict")
    if isinstance(result, str):
        return Image.open(result)
    return result

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Gerçek Yapay Zeka • Sohbet + Görsel")

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

c1, c2 = st.columns([10,1])
with c1:
    user_input = st.text_input(
        "",
        placeholder="Bir şey yaz veya görsel iste…",
        label_visibility="collapsed",
        key="input_text"
    )
with c2:
    send = st.button("➤")

# ================= SEND =================
if send and user_input.strip():
    chat["messages"].append({"role":"user","content":user_input})

    if chat["title"] == "Yeni Sohbet":
        chat["title"] = user_input[:30]

    st.session_state.input_text = ""

    if wants_image(user_input):
        st.markdown("<div class='image-frame'></div>", unsafe_allow_html=True)
        img = generate_image(fix_prompt_tr(user_input))
        if img:
            st.image(img, width=420)
    else:
        try:
            res = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=chat["messages"]
            )
            chat["messages"].append({
                "role":"assistant",
                "content":res.output_text
            })
        except:
            chat["messages"].append({
                "role":"assistant",
                "content":"⚠️ Sistem yoğun, biraz sonra tekrar dene."
            })

    st.rerun()
