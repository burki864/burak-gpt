import uuid, base64
from io import BytesIO
import streamlit as st
from openai import OpenAI
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from datetime import datetime, timezone, timedelta
from gradio_client import Client

# ================= PAGE =================
st.set_page_config(page_title="BurakGPT", page_icon="🤖", layout="wide")

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
    return Client(
        "mrfakename/Z-Image-Turbo",
        token=st.secrets["HF_TOKEN"]
    )

# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="burak_",
    password=st.secrets["COOKIE_SECRET"]
)

if not cookies.ready():
    st.stop()

# ================= DEVICE ID =================
def get_device_id():
    did = cookies.get("device_id")
    if not did:
        did = str(uuid.uuid4())
        cookies["device_id"] = did
        cookies.save()
    return did

DEVICE_ID = get_device_id()

# ================= DEVICE BAN =================
def device_guard():
    try:
        r = supabase.table("banned_devices").select("*").eq("device_id", DEVICE_ID).execute()
    except Exception:
        return
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

# ================= USER GUARD =================
def user_guard(username):
    try:
        r = supabase.table("users").select("*").eq("username", username).limit(1).execute()
    except Exception:
        st.error("⚠️ Kullanıcı doğrulanamadı")
        st.stop()

    if not r.data:
        cookies.clear()
        cookies.save()
        st.session_state.clear()
        return None

    u = r.data[0]

    if u.get("deleted"):
        st.error("🗑️ Bu hesap silinmiştir.")
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
        name = name.strip()
        if len(name) < 3:
            st.error("❌ En az 3 karakter")
            st.stop()

        try:
            r = supabase.table("users").select("username").eq("username", name).execute()
        except Exception:
            st.error("⚠️ Veritabanı hatası")
            st.stop()

        if r.data:
            st.error("❌ Bu kullanıcı adı kullanımda")
            st.stop()

        try:
            supabase.table("users").insert({
                "username": name,
                "banned": False,
                "deleted": False,
                "is_admin": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception:
            st.error("⚠️ Kayıt oluşturulamadı")
            st.stop()

        cookies["v6_user"] = name
        cookies.save()
        st.session_state.user = name
        st.rerun()

# ================= AUTH FLOW =================
if "user" not in st.session_state:
    cookie_user = cookies.get("v6_user")
    if cookie_user:
        st.session_state.user = cookie_user
        st.rerun()
    login_screen()
    st.stop()

me = user_guard(st.session_state.user)
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
if "chat" not in st.session_state:
    st.session_state.chat = []

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
        except Exception:
            reply = "❌ Görsel sistemi kapalı"
    else:
        r = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = r.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
