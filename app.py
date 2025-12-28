import streamlit as st
import requests
from openai import OpenAI
from PIL import Image, ImageFilter
from io import BytesIO
import time

# ---------------- CONFIG ----------------
st.set_page_config("BurakGPT", "🧠", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

HF_TOKEN = st.secrets["HF_TOKEN"]
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ---------------- STYLE ----------------
st.markdown("""
<style>
body { background:#0b0f19; color:white; }
.chat { padding:12px; border-radius:12px; margin:8px 0; max-width:75%; }
.user { background:#1f2937; margin-left:auto; }
.bot { background:#111827; }
input { background:#111827 !important; color:white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- LAYOUT ----------------
left, right = st.columns([1,5])

with left:
    st.markdown("### ⚙️ Mod")
    mode = st.radio("", ["💬 Sohbet", "🎨 Görsel"], label_visibility="collapsed")

with right:
    st.markdown("## 🧠 BurakGPT")

    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "bot"
        st.markdown(
            f"<div class='chat {role}'>{m['content']}</div>",
            unsafe_allow_html=True
        )

    prompt = st.text_input(
        "",
        placeholder="Yaz kral… (örn: cyberpunk şehir çiz)"
    )
    send = st.button("🚀 Gönder")

# ---------------- ACTION ----------------
if send and prompt:
    st.session_state.messages.append({"role":"user","content":prompt})

    if "Görsel" in mode:
        with st.spinner("🎨 Görsel oluşturuluyor..."):
            payload = {
                "inputs": prompt,
                "parameters": {"steps": 35, "guidance_scale": 8.5}
            }

            r = requests.post(HF_URL, headers=HF_HEADERS, json=payload)

            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                blurred = img.filter(ImageFilter.GaussianBlur(16))

                holder = st.empty()
                holder.image(blurred, caption="Yükleniyor...")
                time.sleep(1.2)
                holder.image(img, caption="🖼️ Hazır")

                st.session_state.messages.append({
                    "role":"assistant",
                    "content":"Görsel hazır kral 🎨"
                })
            else:
                st.error("HF görsel üretim hatası")

    else:
        with st.spinner("🧠 Düşünüyorum..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )
            reply = res.choices[0].message.content
            st.session_state.messages.append(
                {"role":"assistant","content":reply}
            )
            st.rerun()
