import time
import requests
import threading
import streamlit as st
from openai import OpenAI
from gradio_client import Client

# ================= KEEP AWAKE =================
def keep_awake():
    while True:
        try:
            requests.get("https://burakgpt.streamlit.app/")
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_awake, daemon=True).start()

# ================= PAGE =================
st.set_page_config(
    page_title="Burak GPT",
    page_icon="🤖",
    layout="wide"
)

# ================= STYLE =================
st.markdown("""
<style>
.stApp {
    background-color: #0b0b0b;
    color: #f2f2f2;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ================= API =================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= IMAGE =================
def is_image_request(text):
    keys = ["çiz", "resim", "görsel", "image", "photo", "art", "manzara"]
    return any(k in text.lower() for k in keys)

def generate_image(prompt):
    client = Client(
        "mrfakename/Z-Image-Turbo",
        token=st.secrets["HF_TOKEN"]
    )
    result = client.predict(
        prompt=prompt,
        height=768,
        width=768,
        num_inference_steps=9,
        randomize_seed=True,
        api_name="/generate_image"
    )

    if isinstance(result, (list, tuple)) and result:
        img = result[0]
        if isinstance(img, dict) and img.get("url"):
            return img["url"]
        if isinstance(img, str):
            return img
    return None

# ================= SESSION =================
if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= UI =================
st.title("🤖 Burak GPT")

# ===== CHAT =====
for m in st.session_state.chat:
    if m["role"] == "user":
        st.markdown(f"**Sen:** {m['content']}")
    else:
        if m.get("type") == "image":
            st.image(m["content"], use_container_width=True)
        else:
            st.markdown(f"**Burak GPT:** {m['content']}")

# ===== INPUT =====
txt = st.text_input("Mesajın")

if st.button("Gönder") and txt.strip():
    # kullanıcı mesajı
    st.session_state.chat.append({
        "role": "user",
        "content": txt
    })

    if is_image_request(txt):
        img = generate_image(txt)

        if img:
            # 👇 GÖRSELİ GERÇEKTEN BAS
            st.session_state.chat.append({
                "role": "assistant",
                "type": "image",
                "content": img
            })
            st.session_state.chat.append({
                "role": "assistant",
                "content": "🖼️ Görsel hazır"
            })
        else:
            st.session_state.chat.append({
                "role": "assistant",
                "content": "❌ Görsel üretilemedi"
            })

    else:
        res = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=txt
        )
        st.session_state.chat.append({
            "role": "assistant",
            "content": res.output_text
        })

    st.rerun()
