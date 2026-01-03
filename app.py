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

# ================= MODELS =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
hf_client = Client("mrfakename/Z-Image-Turbo", token=st.secrets["HF_TOKEN"])

# ================= COOKIES =================
COOKIE_SECRET = st.secrets["COOKIE_SECRET"]

cookies = EncryptedCookieManager(
    prefix="burak_",
    password=COOKIE_SECRET
)

if not cookies.ready():
    st.stop()

# ================= COOKIE + LEGACY SCAN =================
def find_existing_user():
    """
    v1 → v6 dahil eski tüm kullanıcıları
    TEK CookieManager üstünden tarar
    """
    for key in [
        "v6_user",
        "v5_user",
        "v4_user",
        "v3_user",
        "v2_user",
        "v1_user",
        "user"
    ]:
        u = cookies.get(key)
        if u:
            cookies["v6_user"] = u
            cookies.save()
            return u
    return None

# ================= DEVICE ID =================
def get_device_id():
    did = cookies.get("device_id")
    if not did:
        did = str(uuid.uuid4())
        cookies.set("device_id", did)
        cookies.save()
    return did

DEVICE_ID = get_device_id()

# ================= DEVICE BAN GUARD =================
def device_guard():
    r = supabase.table("banned_devices") \
        .select("device_id, reason") \
        .eq("device_id", DEVICE_ID) \
        .execute()

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
    r = supabase.table("users") \
        .select("*") \
        .eq("username", username) \
        .limit(1) \
        .execute()

    if not r.data:
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
if "user" not in st.session_state:

    existing = find_existing_user()
    if existing:
        st.session_state.user = existing
        st.rerun()

    st.title("👤 Giriş")
    name = st.text_input("Kullanıcı adı", max_chars=20)

    if st.button("Giriş"):
        name = name.strip()

        if len(name) < 3:
            st.error("❌ En az 3 karakter")
            st.stop()

        r = supabase.table("users") \
            .select("username") \
            .eq("username", name) \
            .execute()

        if r.data:
            st.error("❌ Bu kullanıcı adı kullanımda")
            st.stop()

        supabase.table("users").insert({
            "username": name,
            "created_at": datetime.utcnow().isoformat(),
            "banned": False,
            "is_admin": False
        }).execute()

        cookies.set("v6_user", name)
        cookies.save()

        st.session_state.user = name
        st.rerun()

    st.stop()

# ================= SESSION USER =================
user = st.session_state.user
me = user_guard(user)

# ================= ADMIN PANEL =================
if me and me.get("is_admin"):
    with st.sidebar.expander("🛠️ Admin Panel"):
        users = supabase.table("users").select("username").execute().data
        target = st.selectbox("Kullanıcı", [u["username"] for u in users])
        reason = st.text_input("Sebep")
        minutes = st.number_input("Ban süresi (dk)", 0, 10080, 0)

        if st.button("⛔ Banla (cihaz kilitli)"):
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

            st.success("Kullanıcı + cihaz banlandı")

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

# ================= INPUT =================
with st.form("chat_form", clear_on_submit=True):
    txt = st.text_input("Mesajın")
    send = st.form_submit_button("Gönder")

# ================= SEND =================
if send and txt:
    st.session_state.chat.append({"role": "user", "content": txt})

    if any(k in txt.lower() for k in ["çiz", "görsel", "resim", "image"]):
        try:
            result = hf_client.predict(prompt=txt, api_name="/generate_image")
            img = render_hf_image(result)
            if img:
                st.image(img, use_container_width=True)
                reply = "🖼️ Görsel oluşturuldu"
            else:
                reply = "⚠️ Görsel var ama gösterilemedi"
        except Exception as e:
            reply = f"❌ Görsel hatası: {e}"
    else:
        r = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = r.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
