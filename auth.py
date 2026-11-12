import streamlit as st
from db import db_query

# отрисовка экрана и CSS чтобы сделать вход красивым
def show_auth_screen():
    st.markdown("""
        <style>
        /* ввод по центру */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            padding: 20px 30px;
            background-color: var(--secondary-background-color);
        }
        /* заголовок */
        .login-title {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        /* поля ввода и кнопки округлил */
        .stTextInput > div > div > input {
            border-radius: 8px;
        }
        .stButton > button {
            border-radius: 8px;
            font-weight: bold;
            height: 45px;
        }
        </style>
    """, unsafe_allow_html=True)

    # разделяю экран на 3 части чтобы поместить в центр
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # рамка вокруг формы входа
        with st.container(border=True):
            st.markdown('<div class="login-title">Яндекс Календарь</div>', unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Вход", "Регистрация"]) # вкладки для входа и регистрации

            with tab1:
                st.write("Войдите, чтобы продолжить")

                # st.form чтобы страница не перезагружалась при вводе - форма поля для ввода
                with st.form(key="login_form"):
                    login_email = st.text_input("Email", placeholder="Введите ваш email")
                    login_pass = st.text_input("Пароль", type="password", placeholder="Введите пароль")

                    # кнопка входа и проверка
                    submit_login = st.form_submit_button("Войти", use_container_width=True)
                    if submit_login:
                        if not login_email or not login_pass:
                            st.warning("Пожалуйста, заполните все поля.")
                        else:
                            with st.spinner("Проверка данных..."):
                                user = db_query("SELECT ID, NAME, SURNAME FROM USERS WHERE EMAIL = ? AND PASSWORD = ?",
                                                (login_email, login_pass), fetch=True)
                            # если нашел записываю его id в память
                            if user:
                                st.session_state.user_id = user[0][0]
                                st.session_state.user_name = f"{user[0][2]} {user[0][1]}"
                                st.rerun()
                            else:
                                st.error("Неверный email или пароль")

            with tab2:
                st.write("Создайте новый аккаунт")

                with st.form(key="register_form"):
                    reg_surname = st.text_input("Фамилия")
                    reg_name = st.text_input("Имя")
                    reg_email = st.text_input("Email", key="reg_email")
                    reg_phone = st.text_input("Телефон")
                    reg_pass = st.text_input("Пароль", type="password", key="reg_pass")

                    submit_register = st.form_submit_button("Зарегистрироваться", use_container_width=True)

                    if submit_register:
                        if not reg_email or not reg_pass or not reg_name or not reg_surname:
                            st.warning("Заполните обязательные поля (Фамилия, Имя, Email, Пароль)")
                        else:
                            existing_user = db_query("SELECT ID FROM USERS WHERE EMAIL = ?", (reg_email,), fetch=True)
                            if existing_user:
                                st.error("Пользователь с таким Email уже существует!")
                            else:
                                success = db_query(
                                    "INSERT INTO USERS (EMAIL, PHONE, PASSWORD, NAME, SURNAME) VALUES (?, ?, ?, ?, ?)",
                                    (reg_email, reg_phone, reg_pass, reg_name, reg_surname))
                                if success:
                                    st.success("Регистрация успешна! Теперь войдите во вкладке 'Вход'.")