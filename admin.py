import streamlit as st
from supabase import create_client

# ================= PAGE =================
st.set_page_config("Admin Panel", "🛠️", "wide")

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]  # 🔥 SERVICE ROLE
)

# ================= AUTH =================
if "admin" not in st.session_state:
    st.session_state.admin = False

if not st.session_state.admin:
    st.title("🔐 Admin Girişi")
    key = st.text_input("Admin Key", type="password")
    if st.button("Giriş"):
        if key == st.secrets["ADMIN_KEY"]:
            st.session_state.admin = True
            st.rerun()
        else:
            st.error("❌ Yetkisiz")
    st.stop()

# ================= LOAD USERS =================
def load_users():
    try:
        res = (
            supabase
            .schema("public")
            .from_("users")
            .select("*")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error("🚨 Kullanıcılar çekilemedi")
        st.exception(e)
        return []

users = load_users()

st.title("🛠️ Admin Panel")

if not users:
    st.info("Kullanıcı bulunamadı")
    st.stop()

# ================= USER SELECT =================
usernames = [u.get("username", "unknown") for u in users]
selected = st.selectbox("👤 Kullanıcı Seç", usernames)

user = next(u for u in users if u.get("username") == selected)

# ================= USER INFO =================
st.subheader("📌 Kullanıcı Bilgisi")
st.json(user)

# ================= ACTIONS =================
c1, c2, c3, c4 = st.columns(4)

def update_user(data):
    supabase.schema("public").from_("users") \
        .update(data) \
        .eq("username", selected) \
        .execute()
    st.rerun()

if c1.button("🚫 Ban"):
    update_user({"banned": True})

if c2.button("✅ Unban"):
    update_user({"banned": False})

if c3.button("🧹 Soft Delete"):
    update_user({"deleted": True})

if c4.button("♻️ Geri Aç"):
    update_user({"deleted": False})

# ================= CHAT REPLAY =================
st.divider()
st.subheader("🎥 Sohbet Replay")

def load_conversation(username):
    try:
        res = (
            supabase
            .schema("public")
            .from_("chat_logs_grouped")
            .select("conversation")
            .eq("username", username)
            .single()
            .execute()
        )
        return res.data["conversation"] if res.data else None
    except:
        return None

conversation = load_conversation(selected)

if conversation:
    with st.expander("🗂️ Konuşmayı Göster / Gizle"):
        st.text(conversation)
else:
    st.info("Bu kullanıcıya ait sohbet yok")

# ================= NAV =================
st.divider()
if st.button("⬅️ GPT’ye Dön"):
    st.switch_page("app.py")
