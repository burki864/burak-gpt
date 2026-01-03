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
COOKIE_PREFIXES = [
    "burak_v1_",
    "burak_v2_",
    "burak_v3_",
    "burak_v4_",
    "burak_v5_",
    "burak_v6_"
]

def find_existing_user():
    for p in COOKIE_PREFIXES:
        c = EncryptedCookieManager(prefix=p, password=st.secrets["COOKIE_SECRET"])
        if not c.ready():
            continue
        u = c.get("user")
        if u:
            return u
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

    # 🔍 TÜM COOKIE VERSİYONLARINI TARA
    existing_user = find_existing_user()

    if existing_user:
        # ✅ ESKİ KULLANICIYI KORU
        cookies["user"] = existing_user  # v6'ya taşı
        cookies.save()
        st.session_state.user = existing_user
        st.rerun()

    # 🆕 YENİ KULLANICI
    st.title("👤 Giriş")

    name = st.text_input("Kullanıcı adı")

    if st.button("Giriş"):
        if not name or len(name) < 3:
            st.error("❌ Geçerli bir kullanıcı adı gir")
            st.stop()

        r = supabase.table("users").select("username").eq("username", name).execute()

        # ❌ AYNI İSİM VARSA GİRİŞ YOK
        if r.data:
            st.error("❌ Bu kullanıcı adı zaten kullanımda")
            st.stop()

        # ✅ YENİ KAYIT
        supabase.table("users").insert({
            "username": name,
            "created_at": datetime.utcnow().isoformat(),
            "banned": False,
            "is_admin": False
        }).execute()

        cookies["user"] = name
        cookies.save()
        st.session_state.user = name
        st.rerun()

    st.stop()
# ================= SESSION USER =================
user = st.session_state.user
me = user_guard(user)

# ================= ADMIN PANEL =================
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
                "ban_until": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat() if minutes else None
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
with st.form("f", clear_on_submit=True):
    txt = st.text_input("Mesajın")
    send = st.form_submit_button("Gönder")

if send and txt:
    if len(st.session_state.chat) >= 2 and \
       st.session_state.chat[-1]["content"] == txt and \
       st.session_state.chat[-2]["content"] == txt:
        st.warning("⏳ Bu isteği zaten işliyorum")
        st.stop()

    st.session_state.chat.append({"role": "user", "content": txt})

    if any(k in txt.lower() for k in ["çiz", "görsel", "resim", "image"]):
        hf_client.predict(prompt=txt, api_name="/generate_image")
        reply = "🖼️ Görsel oluşturuluyor…"
    else:
        r = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        reply = r.output_text

    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.rerun()
