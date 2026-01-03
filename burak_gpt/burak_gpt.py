import reflex as rx

class State(rx.State):
    pass

def index():
    return rx.center(
        rx.text("BurakGPT Online 🚀", font_size="2em")
    )

app = rx.App()
app.add_page(index)
