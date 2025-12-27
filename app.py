import streamlit as st
import openai

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="centered"
)

# =============================
# API KEY
# =============================
openai.api_key = st.secrets["OPENAI_API_KEY"]

# =============================
# STYLE
# =============================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f0f1a, #1a1a2e);
}
.stApp {
    background: transparent;
}
.chat-user {
    background: #2e2e4d;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}
.chat-bot {
    background: #2563eb;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# HEADER
# =============================
st.markdown("## 🧠 **BurakGPT**")
st.caption("Düşünür. Araştırır. Konuşur.")

# =============================
# SESSION
# =============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================
# MODE
# =============================
mode = st.selectbox("Mod", ["Sohbet", "Araştırma", "Yaratıcı"])

system_prompt = {
    "Sohbet": "Samimi ama zeki konuş.",
    "Araştırma": "Net, maddeli ve öğretici anlat.",
    "Yaratıcı": "Yaratıcı ve özgün cevap ver."
}[mode]

# =============================
# CHAT HISTORY
# =============================
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='chat-user'>🧑 {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>🤖 {msg}</div>", unsafe_allow_html=True)

# =============================
# INPUT
# =============================
user_input = st.text_area(
    "",
    placeholder="Bir şey yaz…",
    height=80
)

send = st.button("🚀 Gönder")

# =============================
# ACTION
# =============================
if send and user_input.strip():
    st.session_state.messages.append(("user", user_input))

    with st.spinner("🧠 BurakGPT düşünüyor..."):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response["choices"][0]["message"]["content"]

    st.session_state.messages.append(("bot", reply))
    st.rerun()
