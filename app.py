import streamlit as st
import requests
from openai import OpenAI
from PIL import Image, ImageFilter
from io import BytesIO
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="wide"
)

HF_TOKEN = st.secrets["HF_TOKEN"]
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_KEY)

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {
    background-color: #0b0f19;
    color: white;
}
.chat {
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    max-width: 80%;
}
.user {
    background: #1f2937;
    margin-left: auto;
}
.bot {
    background: #111827;
}
input {
    background-color:#111827 !important;
    color:white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- UI LAYOUT ----------------
left, right = st.columns([1,5])

with left:
    st.markdown("### ⚙️ Mod")
    mode = st.radio("", ["💬 Sohbet", "🎨 Görsel"], label_visibility="collapsed")

with right:
    st.markdown("## 🧠 BurakGPT")

    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "bot"
        st.markdown(
            f"<div class='chat {role}'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

    prompt = st.text_input(
        "Mesaj yaz ya da 'Cyberpunk şehir çiz' gibi komut ver",
        placeholder="Buraya yaz kral…"
    )

    send = st.button("Gönder 🚀")

# ---------------- ACTION ----------------
if send and prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ---------- IMAGE MODE ----------
    if "Görsel" in mode:
        with st.spinner("🎨 Görsel oluşturuluyor..."):
            payload = {
                "inputs": prompt,
                "parameters": {
                    "steps": 30,
                    "guidance_scale": 8
                }
            }

            r = requests.post(HF_URL, headers=HF_HEADERS, json=payload)

            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))

                # -------- EFFECT --------
                blurred = img.filter(ImageFilter.GaussianBlur(18))
                placeholder = st.empty()

                placeholder.image(blurred, caption="Yükleniyor...", use_container_width=False)
                time.sleep(1.2)

                placeholder.image(img, caption="🖼️ Görsel hazır", use_container_width=False)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Görseli senin için oluşturdum 🎨"
                })
            else:
                st.error("Görsel üretilemedi (HF)")

    # ---------- CHAT MODE ----------
    else:
        with st.spinner("🧠 Düşünüyorum..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )
            reply = res.choices[0].message.content
            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )
            st.rerun()
