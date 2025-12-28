import streamlit as st
from openai import OpenAI
from gradio_client import Client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="🧠 Burak GPT",
    page_icon="🧠",
    layout="wide"
)

# =========================
# CLIENTS
# =========================
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
image_client = Client("burak12321/burak-gpt-image")

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# STYLE (PROFESSIONAL)
# =========================
st.markdown("""
<style>
body {
    background-color: #0f172a;
}

.chat-user {
    background:#e0f2fe;
    color:#020617;
    padding:14px;
    border-radius:16px;
    margin:10px 0;
    max-width:70%;
    margin-left:auto;
}

.chat-bot {
    background:#1e293b;
    color:#f8fafc;
    padding:14px;
    border-radius:16px;
    margin:10px 0;
    max-width:70%;
}

.input-bar {
    background:#020617;
    padding:14px;
    border-radius:18px;
}

.send-btn button {
    background:#000 !important;
    color:#fff !important;
    border-radius:50% !important;
    height:44px;
    width:44px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("## 🧠 **Burak GPT**  \nYazı • Araştırma • Görsel")

# =========================
# CHAT HISTORY
# =========================
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='chat-user'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>{msg}</div>", unsafe_allow_html=True)

# =========================
# INPUT BAR
# =========================
col_mode, col_input, col_send = st.columns([1, 6, 1])

with col_mode:
    mode = st.selectbox(
        "",
        ["💬 Sohbet", "🔍 Araştırma", "🎨 Görsel"],
        label_visibility="collapsed"
    )

with col_input:
    user_input = st.text_input(
        "",
        placeholder="Burak GPT’ye yaz…",
        label_visibility="collapsed"
    )

with col_send:
    send = st.button("➤")

# =========================
# FUNCTIONS
# =========================
def burak_gpt(prompt, mode):
    system_style = {
        "💬 Sohbet": "Samimi, zeki, emoji kullanan bir asistansın.",
        "🔍 Araştırma": "Maddeli, net, öğretici anlat.",
    }

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_style.get(mode, "")},
            *[
                {"role": r, "content": m}
                for r, m in st.session_state.messages
            ],
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def generate_image(prompt):
    result = image_client.predict(
        prompt=prompt,
        api_name="/generate"
    )
    return result["url"]

# =========================
# ACTION
# =========================
if send and user_input:
    st.session_state.messages.append(("user", user_input))

    if mode == "🎨 Görsel":
        placeholder = st.empty()
        placeholder.markdown("""
        <div style="
        width:100%;
        height:420px;
        background:#020617;
        border-radius:16px;
        display:flex;
        align-items:center;
        justify-content:center;
        color:#94a3b8;
        font-size:18px;
        animation:pulse 1.5s infinite;">
        🎨 Burak GPT çiziyor…
        </div>

        <style>
        @keyframes pulse {
          0% { opacity:.4; }
          50% { opacity:1; }
          100% { opacity:.4; }
        }
        </style>
        """, unsafe_allow_html=True)

        try:
            img_url = generate_image(user_input)
            placeholder.image(img_url, use_container_width=True)
            st.download_button(
                "⬇️ Görseli indir",
                data=img_url,
                file_name="burakgpt.png"
            )
        except:
            placeholder.error("❌ Görsel üretilemedi. Biraz sonra tekrar dene.")

    else:
        with st.spinner("🧠 Burak GPT düşünüyor…"):
            reply = burak_gpt(user_input, mode)
        st.session_state.messages.append(("assistant", reply))
        st.rerun()
