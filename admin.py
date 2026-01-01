import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh

# ================= PAGE =================
st.set_page_config("Admin Panel", "🛠️", "wide")

# 🔁 AUTO REFRESH (2 SN)
st_autorefresh(interval=2000, key="admin_live")

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]  # SERVICE ROLE
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
            .from_("users")
            .select("*")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error("❌ Kullanıcılar yüklenemedi")
        st.exception(e)
        return []

users = load_users()

st.title("🛠️ Admin Panel")

if not users:
    st.info("Kullanıcı yok")
    st.stop()

# ================= USER SELECT =================
usernames = [u["username"] for u in users]
selected = st.selectbox("👤 Kullanıcı", usernames)

user = next(u for u in users if u["username"] == selected)

# ================= USER INFO =================
st.subheader("📌 Kullanıcı Bilgisi")
st.json(user)

# ================= ACTIONS =================
st.subheader("⚙️ İşlemler")

c1, c2, c3, c4, c5 = st.columns(5)

def update_user(data):
    supabase.from_("users") \
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

# ================= HARD DELETE =================
with c5:
    confirm = st.checkbox("Kalıcı sil")

    if st.button("🗑️ HESABI SİL"):
        if not confirm:
            st.error("⚠️ Onay ver")
        else:
            supabase.from_("chats") \
                .delete() \
                .eq("username", selected) \
                .execute()

            supabase.from_("users") \
                .delete() \
                .eq("username", selected) \
                .execute()

            st.success("✅ Hesap kalıcı olarak silindi")
            st.rerun()

# ================= CHAT REPLAY =================
st.divider()
st.subheader("🎥 Canlı Sohbet Replay")

def load_chat(username):
    try:
        res = (
            supabase
            .from_("chats")
            .select("role, content, created_at")
            .eq("username", username)
            .order("created_at")
            .execute()
        )
        return res.data or []
    except:
        return []

messages = load_chat(selected)

if messages:
    with st.expander("🗂️ Konuşma", expanded=True):
        for m in messages:
            role = "👤 USER" if m["role"] == "user" else "🤖 AI"
            st.markdown(f"**{role}:** {m['content']}")
else:
    st.info("Henüz mesaj yok")

# ================= NAV =================
st.divider()
if st.button("⬅️ GPT’ye Dön"):
    st.switch_page("app.py")
