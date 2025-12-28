import gradio as gr
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import io
import base64

# ========== MODEL ==========
MODEL_ID = "runwayml/stable-diffusion-v1-5"

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float32
)
pipe = pipe.to("cpu")

# ========== MEMORY ==========
chat_memory = []

def chat_response(message, mode):
    global chat_memory

    if mode == "Yazı":
        reply = f"🧠 **Burak GPT:** {message} üzerine düşünüyorum...\n\nBu konuda detaylı bir cevap hazırlayabilirim."
        chat_memory.append((message, reply))
        return chat_memory, None

    elif mode == "Görsel":
        image = pipe(
            prompt=message,
            num_inference_steps=20,
            guidance_scale=7.5
        ).images[0]

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        reply = f"🎨 **Burak GPT çiziyor:** `{message}`"
        chat_memory.append((message, reply))

        return chat_memory, f"data:image/png;base64,{img_base64}"

# ========== TASARIM ==========
css = """
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
.gradio-container {
    max-width: 1000px !important;
}
#chatbox {
    height: 420px;
    overflow-y: auto;
}
"""

# ========== UI ==========
with gr.Blocks(css=css, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🧠 Burak GPT
        **Yazı • Araştırma • Görsel üretimi**  
        Profesyonel yapay zeka arayüzü
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            mode = gr.Radio(
                ["Yazı", "Görsel"],
                value="Yazı",
                label="🛠️ Mod"
            )

        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                elem_id="chatbox",
                label="💬 Sohbet"
            )

    with gr.Row():
        user_input = gr.Textbox(
            placeholder="Mesajını yaz...",
            show_label=False,
            scale=4
        )
        send_btn = gr.Button("➤", scale=1)

    image_output = gr.Image(
        label="🖼️ Üretilen Görsel",
        visible=True
    )

    send_btn.click(
        fn=chat_response,
        inputs=[user_input, mode],
        outputs=[chatbot, image_output]
    )

demo.launch()
