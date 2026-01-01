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

# ================= STYLE =================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #1b1b1b, #0f0f0f);
    color: #eaeaea;
}

.chat-box {
    height: 65vh;
    overflow-y: auto;
    padding: 12px;
    border-radius: 14px;
    background: #121212;
    border: 1px solid #222;
}

.chat-bubble {
    padding: 10px 14px;
    border-radius: 14px;
    margin-bottom: 8px;
    max-width: 70%;
    line-height: 1.4;
    word-wrap: break-word;
}

.user {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    margin-left: auto;
    color: white;
}

.bot {
    background: #1f1f1f;
    border: 1px solid #2a2a2a;
    color: #eaeaea;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)
<style>
/* Üst boşluğu öldür */
.block-container {
    padding-top: 2rem !important;
}

/* Chat alanı */
.chat-box {
    height: calc(100vh - 160px);
    overflow-y: auto;
    padding-bottom: 80px;
}

/* Input alanını alta sabitle */
.input-fixed {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: #0f0f0f;
    padding: 12px 24px;
    border-top: 1px solid #222;
    z-index: 999;
}
</style>
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

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= IMAGE =================
def is_image_request(text):
    keys = ["çiz","resim","görsel","image","photo","art","manzara"]
    return any(k in text.lower() for k in keys)

def clean_image_prompt(p):
    return f"Ultra realistic, cinematic lighting, ultra detailed. {p}"

def generate_image(prompt):
    client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])
    result = client.predict(
        prompt=prompt,
        height=768,
        width=768,
        num_inference_steps=9,
        randomize_seed=True,
        api_name="/generate_image"
    )

    if isinstance(result, (list, tuple)) and result:
        img = result[0]
        if isinstance(img, dict) and img.get("url"):
            return img["url"]
        if isinstance(img, str):
            return img
    return None

# ================= CHAT =================
def auto_title(text):
    return " ".join(text.split()[:5]).capitalize()

def create_conversation(username):
    res = supabase.table("conversations").insert({
        "username": username,
        "title": "Yeni sohbet"
    }).execute()
    return res.data[0]["id"]

def load_messages(cid):
    return supabase.table("chat_logs") \
        .select("role,content") \
        .eq("conversation_id", cid) \
        .order("created_at") \
        .execute().data or []

def save_message(username, role, content, cid):
    supabase.table("chat_logs").insert({
        "username": username,
        "conversation_id": cid,
        "role": role,
        "content": content
    }).execute()

# ================= SESSION =================
if "conversation_id" not in st.session_state:
    saved = cookies.get("conversation_id")
    if saved:
        st.session_state.conversation_id = saved
        st.session_state.chat = load_messages(saved)
    else:
        cid = create_conversation(user)
        cookies["conversation_id"] = cid
        cookies.save()
        st.session_state.conversation_id = cid
        st.session_state.chat = []

    st.session_state.last_image = None

# ================= UI =================
st.title("🤖 Burak GPT")

st.markdown("<div class='chat-box'>", unsafe_allow_html=True)

for m in st.session_state.chat:
    cls = "user" if m["role"] == "user" else "bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"""
        <div class="chat-bubble {cls}">
            <b>{name}:</b><br>{m['content']}
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)

# ================= INPUT =================
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():

    if len(st.session_state.chat) == 0:
        supabase.table("conversations").update({
            "title": auto_title(txt)
        }).eq("id", st.session_state.conversation_id).execute()

    st.session_state.chat.append({"role": "user", "content": txt})
    save_message(user, "user", txt, st.session_state.conversation_id)

    if is_image_request(txt):
        img = generate_image(clean_image_prompt(txt))
        reply = "🖼️ Görsel hazır" if img else "❌ Görsel üretilemedi"
    else:
        messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat]

        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=messages
        )
        reply = res.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    save_message(user, "assistant", reply, st.session_state.conversation_id)

    st.rerun()
