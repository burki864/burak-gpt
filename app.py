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
from io import BytesIO
from PIL import Image

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
@keyframes pulseGlow {
    0% { box-shadow: 0 0 6px rgba(180,180,180,0.25); }
    50% { box-shadow: 0 0 22px rgba(220,220,220,0.7); }
    100% { box-shadow: 0 0 6px rgba(180,180,180,0.25); }
}

.image-frame {
    padding: 14px;
    border-radius: 10px;
    background: linear-gradient(135deg,#1e1e1e,#3a3a3a,#1e1e1e);
    animation: pulseGlow 2.2s infinite ease-in-out;
    width: fit-content;
    margin-top: 12px;
}

.image-frame img {
    border-radius: 6px;
}
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
        check = supabase.table("users").select("username").eq("username", username).execute()
        if check.data:
            st.error("❌ Bu isim alınmış")
            st.stop()

        cookies["user"] = username
        cookies.save()
        st.session_state.user = username

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
    return f"Ultra realistic, cinematic lighting, high detail. {p}"

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

    if not result:
        return None

    img = result[0]

    if isinstance(img, dict) and img.get("url"):
        return img["url"]

    if isinstance(img, str) and img.startswith("http"):
        return img

    if isinstance(img, Image.Image):
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    return None

# ================= GALLERY =================
def save_image(username, prompt, image):
    supabase.table("image_gallery").insert({
        "username": username,
        "prompt": prompt,
        "image_url": image,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

def load_gallery(username):
    return supabase.table("image_gallery") \
        .select("id,image_url,prompt") \
        .eq("username", username) \
        .order("created_at", desc=True) \
        .execute().data or []

# ================= CHAT =================
def create_conversation(username):
    return supabase.table("conversations").insert({
        "username": username,
        "title": "Yeni sohbet"
    }).execute().data[0]["id"]

def load_conversations(username):
    return supabase.table("conversations") \
        .select("id,title") \
        .eq("username", username) \
        .order("created_at", desc=True) \
        .execute().data or []

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
    convs = load_conversations(user)
    if convs:
        st.session_state.conversation_id = convs[0]["id"]
        st.session_state.chat = load_messages(convs[0]["id"])
    else:
        st.session_state.conversation_id = create_conversation(user)
        st.session_state.chat = []
    st.session_state.last_image = None
    st.session_state.open_gallery = False

# ================= SIDEBAR =================
with st.sidebar:
    for c in load_conversations(user):
        if st.button(c["title"], key=c["id"]):
            st.session_state.conversation_id = c["id"]
            st.session_state.chat = load_messages(c["id"])
            st.session_state.last_image = None
            st.rerun()

    if st.button("➕ Yeni Sohbet"):
        st.session_state.conversation_id = create_conversation(user)
        st.session_state.chat = []
        st.session_state.last_image = None
        st.rerun()

    if st.button("🖼️ Galeri"):
        st.session_state.open_gallery = not st.session_state.open_gallery

# ================= GALLERY =================
if st.session_state.open_gallery:
    with st.expander("🖼️ Galeri", expanded=True):
        for img in load_gallery(user):
            st.image(img["image_url"], use_container_width=True)
            st.caption(img["prompt"])

# ================= UI =================
st.title("🤖 Burak GPT")

for m in st.session_state.chat:
    st.markdown(f"**{'Sen' if m['role']=='user' else 'Burak GPT'}:** {m['content']}")

if st.session_state.last_image:
    st.markdown("<div class='image-frame'>", unsafe_allow_html=True)
    st.image(st.session_state.last_image, width=320)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= INPUT =================
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():
    st.session_state.chat.append({"role":"user","content":txt})
    save_message(user,"user",txt,st.session_state.conversation_id)

    if is_image_request(txt):
        img = generate_image(clean_image_prompt(txt))
        if img:
            st.session_state.last_image = img
            save_image(user, txt, img)
            reply = "🖼️ Görsel hazır"
        else:
            reply = "❌ Görsel üretilemedi"
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = res.output_text

    st.session_state.chat.append({"role":"assistant","content":reply})
    save_message(user,"assistant",reply,st.session_state.conversation_id)
    st.rerun()
