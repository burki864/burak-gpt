import streamlit as st
import json, os
from supabase import create_client

# ================= PAGE =================
st.set_page_config("Admin Panel","🛠️","wide")

# ================= SUPABASE =================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
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

# ================= USERS (LOCAL JSON – BOZULMADI) =================
def load_users():
    if not os.path.exists("users.json"):
        return {}
    return json.load(open("users.json","r"))

def save_users(u):
    json.dump(u, open("users.json","w"), indent=2)

users = load_users()

st.title("🛠️ Admin Panel")

if not users:
    st.info("Henüz kullanıcı yok")
    st.stop()

# ================= USER SELECT =================
user = st.selectbox("👤 Kullanıcı", users.keys())
info = users[user]

st.write("📌 Durum:", info)

# ================= ACTION BUTTONS =================
c1, c2, c3 = st.columns(3)

if c1.button("🚫 Ban"):
    info["banned"] = True

if c2.button("✅ Unban"):
    info["banned"] = False

if c3.button("🧹 Soft Delete"):
    info["deleted"] = True

if st.button("♻️ Geri Aç"):
    info["deleted"] = False

save_users(users)
st.success("✔️ Güncellendi")

# ================= CHAT REPLAY =================
st.divider()
st.subheader("🎥 Sohbet Replay")

def load_conversation(username):
    res = supabase.table("chat_logs_grouped") \
        .select("conversation") \
        .eq("username", username) \
        .execute()

    if res.data:
        return res.data[0]["conversation"]
    return None

conversation = load_conversation(user)

if conversation:
    with st.expander("🗂️ Konuşmayı Göster / Gizle", expanded=False):
        st.text(conversation)
else:
    st.info("Bu kullanıcıya ait sohbet kaydı yok")

# ================= NAV =================
st.divider()
if st.button("⬅️ GPT’ye Dön"):
    st.switch_page("app.py")
