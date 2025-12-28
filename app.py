import streamlit as st
from openai import OpenAI
from gradio_client import Client
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🧠",
    layout="wide"
)

# ---------------- SECRETS ----------------
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
HF_SPACE_URL = st.secrets["HF_SPACE_URL"]

openai_client = OpenAI(api_key=OPENAI_API_KEY)
hf_client = Client(HF_SPACE_URL)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.chat-user {
    background:#2563eb;
    color:white;
    padding:12px;
    border-radius:12px;
    margin:8px 0;
    width:fit-content;
}
.chat-bot {
    background:#1e293b;
    color:white;
    padding:12px;
    border-radius:12px;
    margin:8px 0;
    width:fit-content;
}
.image-box {
    background:#111827;
    border-radius:16px;
    padding:20px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("🧠 Burak GPT")
st.caption("Yazı • Araştırma • Görsel")

# ---------------- INPUT BAR ----------------
col1, col2, col3 = st.columns([2, 8, 1])

with col1:
    mode = st.selectbox(
        "",
        ["Yazı", "Araştırma", "Görsel"],
        label_visibility="collapsed"
    )

with col2:
    user_input = st.text_input(
        "",
        placeholder="Bir şey yaz..."
    )

with col3:
    send = st.button("▶")

# ---------------- FUNCTIONS ----------------
def burak_gpt_text(prompt, mode):
    system_prompt = {
        "Yazı": "Samimi, net ve akıllı cevap ver.",
        "Araştırma": "Maddeli, öğretici ve detaylı anlat."
    }.get(mode, "")

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def burak_gpt_image(prompt):
    result = hf_client.predict(
        prompt=prompt,
        api_name="/generate"
    )
    return result["url"]

# ---------------- SEND ----------------
if send and user_input:
    st.session_state.messages.append(("user", user_input, mode))

    if mode == "Görsel":
        with st.spinner("🎨 Burak GPT çiziyor..."):
            img_url = burak_gpt_image(user_input)
            st.session_state.messages.append(("image", img_url, mode))
    else:
        with st.spinner("🧠 Burak GPT düşünüyor..."):
            reply = burak_gpt_text(user_input, mode)
            st.session_state.messages.append(("bot", reply, mode))

# ---------------- CHAT AREA ----------------
st.divider()

for role, content, mode in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='chat-user'>🧑 {content}</div>", unsafe_allow_html=True)

    elif role == "bot":
        st.markdown(f"<div class='chat-bot'>🤖 {content}</div>", unsafe_allow_html=True)

    elif role == "image":
        st.markdown("<div class='image-box'>", unsafe_allow_html=True)
        st.image(content, width=512)
        st.markdown("</div>", unsafe_allow_html=True)
