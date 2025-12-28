import streamlit as st
import os
import time
from openai import OpenAI
from gradio_client import Client

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="centered"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
body { background-color:#0e0e0e; color:white; }
input, textarea { background:#1e1e1e !important; color:white !important; }
button { background:white !important; color:black !important; border-radius:10px; }
.chat-user { background:#1f1f1f; padding:10px; border-radius:10px; margin-bottom:6px; }
.chat-bot { background:#2b2b2b; padding:10px; border-radius:10px; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

# 🔑 HF TOKEN ENV (KRİTİK NOKTA)
os.environ["HF_TOKEN"] = HF_TOKEN

# ---------------- CLIENTS ----------------
openai_client = OpenAI(api_key=OPENAI_KEY)

hf_client = Client(
    "burak12321/burak-gpt-image"
)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- UI ----------------
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel Üretim")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'><b>Sen:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'><b>Burak GPT:</b> {msg['content']}</div>", unsafe_allow_html=True)

prompt = st.text_input("Bir şey yaz (görsel için: resim:)")

# ---------------- ACTION ----------------
if st.button("Gönder") and prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("İşleniyor..."):
        time.sleep(0.4)

        # 🖼️ IMAGE
        if prompt.lower().startswith("resim:"):
            image_prompt = prompt.replace("resim:", "").strip()
            try:
                result = hf_client.predict(
                    image_prompt,
                    api_name="/generate"
                )
                st.image(result)
                bot_reply = "Görsel hazır 👑"
            except Exception as e:
                bot_reply = f"Görsel hata: {e}"

        # 💬 CHAT
        else:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )
            bot_reply = response.choices[0].message.content

        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )

    st.rerun()
