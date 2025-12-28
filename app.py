import streamlit as st
from gradio_client import Client
from openai import OpenAI

# =====================
# CONFIG
# =====================
HF_SPACE_URL = "https://burak12321-generate-image-burakgpt.hf.space"

# =====================
# PAGE
# =====================
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# DARK MODE CSS
# =====================
st.markdown("""
<style>
body, .stApp {
    background-color: #0f1117;
    color: #e6e6e6;
}
textarea, input {
    background-color: #1c1f26 !important;
    color: white !important;
}
.stButton>button {
    background: linear-gradient(135deg,#6a11cb,#2575fc);
    color: white;
    border-radius: 10px;
    padding: 10px 16px;
}
.stChatMessage {
    background-color: #1c1f26;
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("⚙️ BurakGPT")
mode = st.sidebar.radio(
    "Mod Seç",
    ["💬 Sohbet", "🎨 Görsel Üret"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Dark Mode • HF + OpenAI")

# =====================
# HEADER
# =====================
st.title("🧠 BurakGPT")
st.caption("Profesyonel yapay zeka • Sohbet + Görsel üretim")

# =====================
# OPENAI CLIENT
# =====================
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ OPENAI_API_KEY Secrets'e eklenmemiş")
    st.stop()

client_ai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =====================
# CHAT MODE
# =====================
if mode == "💬 Sohbet":

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("BurakGPT’ye yaz...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Düşünüyorum..."):
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                reply = response.choices[0].message.content
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

# =====================
# IMAGE MODE
# =====================
elif mode == "🎨 Görsel Üret":

    st.subheader("🎨 Görsel Üret")

    prompt = st.text_area(
        "Görseli tarif et",
        placeholder="Cyberpunk İstanbul, neon ışıklar, sinematik, ultra detay",
        height=120
    )

    if st.button("🚀 Görsel Oluştur"):
        if not prompt.strip():
            st.warning("Prompt boş olamaz")
        else:
            with st.spinner("🎨 Görsel oluşturuluyor..."):
                hf_client = Client(HF_SPACE_URL)
                result = hf_client.predict(prompt, api_name="/predict")

            st.image(result, caption="BurakGPT tarafından üretildi", use_container_width=True)

# =====================
# FOOTER
# =====================
st.markdown("---")
st.caption("⚡ BurakGPT • HF Spaces + OpenAI • 2025")
