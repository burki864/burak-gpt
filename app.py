import streamlit as st
import json, os
from datetime import datetime

st.set_page_config(page_title="Burak GPT", layout="wide")

# ---------- STATE GARANTİ ----------
for key, val in {
    "user_id": None,
    "theme": "dark",
    "mode": "💬 Sohbet",
    "messages": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------- USER DATA ----------
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {"counter": 0, "users": {}}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- LOGIN ----------
if st.session_state.user_id is None:
    st.title("👋 Hoş Geldin")
    name = st.text_input("Adın nedir?")

    if st.button("Devam Et") or st.button("Bu adımı geç"):
        data = load_users()
        data["counter"] += 1

        uid = name.strip() if name.strip() else f"user{data['counter']}"

        if uid not in data["users"]:
            data["users"][uid] = {
                "name": uid,
                "created": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "visits": 1,
                "banned": False,
                "active": True
            }
        else:
            data["users"][uid]["visits"] += 1
            data["users"][uid]["last_seen"] = datetime.now().isoformat()

        save_users(data)
        st.session_state.user_id = uid
        st.rerun()

    st.stop()

# ---------- BAN KONTROL ----------
data = load_users()
user = data["users"].get(st.session_state.user_id)

if not user or user.get("banned") or not user.get("active"):
    st.error("⛔ Hesabınız kapalı veya banlı.")
    st.stop()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_id}**")
    st.session_state.mode = st.radio(
        "Mod", ["💬 Sohbet", "🎨 Görsel Üretim", "🔍 Araştırma"]
    )
    if st.button("🚪 Çıkış"):
        st.session_state.user_id = None
        st.rerun()

# ---------- MAIN ----------
st.title("🤖 Burak GPT")

if st.session_state.mode == "💬 Sohbet":
    for m in st.session_state.messages:
        st.write(f"**{m['role']}**: {m['content']}")

    msg = st.text_input("Mesaj yaz")
    if st.button("Gönder") and msg:
        st.session_state.messages.append({"role": "Sen", "content": msg})
        st.session_state.messages.append({"role": "Burak GPT", "content": "Hazırım kral 😎"})
        st.rerun()

elif st.session_state.mode == "🎨 Görsel Üretim":
    st.info("🎨 Görsel üretim burada çalışır")

else:
    st.info("🔍 Araştırma burada çalışır")
