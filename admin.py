import streamlit as st
import json

ADMIN_KEY = st.secrets["ADMIN_KEY"]
DB_FILE = "users.json"

def load_users():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 🔐 GİZLİ GİRİŞ
key = st.text_input("Admin Key", type="password")

if key != ADMIN_KEY:
    st.warning("Yetkisiz erişim")
    st.stop()

st.success("👑 Admin Paneli")

users = load_users()
username = st.text_input("Kullanıcı adı")

col1, col2 = st.columns(2)

if col1.button("🚫 Ban"):
    users[username] = {"status": "banned"}
    save_users(users)
    st.success("Banlandı")

if col2.button("❌ Kapat"):
    users[username] = {"status": "closed"}
    save_users(users)
    st.success("Kapatıldı")

st.subheader("📋 Kayıtlı Kullanıcılar")
st.json(users)
