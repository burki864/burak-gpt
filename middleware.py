import streamlit as st
from utils import load_users

def user_guard(user_id):
    data = load_users()
    user = data["users"].get(user_id)

    if not user:
        st.error("❌ Kullanıcı bulunamadı")
        st.stop()

    if user.get("banned"):
        st.error("🚫 Bu hesap banlandı")
        st.stop()

    if not user.get("active"):
        st.error("⚫ Bu hesap kapatıldı")
        st.stop()
