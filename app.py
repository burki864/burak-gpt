import streamlit as st
from openai import OpenAI
from gradio_client import Client as HFClient
import time

# =======================
# CONFIG
# =======================
st.set_page_config(
    page_title="🧠 BurakGPT",
    page_icon="🧠",
    layout="wide"
)

# =======================
# SECRETS
# =======================
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_SPACE = st.secrets["HF_SPACE"]
HF_TOKEN = st.secrets["HF_TOKEN"]

openai_client = OpenAI(api_key=OPENAI_KEY)
hf_client = HFClient(HF_SPACE, hf_token=HF_TOKEN)

# =======================
# SESSION STATE
# =======================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =======================
# STYLE (FULL DARK)
# =======================
st.markdown("""
<style>
body {
    background: linear-gradient(180deg, #020617, #020617);
}

.chat-bubble-user {
    background: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 16px;
    margin: 6px 0;
    max-width: 70%;
    margin-left: auto;
}

.chat-bubble-bot {
    background: #020617;
    color: #e5e7eb;
    padding: 12px 16px;
    border-radius: 16px;
    margin: 6px 0;
    max-width: 70%;
    border: 1px solid #1e293b;
}

input, textarea {
    color: white !important;
    background-color: #020617 !important;
}

::placeholder {
    color: #9ca3af !important;
}
</style>
""", unsafe_allow_html=True)

# =======================
# TITLE
# =======================
st.markdown("## 🧠 **BurakGPT**")
st.caption("Yazı • Araştırma • Görsel")

# =======================
# CHAT HISTORY
# =======================
for role, msg in st.session_state.messages:
    css = "chat-bubble-user" if role == "user" else "chat-bubble-bot"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

# =======================
# INPUT AREA
# =======================
col_mode, col_input, col_send = st.columns([1, 6, 1])

with col_mode:
    mode = st.selectbox(
        "Mod",
        ["Sohbet", "Araştırma", "Görsel"],
        label_visibility="collapsed"
    )

with col_input:
    user_input = st.text_input(
        "Mesaj",
        placeholder="BurakGPT’ye yaz...",
        label_visibility="collapsed"
    )

with col_send:
    send = st.button("➤")

# =======================
# FUNCTIONS
# =======================
def chat_gpt(prompt, mode):
    styles = {
        "Sohbet": "Samimi, kısa ve net cevap ver.",
        "Araştırma": "Maddeli, öğretici ve net anlat."
    }

    messages = [{"role": "system", "content": styles.get(mode, "")}]
    for r, m in st.session_state.messages:
        messages.append({"role": r, "content": m})
    messages.append({"role": "user", "content": prompt})

    res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return res.choices[0].message.content


def generate_image(prompt):
    try:
        result = hf_client.predict(prompt, api_name="/predict")
        return result["url"] if isinstance(result, dict) else result
    except Exception as e:
        return None

# =======================
# ACTION
# =======================
if send and user_input:
    st.session_state.messages.append(("user", user_input))

    if mode == "Görsel":
        with st.spinner("🎨 Görsel oluşturuluyor..."):
            img_url = generate_image(user_input)
            if img_url:
                st.image(img_url, caption="BurakGPT Görsel", use_column_width=False, width=512)
            else:
                st.error("❌ Görsel üretilemedi. Biraz sonra tekrar dene.")

    else:
        with st.spinner("🧠 BurakGPT düşünüyor..."):
            reply = chat_gpt(user_input, mode)
            st.session_state.messages.append(("assistant", reply))
            st.rerun()
