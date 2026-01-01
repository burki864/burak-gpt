import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh

# ================= PAGE =================
st.set_page_config("Admin Panel", "🛠️", "wide")

# 🔁 AUTO REFRESH (2 SANİYE)
st_autorefresh(interval=2000, key="admin_realtime")

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]  # SERVICE ROLE (RLS BYPASS)
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
            .order("created_at", desc=True)
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
st.json({
    "username": user.get("username"),
    "banned": user.get("banned"),
    "deleted": user.get("deleted"),
    "is_online": user.get("is_online"),
    "last_seen": user.get("last_seen"),
    "created_at": user.get("created_at"),
})

# ================= ACTIONS =================
c1, c2, c3, c4 = st.columns(4)

def update_user(data):
    supabase.schema("public") \
        .from_("users") \
        .update(data) \
        .eq("username", selected) \
        .execute()
    st.success("✔️ Güncellendi")
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
st.subheader("🎥 Sohbet Replay (Canlıya Yakın)")

def load_conversation(username):
    try:
        res = (
            supabase
            .schema("public")
            .from_("chat_logs_grouped")
            .select("conversation, updated_at")
            .eq("username", username)
            .single()
            .execute()
        )
        return res.data
    except:
        return None

chat = load_conversation(selected)

if chat and chat.get("conversation"):
    with st.expander("🗂️ Konuşmayı Göster / Gizle", expanded=True):
        st.caption(f"🕒 Son güncelleme: {chat.get('updated_at')}")
        st.text(chat["conversation"])
else:
    st.info("Bu kullanıcıya ait sohbet yok")

# ================= QUICK FILTERS =================
st.divider()
st.subheader("⚡ Hızlı Filtreler")

c5, c6, c7 = st.columns(3)

if c5.button("🚫 Banlılar"):
    data = supabase.schema("public").from_("users").select("*").eq("banned", True).execute().data
    st.dataframe(data)

if c6.button("🧹 Silinenler"):
    data = supabase.schema("public").from_("users").select("*").eq("deleted", True).execute().data
    st.dataframe(data)

if c7.button("🟢 Online"):
    data = supabase.schema("public").from_("users").select("*").eq("is_online", True).execute().data
    st.dataframe(data)

# ================= NAV =================
st.divider()
if st.button("⬅️ GPT’ye Dön"):
    st.switch_page("app.py")
