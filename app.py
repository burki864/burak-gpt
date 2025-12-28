import streamlit as st
import requests, time
from openai import OpenAI
from PIL import Image
from io import BytesIO

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="wide"
)

# ===============================
# DARK THEME CSS
# ===============================
st.markdown("""
<style>
body { background-color:#0f1117; }
.chat-bubble-user {
    background:#1f2937;
    padding:12px;
    border-radius:12px;
    margin:6px 0;
}
.chat-bubble-bot {
    background:#111827;
    padding:12px;
    border-radius:12px;
    margin:6px 0;
}
.input-box {
    background:#020617;
    padding:12px;
    border-radius:14px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# API CLIENTS
# ===============================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

HF_MODEL = "runwayml/stable-diffusion-v1-5"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {
    "Authorization": f"Bearer {st.secrets['HF_TOKEN']}"
}

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===============================
# FUNCTIONS
# ===============================
def chat_gpt(prompt):
    msgs = [{"role": "system", "content": "Samimi ama profesyonel cevap ver."}]
    for r, c in st.session_state.messages:
        msgs.append({"role": "user" if r=="user" else "assistant", "content": c})
    msgs.append({"role": "user", "content": prompt})

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=msgs
    )
    return res.choices[0].message.content

def generate_image(prompt):
    payload = {"inputs": prompt}
    for _ in range(3):
        r = requests.post(HF_URL, headers=HF_HEADERS, json=payload)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
        if r.status_code == 503:
            time.sleep(5)
    return None

# ===============================
# TITLE
# ===============================
st.markdown("## 🧠 **BurakGPT**")
st.caption("Sohbet • Araştırma • Görsel")

# ===============================
# CHAT HISTORY
# ===============================
for role, content in st.session_state.messages:
    css = "chat-bubble-user" if role=="user" else "chat-bubble-bot"
    st.markdown(f"<div class='{css}'>{content}</div>", unsafe_allow_html=True)

# ===============================
# INPUT BAR
# ===============================
with st.container():
    c1, c2, c3 = st.columns([1,5,1])

    with c1:
        mode = st.selectbox(
            "",
            ["💬 Sohbet", "🔍 Araştırma", "🎨 Görsel"],
            label_visibility="collapsed"
        )

    with c2:
        user_input = st.text_input(
            "",
            placeholder="BurakGPT’ye yaz…",
            label_visibility="collapsed"
        )

    with c3:
        send = st.button("➤")

# ===============================
# ACTION
# ===============================
if send and user_input:
    st.session_state.messages.append(("user", user_input))

    if "Görsel" in mode:
        with st.spinner("🎨 Görsel hazırlanıyor..."):
            img = generate_image(user_input)
            if img:
                st.image(img, use_container_width=False, width=512)
                st.session_state.messages.append(("bot", "🖼️ Görsel hazır"))
            else:
                st.session_state.messages.append(("bot", "⚠️ Görsel motoru yoğun, biraz sonra dene"))

    else:
        with st.spinner("🧠 BurakGPT düşünüyor..."):
            reply = chat_gpt(user_input)
            st.session_state.messages.append(("bot", reply))

    st.rerun()
