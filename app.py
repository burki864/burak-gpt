# ---------------- IMAGE API ----------------
Z_IMAGE_API = st.secrets["Z_IMAGE_API"]  
# örnek secret değeri:
# https://mrflakename-z-image-turbo.hf.space/run/predict

def generate_image(prompt):
    try:
        payload = {
            "data": [
                prompt,
                8,   # steps
                0    # seed (random)
            ]
        }

        response = requests.post(
            Z_IMAGE_API,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            st.error(f"Z-Image Turbo hata: {response.status_code}")
            return None

        result = response.json()
        img_base64 = result["data"][0].split(",")[-1]

        image = Image.open(
            BytesIO(base64.b64decode(img_base64))
        )

        return image

    except Exception as e:
        st.error(f"Görsel hata: {e}")
        return None
