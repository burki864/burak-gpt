import time, requests, threading, uuid
import streamlit as st
from openai import OpenAI
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime
from gradio_client import Client

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
st.set_page_config(page_title="BurakGPT", page_icon="🤖", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp { background:#f2f3f7; }

.chat-user {
 background:#1e88e5; color:white;
 padding:12px 16px; border-radius:18px;
 margin:8px 0; max-width:70%;
}
.chat-ai {
 background:#ede7f6; color:#222;
 padding:12px 16px; border-radius:18px;
 margin:8px 0; max-width:70%;
}
.input-box input {
 background:black !important;
 color:white !important;
}
.image-wrap {
 position:relative; display:inline-block;
}
.image-wrap a {
 position:absolute; bottom:10px; right:10px;
 background:#000a; color:white;
 padding:6px 10px; border-radius:8px;
 text-decoration:none; display:none;
}
.image-wrap:hover a { display:block; }
</style>
""", unsafe_allow_html=True)

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= MODELS =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
hf_client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_v5_",
    password=st.secrets["COOKIE_SECRET"]
)
if not cookies.ready():
    st.stop()

# ================= USERS =================
def upsert_user(username):
    r = supabase.table("users").select("username").eq("username", username).execute()
    if not r.data:
        supabase.table("users").insert({
            "username": username,
            "created_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat()
        }).execute()
    else:
        supabase.table("users").update({
            "last_seen": datetime.utcnow().isoformat()
        }).eq("username", username).execute()

# ================= LOGIN =================
if "user" not in st.session_state:
    u = cookies.get("user")
    if u:
        st.session_state.user = u
        upsert_user(u)
    else:
        st.title("👋 Hoş Geldin")
        name = st.text_input("Adın nedir?")
        if st.button("Devam") and name.strip():
            cookies["user"] = name.strip()
            cookies.save()
            st.session_state.user = name.strip()
            upsert_user(name.strip())
            st.rerun()
        st.stop()

user = st.session_state.user

# ================= CONVERSATIONS =================
def new_conversation(title="Yeni Sohbet"):
    cid = str(uuid.uuid4())
    supabase.table("conversations").insert({
        "id": cid,
        "username": user,
        "title": title,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    st.session_state.conversation_id = cid
    st.session_state.chat = []

def get_conversations():
    return supabase.table("conversations") \
        .select("*").eq("username", user) \
        .order("created_at", desc=True).execute().data

def load_messages(cid):
    return supabase.table("chats") \
        .select("*").eq("conversation_id", cid) \
        .order("created_at").execute().data

# ================= SESSION =================
st.session_state.setdefault("conversation_id", None)
st.session_state.setdefault("chat", [])

# ================= SIDEBAR =================
st.sidebar.title("👤 " + user)
st.sidebar.markdown("⚠️ Uyarı sistemi kapalı")
st.sidebar.markdown("⚠️ Ceza sistemi kapalı")

if st.sidebar.button("➕ Yeni Sohbet"):
    new_conversation()
    st.rerun()

for c in get_conversations():
    if st.sidebar.button(c["title"], key=c["id"]):
        st.session_state.conversation_id = c["id"]
        st.session_state.chat = load_messages(c["id"])
        st.rerun()

# ================= MAIN =================
st.markdown("<h1 style='text-align:center'>BurakGPT</h1>", unsafe_allow_html=True)

for m in st.session_state.chat:
    if m.get("type") == "image":
        st.markdown(f"""
        <div class="image-wrap">
            <img src="{m['content']}" width="350">
            <a href="{m['content']}" download>⬇️ İndir</a>
        </div>
        """, unsafe_allow_html=True)
    elif m["role"] == "user":
        st.markdown(f"<div class='chat-user'>🧑 {m['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-ai'>🤖 {m['content']}</div>", unsafe_allow_html=True)

# ================= INPUT =================
with st.form("chat", clear_on_submit=True):
    txt = st.text_input("Mesajın", key="msg")
    send = st.form_submit_button("Gönder")

def is_image(t):
    return any(k in t.lower() for k in ["çiz", "resim", "image", "draw", "görsel"])

if send and txt.strip():

    if not st.session_state.conversation_id:
        title = txt[:30]
        new_conversation(title)

    st.session_state.chat.append({"role":"user","content":txt})
    supabase.table("chats").insert({
        "conversation_id": st.session_state.conversation_id,
        "username": user,
        "role":"user",
        "content":txt,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    if is_image(txt):
        img = hf_client.predict(prompt=txt, api_name="/generate_image")
        url = img[0]["url"] if isinstance(img, list) else img
        st.session_state.chat.append({"role":"assistant","content":url,"type":"image"})
    else:
        try:
            r = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=txt
            )
            reply = r.output_text
        except:
            reply = "⚠️ Geçici olarak cevap veremiyorum."

        st.session_state.chat.append({"role":"assistant","content":reply})

    st.rerun()
