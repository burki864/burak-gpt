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

COOKIE_VERSIONS = [
    "v1",
    "v2",
    "v3",
    "v4",
    "v5",
    "v6",
]

# 🔒 TEK CookieManager (component ÇAKIŞMASI YOK)
cookies = EncryptedCookieManager(
    prefix="burak_",
    password=COOKIE_SECRET
)

if not cookies.ready():
    st.stop()


def find_existing_user():
    """
    v1 → v6 tüm cookie'leri kontrol eder
    bulursa v6_user olarak migrate eder
    """
    for v in COOKIE_VERSIONS:
        key = f"{v}_user"
        user = cookies.get(key)
        if user:
            # 🔁 v6'ya taşı
            cookies["v6_user"] = user
            cookies.save()
            return user
    return None
# ================= IMAGE HELPER =================
def render_hf_image(result):
    if isinstance(result, dict) and "image" in result:
        return BytesIO(base64.b64decode(result["image"]))
    if isinstance(result, bytes):
        return BytesIO(result)
    return None

# ================= USER GUARD =================
def user_guard(username):
    r = supabase.table("users").select("*").eq("username", username).limit(1).execute()
    if not r.data:
        return None

    u = r.data[0]

    if u.get("deleted"):
        st.error("🗑️ Bu hesap silinmiştir.")
        st.stop()

    if u.get("banned"):
        until = u.get("ban_until")
        if until:
            if datetime.fromisoformat(until) < datetime.now(timezone.utc):
                supabase.table("users").update({
                    "banned": False,
                    "ban_until": None,
                    "ban_reason": None
                }).eq("username", username).execute()
            else:
                st.error(f"⛔ Banlısın\n\nSebep: {u.get('ban_reason','-')}")
                st.stop()
        else:
            st.error(f"⛔ Banlısın\n\nSebep: {u.get('ban_reason','-')}")
            st.stop()

    return u
# ================= LOGIN =================
if "user" not in st.session_state:

    # 🔎 Eski cookie'leri tara
    existing = find_existing_user()

    if existing:
        # ❗ cookie'yi hemen yazmaya zorlama
        # sadece session'a al
        st.session_state.user = existing

        # 🔁 migrate flag
        if not cookies.get("v6_user"):
            cookies["v6_user"] = existing
            cookies.save()

        st.rerun()

    # 👤 Login ekranı
    st.title("👤 Giriş")
    name = st.text_input("Kullanıcı adı", max_chars=20)

    if st.button("Giriş"):
        name = name.strip()

        if not name or len(name) < 3:
            st.error("❌ Kullanıcı adı en az 3 karakter olmalı")
            st.stop()

        r = supabase.table("users") \
            .select("username") \
            .eq("username", name) \
            .execute()

        if r.data:
            st.error("❌ Bu kullanıcı adı zaten kullanımda")
            st.stop()

        # 🧾 yeni kayıt
        supabase.table("users").insert({
            "username": name,
            "created_at": datetime.utcnow().isoformat(),
            "banned": False,
            "is_admin": False
        }).execute()

        # 🍪 sadece v6 yaz
        cookies["v6_user"] = name
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

        if st.button("⛔ Banla"):
            supabase.table("users").update({
                "banned": True,
                "ban_reason": reason,
                "ban_until": (
                    datetime.now(timezone.utc) + timedelta(minutes=minutes)
                ).isoformat() if minutes else None
            }).eq("username", target).execute()
            st.success("Banlandı")

        if st.button("✅ Ban kaldır"):
            supabase.table("users").update({
                "banned": False,
                "ban_reason": None,
                "ban_until": None
            }).eq("username", target).execute()
            st.success("Açıldı")

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
    if len(st.session_state.chat) >= 2 and \
       st.session_state.chat[-1]["content"] == txt and \
       st.session_state.chat[-2]["content"] == txt:
        st.warning("⏳ Bu isteği zaten işliyorum")
        st.stop()

    st.session_state.chat.append({"role": "user", "content": txt})

    if any(k in txt.lower() for k in ["çiz", "görsel", "resim", "image"]):
        try:
            result = hf_client.predict(prompt=txt, api_name="/generate_image")
            img_io = render_hf_image(result)

            if img_io:
                st.session_state.chat.append({
                    "role": "assistant",
                    "content": "🖼️ Oluşturulan görsel:"
                })
                st.image(img_io, use_container_width=True)
                st.rerun()
            else:
                reply = "⚠️ Görsel üretildi ama gösterilemedi"

        except Exception:
            reply = "❌ Görsel üretim hatası"
    else:
        r = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = r.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
