import streamlit as st

# ---------- AYAR ----------
st.set_page_config(page_title="Burak GPT", layout="wide")

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None

if "show_login" not in st.session_state:
    st.session_state.show_login = False

if "show_register" not in st.session_state:
    st.session_state.show_register = False


# ---------- CSS ----------
st.markdown("""
<style>
.menu-text {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ---------- HEADER ----------
col1, col2, col3 = st.columns([6,2,2])

with col1:
    st.markdown("## 🤖 **Burak GPT Image**")

with col2:
    if st.session_state.user is None:
        if st.button("Giriş Yap", key="open_login"):
            st.session_state.show_login = True
            st.session_state.show_register = False
    else:
        st.markdown("")

with col3:
    if st.session_state.user is None:
        if st.button("Kayıt Ol", key="open_register"):
            st.session_state.show_register = True
            st.session_state.show_login = False
    else:
        with st.popover("👤 Profil"):
            st.write("**Ad:**", st.session_state.user["name"])
            st.write("**Email:**", st.session_state.user["email"])
            if st.button("Çıkış Yap", key="logout"):
                st.session_state.user = None
                st.rerun()


st.divider()

# ---------- LOGIN POPUP ----------
if st.session_state.show_login:
    st.subheader("🔐 Giriş Yap")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")

        if submit:
            if email and password:
                st.session_state.user = {
                    "name": "Kullanıcı",
                    "email": email
                }
                st.session_state.show_login = False
                st.success("Giriş başarılı ✅")
                st.rerun()
            else:
                st.error("Email ve şifre zorunlu")

# ---------- REGISTER POPUP ----------
if st.session_state.show_register:
    st.subheader("📝 Kayıt Ol")

    with st.form("register_form"):
        name = st.text_input("Ad *")
        surname = st.text_input("Soyad (isteğe bağlı)")
        email = st.text_input("Email")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Kayıt Ol")

        if submit:
            if name and email and password:
                st.session_state.user = {
                    "name": f"{name} {surname}".strip(),
                    "email": email
                }
                st.session_state.show_register = False
                st.success("Kayıt başarılı 🎉")
                st.rerun()
            else:
                st.error("Ad, Email ve Şifre zorunlu")


# ---------- MAIN ----------
st.markdown("### 🎨 Görsel Oluştur")

if st.session_state.user is None:
    st.info("Hesapsız 1–2 görsel oluşturabilirsin. Sınırsız için giriş yap.")
else:
    st.success("Sınırsız kullanım aktif 🚀")

prompt = st.text_input("Prompt gir")

if st.button("Görsel Oluştur", key="generate_image"):
    if prompt:
        st.image("https://placehold.co/512x512", caption="Örnek çıktı")
    else:
        st.warning("Prompt gir kral 😄")
