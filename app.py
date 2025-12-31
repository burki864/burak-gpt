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

# ================= LOGIN =================
if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

if not st.session_state.user:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")

    if st.button("Devam") and name.strip():
        username = name.strip()
        st.session_state.user = username
        cookies["user"] = username
        cookies.save()

        # kullanıcıyı garanti altına al
        supabase.table("users").upsert({
            "username": username,
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

data = res.data if res and isinstance(res.data, list) else []

# kullanıcı yoksa oluştur
if len(data) == 0:
    supabase.table("users").insert({
        "username": user,
        "banned": False,
        "deleted": False,
        "is_online": True,
        "last_seen": datetime.utcnow().isoformat()
    }).execute()
    info = {
        "banned": False,
        "deleted": False
    }
else:
    info = data[0]

# ================= BAN / DELETE =================
if info.get("deleted"):
    st.error("❌ Hesabın devre dışı bırakıldı")
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

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= HELPERS =================
def wants_image(text):
    return any(k in text.lower() for k in ["çiz", "resim", "görsel", "image", "foto"])

def clean_image_prompt(p):
    return f"""
Ultra realistic high quality photograph.

Subject:
{p}

Style:
photorealistic, cinematic lighting, ultra detail.

Negative prompt:
cartoon, anime, illustration, low quality, watermark
"""

def generate_image(prompt):
    client = Client(
        "burak12321/burak-gpt-image",
        hf_token=st.secrets["HF_TOKEN"]
    )
    return client.predict(prompt)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown(f"👤 **{user}**")

    if st.button("🌙 / ☀️ Tema"):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    if user.lower() == "burak":
        st.markdown("""
        <a href="https://burak-gpt-adm1n.streamlit.app" target="_blank">
        <button style="width:100%;padding:10px;border-radius:8px;">
        🛠️ Admin Panel
        </button>
        </a>
        """, unsafe_allow_html=True)

# ================= MAIN =================
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel • Gerçek AI")

for m in st.session_state.chat:
    cls = "chat-user" if m["role"] == "user" else "chat-bot"
    name = "Sen" if m["role"] == "user" else "Burak GPT"
    st.markdown(
        f"<div class='{cls}'><b>{name}:</b> {m['content']}</div>",
        unsafe_allow_html=True
    )

# ================= INPUT =================
c1, c2 = st.columns([10,1])
with c1:
    txt = st.text_input("", placeholder="Bir şey yaz…", label_visibility="collapsed")
with c2:
    send = st.button("➤")

if send and txt.strip():
    st.session_state.chat.append({"role": "user", "content": txt})

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
