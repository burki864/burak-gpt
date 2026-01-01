import streamlit as st
from supabase import create_client

# ================= PAGE =================
st.set_page_config(
    page_title="Admin Panel",
    page_icon="🛠️",
    layout="wide"
)

# ================= SUPABASE (SERVICE ROLE) =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]  # 🔥 service_role (RLS bypass)
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
    res = (
        supabase
        .table("users")          # ⚠️ SADECE users
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []

users = load_users()

st.title("🛠️ Admin Panel")

if not users:
    st.info("Kullanıcı bulunamadı")
    st.stop()

# ================= USER SELECT =================
usernames = [u["username"] for u in users]
selected = st.selectbox("👤 Kullanıcı Seç", usernames)

user = next(u for u in users if u["username"] == selected)

# ================= USER INFO =================
st.subheader("📌 Kullanıcı Bilgisi")
st.json({
    "username": user["username"],
    "banned": user.get("banned"),
    "deleted": user.get("deleted"),
    "is_online": user.get("is_online"),
    "last_seen": user.get("last_seen"),
    "created_at": user.get("created_at")
})

# ================= ACTIONS =================
c1, c2, c3, c4 = st.columns(4)

if c1.button("🚫 Ban"):
    supabase.table("users").update(
        {"banned": True}
    ).eq("username", selected).execute()
    st.success("Kullanıcı banlandı")
    st.rerun()

if c2.button("✅ Unban"):
    supabase.table("users").update(
        {"banned": False}
    ).eq("username", selected).execute()
    st.success("Ban kaldırıldı")
    st.rerun()

if c3.button("🧹 Soft Delete"):
    supabase.table("users").update(
        {"deleted": True}
    ).eq("username", selected).execute()
    st.success("Kullanıcı soft delete edildi")
    st.rerun()

if c4.button("♻️ Geri Aç"):
    supabase.table("users").update(
        {"deleted": False}
    ).eq("username", selected).execute()
    st.success("Kullanıcı geri açıldı")
    st.rerun()

# ================= CHAT REPLAY =================
st.divider()
st.subheader("🎥 Sohbet Replay")

def load_conversation(username):
    res = (
        supabase
        .table("chat_logs_grouped")   # ⚠️ public. YOK
        .select("conversation")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["conversation"]
    return None

conversation = load_conversation(selected)

if conversation:
    with st.expander("🗂️ Konuşmayı Göster / Gizle"):
        st.text(conversation)
else:
    st.info("Bu kullanıcıya ait sohbet yok")

# ================= QUICK FILTERS =================
st.divider()
st.subheader("⚡ Hızlı Filtreler")

c5, c6, c7 = st.columns(3)

if c5.button("🚫 Sadece Banlılar"):
    data = supabase.table("users").select("*").eq("banned", True).execute().data
    st.dataframe(data)

if c6.button("🧹 Silinenler"):
    data = supabase.table("users").select("*").eq("deleted", True).execute().data
    st.dataframe(data)

if c7.button("🟢 Online"):
    data = supabase.table("users").select("*").eq("is_online", True).execute().data
    st.dataframe(data)

# ================= NAV =================
st.divider()
if st.button("⬅️ GPT’ye Dön"):
    st.switch_page("app.py")

