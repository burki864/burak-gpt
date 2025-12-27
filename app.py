import streamlit as st
from openai import OpenAI

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="centered"
)

# =============================
# STYLE
# =============================
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top, #1e1e2f, #0e0e15);
    color: #f5f5f7;
}
.stApp {
    background: transparent;
}
.chat-bubble-user {
    background: #3a3a55;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 8px;
}
.chat-bubble-bot {
    background: #1f7aec;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 8px;
}
textarea {
    border-radius: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# =============================
# HEADER
# =============================
st.markdown("## 🧠 **BurakGPT**")
st.caption("Araştırır. Düşünür. Cevap verir. Rakip tanımaz.")

# =============================
# SESSION
# =============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================
# MODE SELECT
# =============================
mode = st.selectbox(
    "Mod",
    ["Sohbet", "Araştırma", "Yaratıcı"]
)

system_styles = {
    "Sohbet": "Samimi ama zeki konuş.",
    "Araştırma": "Maddeli, net ve öğretici anlat.",
    "Yaratıcı": "Yaratıcı, özgün ve ilham verici ol."
}

# =============================
# CLIENT
# =============================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =============================
# CHAT HISTORY
# =============================
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='chat-bubble-user'>🧑 {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>🤖 {msg}</div>", unsafe_allow_html=True)

# =============================
# INPUT
# =============================
user_input = st.text_area(
    "",
    placeholder="Bir şey yaz… BurakGPT düşünsün.",
    height=80
)

send = st.button("🚀 Gönder")

# =============================
# ACTION
# =============================
if send and user_input.strip():
    st.session_state.messages.append(("user", user_input))

    with st.spinner("🧠 BurakGPT düşünüyor..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_styles[mode]},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.choices[0].message.content

    st.session_state.messages.append(("bot", reply))
    st.rerun()
