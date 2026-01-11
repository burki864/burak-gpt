import uuid, base64
from io import BytesIO
import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime, timezone, timedelta
from gradio_client import Client

# ================= PAGE =================
st.set_page_config(page_title="BurakGPT", page_icon="🤖", layout="wide")

# ================= SESSION INIT =================
def init_session():
    defaults = {
        "logged_in": False,
        "username": None,
        "user": None,
        "device_id": None,
        "chat": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ================= OPENAI =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= HF CLIENT =================
@st.cache_resource(show_spinner=False)
def get_hf_client():
    return Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])

# ================= DEVICE ID =================
def get_device_id():
    if not st.session_state.device_id:
        st.session_state.device_id = str(uuid.uuid4())
    return st.session_state.device_id

DEVICE_ID = get_device_id()

# ================= DEVICE BAN =================
def device_guard():
    r = supabase.table("banned_devices").select("*").eq("device_id", DEVICE_ID).execute()
    if r.data:
        st.error("🚫 Bu cihaz engellenmiştir.")
        if r.data[0].get("reason"):
            st.info(f"Sebep: {r.data[0]['reason']}")
        st.stop()

device_guard()

# ================= IMAGE HELPER =================
def render_hf_image(result):
    if isinstance(result, dict) and "image" in result:
        return BytesIO(base64.b64decode(result["image"]))
    if isinstance(result, bytes):
        return BytesIO(result)
    return None

# ================= RESET =================
def reset_session():
    st.session_state.clear()
    st.rerun()

# ================= USER GUARD =================
def user_guard(username):
    r = supabase.table("users").select("*").eq("username", username).limit(1).execute()
    if not r.data:
        reset_session()
        return None

    u = r.data[0]

    if u.get("deleted"):
        st.error("🗑️ Bu hesap silinmiştir.")
        reset_session()
        st.stop()

    if u.get("banned"):
        until = u.get("ban_until")
        if until and datetime.fromisoformat(until) < datetime.now(timezone.utc):
            supabase.table("users").update({
                "banned": False,
                "ban_until": None,
                "ban_reason": None
            }).eq("username", username).execute()
        else:
            st.error(f"⛔ Banlısın\n\nSebep: {u.get('ban_reason','-')}")
            st.stop()

    return u

# ================= LOGIN =================
def login_screen():
    st.title("👤 Giriş")
    name = st.text_input("Kullanıcı adı", max_chars=20)

    if st.button("Giriş"):
        name = name.strip().lower()

        if len(name) < 3:
            st.error("❌ En az 3 karakter")
            st.stop()

        try:
            # UPSERT = varsa dokunma, yoksa oluştur
            supabase.table("users").upsert({
                "username": name,
                "banned": False,
                "deleted": False,
                "is_admin": False
            }, on_conflict="username").execute()
        except Exception as e:
            st.error("⚠️ Supabase yazma hatası")
            st.code(str(e))
            st.stop()

        st.session_state.username = name
        st.session_state.logged_in = True
        st.rerun()

# ================= AUTH FLOW =================
if not st.session_state.logged_in:
    login_screen()
    st.stop()

me = user_guard(st.session_state.username)
if me is None:
    login_screen()
    st.stop()

# ================= ADMIN =================
if me.get("is_admin"):
    with st.sidebar.expander("🛠️ Admin Panel"):
        users = supabase.table("users").select("username").execute().data
        target = st.selectbox("Kullanıcı", [u["username"] for u in users])
        reason = st.text_input("Sebep")
        minutes = st.number_input("Ban süresi (dk)", 0, 10080, 0)

        if st.button("⛔ Banla"):
            supabase.table("users").update({
                "banned": True,
                "ban_reason": reason,
                "ban_until": (
                    datetime.now(timezone.utc) + timedelta(minutes=minutes)
                ).isoformat() if minutes else None
            }).eq("username", target).execute()

            supabase.table("banned_devices").insert({
                "device_id": DEVICE_ID,
                "reason": reason
            }).execute()

            st.success("Banlandı")

# ================= CHAT =================
st.markdown("<h1 style='text-align:center'>BurakGPT</h1>", unsafe_allow_html=True)

for m in st.session_state.chat:
    st.markdown(
        f"<div style='padding:10px;margin:6px;border-radius:12px;"
        f"background:{'#1e88e5' if m['role']=='user' else '#ede7f6'};"
        f"color:{'white' if m['role']=='user' else '#222'}'>"
        f"{m['content']}</div>",
        unsafe_allow_html=True
    )

with st.form("chat_form", clear_on_submit=True):
    txt = st.text_input("Mesajın")
    send = st.form_submit_button("Gönder")

if send and txt:
    st.session_state.chat.append({"role": "user", "content": txt})

    if any(k in txt.lower() for k in ["çiz", "resim", "görsel", "image"]):
        try:
            hf = get_hf_client()
            result = hf.predict(prompt=txt, api_name="/generate_image")
            img = render_hf_image(result)
            if img:
                st.image(img, use_container_width=True)
                reply = "🖼️ Görsel oluşturuldu"
            else:
                reply = "⚠️ Görsel gösterilemedi"
        except:
            reply = "❌ Görsel sistemi kapalı"
    else:
        r = openai_client.responses.create(model="gpt-4.1-mini", input=txt)
        reply = r.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
