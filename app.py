import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io

# Sayfa ayarları
st.set_page_config(
    page_title="BurakGPT",
    page_icon="🧠",
    layout="centered"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🧠 Burak GPT")
st.caption("Yaz • Araştır • Görsel oluştur")

# Mod seçimi
mode = st.selectbox(
    "Mod",
    ["Yazı", "Araştırma", "Görsel"],
    index=2
)

prompt = st.text_input("Ne istiyorsun kral?", placeholder="istanbul manzarası")

# === GÖRSEL MODU ===
if mode == "Görsel" and prompt:
    if st.button("🎨 Görsel oluştur"):
        with st.spinner("🎨 BurakGPT çiziyor..."):
            try:
                result = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size="512x512"
                )

                image_base64 = result.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(io.BytesIO(image_bytes))

                st.markdown("### 🖼 Oluşturulan Görsel")
                st.image(image, width=300)  # 👈 KÜÇÜK + KARE

            except Exception as e:
                st.error("Görsel oluşturulamadı 😕")
                st.code(str(e))

# === YAZI MODU (kısaca hazır dursun) ===
elif mode != "Görsel" and prompt:
    with st.spinner("BurakGPT düşünüyor..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        st.markdown(response.choices[0].message.content)
