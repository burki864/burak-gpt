import streamlit as st
from openai import OpenAI
from gradio_client import Client as GradioClient
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="centered"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
body {
    background-color: #0e0e0e;
    color: white;
}
.stTextInput input {
    background-color: #1e1e1e;
    color: white;
}
.stTextArea textarea {
    background-color: #1e1e1e;
    color: white;
}
.stButton button {
    background-color: #ffffff;
    color: black;
    border-radius: 10px;
}
.chat-user {
    background-color: #1f1f1f;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 5px;
}
.chat-bot {
    background-color: #2b2b2b;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.loader {
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
    animation: pulse 1s infinite;
}
@keyframes pulse {
    0% {opacity: .3;}
    50% {opacity: 1;}
    100% {opacity: .3;}
}
</style>
""", unsafe_allow_html=True)

# ---------------- SECRETS ----------------
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

# ---------------- CLIENTS ----------------
openai_client = OpenAI(api_key=OPENAI_KEY)

hf_client = GradioClient(
    "burak12321/burak-gpt-image",
    hf_token=HF_TOKEN
)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- HEADER ----------------
st.title("🤖 Burak GPT")
st.caption("Sohbet + Görsel Üretim")

# ---------------- CHAT HISTORY ----------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'><b>Sen:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'><b>Burak GPT:</b> {msg['content']}</div>", unsafe_allow_html=True)

# ---------------- INPUT ----------------
prompt = st.text_input("Bir şey yaz... (görsel için: resim:)")

# ---------------- ACTION ----------------
if st.button("Gönder") and prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Düşünüyorum..."):
        time.sleep(0.5)

        # ---- IMAGE MODE ----
        if prompt.lower().startswith("resim:"):
            image_prompt = prompt.replace("resim:", "").strip()

            try:
                result = hf_client.predict(
                    image_prompt,
                    api_name="/generate"
                )

                if isinstance(result, dict) and result.get("url"):
                    image_url = result["url"]
                elif isinstance(result, str):
                    image_url = result
                else:
                    image_url = None

                if image_url:
                    st.image(image_url, caption="Oluşturulan Görsel")
                    bot_reply = "Görsel hazır 👑"
                else:
                    bot_reply = "Görsel üretilemedi."

            except Exception as e:
                bot_reply = f"Hata: {e}"

        # ---- CHAT MODE ----
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
