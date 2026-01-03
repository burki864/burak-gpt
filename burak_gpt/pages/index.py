# burak_gpt/pages/index.py
import reflex as rx

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("🤖 BurakGPT", size="9"),
            rx.text("Render üzerinde çalışan profesyonel chatbot"),
            rx.button(
                "Başla",
                color_scheme="blue",
                size="lg"
            ),
            spacing="4",
        ),
        height="100vh",
    )

