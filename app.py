import streamlit as st
import base64
from openai import OpenAI

# =======================
# AYARLAR
# =======================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🧠",
    layout="wide"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =======================
# CSS – PROFESYONEL TASARIM
# =======================
st.markdown("""
<style>
body {
    background: linear-gradient(120deg, #f6f7fb, #eef1f7);
}
.chat-user {
    background:#dbeafe;
    padding:12px;
    border-radius:12px;
    margin:8px 0;
}
.chat-bot {
    background:#ffffff;
    padding:12px;
    border-radius:12px;
    margin:8px 0;
    box-shadow:0 2px 6px rgba(0,0,0,0.05);
}
.image-box {
    background:#8b8d93;
    height:360px;
    border-radius:16px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size:18px;
}
</style>
""", unsafe_allow_html=True)

# =======================
# SESSION STATE
# =======================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =======================
# BAŞLIK
# =======================
st.markdown("## 🧠 Burak GPT")
st.caption("Yazı • Araştırma • Görsel")

# =======================
# INPUT BAR (MOD + YAZI + GÖNDER)
# =======================
col1, col2, col3 = st.columns([2, 10, 1])

with col1:
    mode = st.selectbox(" ", ["Sohbet", "Araştırma", "Görsel"], label_visibility="collapsed")

with col2:
    user_input = st.text_input("Burak GPT’ye yaz…", label_visibility="collapsed")

with col3:
    send = st.button("➤")

# =======================
# MESAJ GÖNDER
# =======================
if send and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # -------- GÖRSEL MODU --------
    if mode == "Görsel":
        with st.container():
            box = st.empty()
            box.markdown('<div class="image-box">🎨 Burak GPT çiziyor…</div>', unsafe_allow_html=True)

            img = client.images.generate(
                model="gpt-image-1",
                prompt=user_input,
                size="1024x1024"
            )

            image_base64 = img.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            box.image(image_bytes, width=320)

            st.download_button(
                "⬇️ Görseli indir",
                image_bytes,
                file_name="burakgpt.png",
                mime="image/png"
            )

    # -------- YAZI / ARAŞTIRMA --------
    else:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=st.session_state.messages
        )

        reply = response.output_text
        st.session_state.messages.append({"role": "assistant", "content": reply})

# =======================
# SOHBET GEÇMİŞİ
# =======================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>🤖 {msg['content']}</div>", unsafe_allow_html=True)
