import time
import requests
import threading
import streamlit as st
from openai import OpenAI
from gradio_client import Client
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime, timezone, timedelta
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

# ================= STYLE =================
st.markdown("""
<style>
.stApp { background-color:#0b0b0b; color:#f2f2f2; }
.block-container { padding-top:1rem; }
</style>
""", unsafe_allow_html=True)

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= USERS =================
def get_user(username):
    res = supabase.table("users") \
        .select("*") \
        .eq("username", username) \
        .execute()
    return res.data[0] if res.data else None

def upsert_user(username):
    supabase.table("users").upsert({
        "username": username,
        "banned": False,
        "deleted": False,
        "is_online": True,
        "last_seen": datetime.utcnow().isoformat()
    }, on_conflict="username").execute()

def update_last_seen(username):
    supabase.table("users").update({
        "last_seen": datetime.utcnow().isoformat(),
        "is_online": True
    }).eq("username", username).execute()

def save_chat(username, role, content, type_="text"):
    supabase.table("chats").insert({
        "username": username,
        "role": role,
        "content": content,
        "type": type_,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# ================= COOKIES (GLOBAL RESET) =================
cookies = EncryptedCookieManager(
    prefix="burak_v4_",  # 🔥 herkes çıkış
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

        user_db = get_user(username)

        if user_db and user_db["deleted"]:
            st.error("⛔ Bu hesap silinmiş.")
            st.stop()

        if user_db and user_db["banned"]:
            st.error("🚫 Bu hesap banlı.")
            st.stop()

        st.session_state.user = username
        cookies["user"] = username
        cookies.save()

        upsert_user(username)
        st.rerun()

    st.stop()

# ================= USER CHECK =================
user = st.session_state.user
user_db = get_user(user)

if not user_db:
    upsert_user(user)
    user_db = get_user(user)

if user_db["deleted"]:
    st.error("⛔ Hesabın silinmiş.")
    st.stop()

if user_db["banned"]:
    st.error("🚫 Banlandın.")
    st.stop()

update_last_seen(user)

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= TIME / DATE =================
def get_time_reply():
    tr_time = datetime.now(timezone.utc) + timedelta(hours=3)

    days_tr = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı",
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }

    return (
        f"⏰ Saat: **{tr_time.strftime('%H:%M')}**\n\n"
        f"📅 Tarih: **{tr_time.strftime('%d.%m.%Y')}**\n"
        f"📆 Gün: **{days_tr[tr_time.strftime('%A')]}**"
    )


# ================= IMAGE =================
def is_image_request(text):
    keys = ["çiz", "resim", "görsel", "image", "photo", "art", "manzara"]
    return any(k in text.lower() for k in keys)

def generate_image(prompt):
    client = Client(
        "mrfakename/Z-Image-Turbo",
        token=st.secrets["HF_TOKEN"]
    )
    result = client.predict(
        prompt=prompt,
        height=512,
        width=512,
        num_inference_steps=8,
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

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= UI =================
st.title(f"🤖 Burak GPT | {user}")

# ===== CHAT =====
for m in st.session_state.chat:
    if m["role"] == "user":
        st.markdown(f"**Sen:** {m['content']}")
    else:
        if m.get("type") == "image":
            st.image(m["content"], width=300)
        else:
            st.markdown(f"**Burak GPT:** {m['content']}")

# ===== INPUT =====
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():
    st.session_state.chat.append({"role": "user", "content": txt})
    save_chat(user, "user", txt)

    # ⏰ SAAT / TARİH
    if is_time_request(txt):
        reply = get_time_reply()
        st.session_state.chat.append({
            "role": "assistant",
            "content": reply
        })
        save_chat(user, "assistant", reply)
        st.rerun()

    # 🖼️ IMAGE
    if is_image_request(txt):
        img = generate_image(txt)

        if img:
            st.session_state.chat.append({
                "role": "assistant",
                "type": "image",
                "content": img
            })
            save_chat(user, "assistant", img, "image")

            st.session_state.chat.append({
                "role": "assistant",
                "content": "🖼️ Görsel hazır"
            })
            save_chat(user, "assistant", "🖼️ Görsel hazır")
        else:
            st.session_state.chat.append({
                "role": "assistant",
                "content": "❌ Görsel üretilemedi"
            })
            save_chat(user, "assistant", "❌ Görsel üretilemedi")

    # 💬 TEXT
    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = res.output_text

        st.session_state.chat.append({
            "role": "assistant",
            "content": reply
        })
        save_chat(user, "assistant", reply)

    st.rerun()
