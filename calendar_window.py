import streamlit as st
from db import db_query

# окно настроек календаря
@st.dialog("Настройки календаря") # функция откроется в красивом окне
# смена цвета, длительности и возможность поделиться доступом
def calendar_settings_modal(cal_id):
    cal_info = db_query("SELECT NAME, COLOR, DEFAULT_DURATION FROM CALENDARS WHERE ID = ?", (cal_id,), fetch=True)
    if not cal_info: return
    cal_name, cal_color, cal_duration = cal_info[0]

    st.markdown(f"{cal_name}")

    # настройка цвета
    st.write("Цвет календаря:")
    colors = ["#e74c3c", "#2ecc71", "#e67e22", "#9b59b6", "#3498db", "#f1c40f", "#95a5a6"]
    cols = st.columns(7)
    # прохожусь по индексам от 0 до 6 чтобы взять колонку и цвет
    for i in range(len(cols)):
        with cols[i]:
            color_hex = colors[i]
            st.markdown(f"""<style>
                div.st-key-settings_color_{i} button {{
                    background-color: {color_hex} !important; color: transparent !important;
                    border-radius: 50% !important; width: 26px !important; height: 26px !important;
                    min-width: 26px !important; min-height: 26px !important; padding: 0 !important;
                    border: 2px solid {'white' if cal_color == color_hex else 'transparent'} !important;
                    box-shadow: none !important; margin: 0 auto !important;
                }}
                div.st-key-settings_color_{i} button p {{ display: none !important; }}
                </style>""", unsafe_allow_html=True)
            if st.button(" ", key=f"settings_color_{i}"):
                db_query("UPDATE CALENDARS SET COLOR = ? WHERE ID = ?", (colors[i], cal_id))
                st.rerun()

    # настройка длительности
    new_duration = st.number_input("Длительность встречи по умолчанию (мин)", min_value=15, max_value=1440,
                                   value=cal_duration if cal_duration else 30, step=15)
    if st.button("Сохранить длительность"):
        db_query("UPDATE CALENDARS SET DEFAULT_DURATION = ? WHERE ID = ?", (new_duration, cal_id))
        st.success("Настройки сохранены!")
        st.rerun()

    st.divider()
    st.write("Доступ к календарю")
    shared_users = db_query("""SELECT U.NAME, U.SURNAME, S.ROLE FROM SHARES S
              JOIN USERS U ON S.USER_ID = U.ID WHERE S.CALENDAR_ID = ?""", (cal_id,), fetch=True)

    if shared_users:
        for u in shared_users:
            role_ru = "Редактор" if u[2] == 'editor' else "Читатель"
            st.caption(f"- {u[1]} {u[0]} ({role_ru})")
    else:
        st.caption("Пока никто не имеет доступа.")

    friend_email = st.text_input("Введите Email пользователя")
    role_ru = st.selectbox("Права доступа", ["Редактор", "Читатель"])
    role = "editor" if role_ru == "Редактор" else "reader"

    if st.button("Предоставить доступ", type="primary"):
        if friend_email:
            user = db_query("SELECT ID FROM USERS WHERE EMAIL = ?", (friend_email,), fetch=True)
            if user:
                existing = db_query("SELECT ID FROM SHARES WHERE CALENDAR_ID = ? AND USER_ID = ?", (cal_id, user[0][0]),
                                    fetch=True)
                if existing:
                    st.warning("У этого пользователя уже есть доступ.")
                else:
                    db_query("INSERT INTO SHARES (CALENDAR_ID, USER_ID, ROLE) VALUES (?, ?, ?)",
                             (cal_id, user[0][0], role))
                    st.success("Доступ выдан!")
                    st.rerun()
            else:
                st.error("Пользователь не найден.")


# окно создания календаря
@st.dialog("Создать новый календарь")
# собираю название, видимость, длительность, цвет
def create_calendar_modal():
    new_cal_name = st.text_input("Название календаря")

    visibility = st.selectbox("Кто видит события, которые я создаю", options=["Только участники", "Все пользователи"])

    if visibility == "Только участники":
        vis_db_value = "participants"
    else:
        vis_db_value = "all"

    is_main = st.checkbox("Использовать календарь как основной", value=False)

    new_duration = st.number_input("Длительность встречи по умолчанию (мин)", min_value=15, max_value=1440, value=30,
                                   step=15)

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f1c40f", "#9b59b6", "#e67e22", "#95a5a6"]
    cols = st.columns(7)
    for i in range(len(cols)):
        with cols[i]:
            color_hex = colors[i]
            st.markdown(f"""<style>
                div.st-key-color_btn_{i} button {{
                    background-color: {color_hex} !important; color: transparent !important;
                    border-radius: 50% !important; width: 28px !important; height: 28px !important;
                    min-width: 28px !important; min-height: 28px !important; padding: 0 !important;
                    border: 2px solid {'white' if st.session_state.selected_color == color_hex else 'transparent'} !important;
                    margin: 0 auto !important;
                }}
                div.st-key-color_btn_{i} button p {{ display: none !important; }}
                </style>""", unsafe_allow_html=True)
            if st.button(" ", key=f"color_btn_{i}"):
                st.session_state.selected_color = color_hex
                st.rerun()

    if st.button("Создать", type="primary", use_container_width=True):
        if new_cal_name:
            res = db_query("""INSERT INTO CALENDARS (OWNER_ID, NAME, COLOR, DEFAULT_DURATION, DEFAULT_VISIBILITY)
VALUES (?, ?, ?, ?, ?) RETURNING ID""", (st.session_state.user_id, new_cal_name,
                                         st.session_state.selected_color, new_duration, vis_db_value), fetch=True)

            if res:
                new_cal_id = res[0][0]
                if is_main:
                    db_query("UPDATE USERS SET MAIN_CALENDAR_ID = ? WHERE ID = ?",
                             (new_cal_id, st.session_state.user_id))

                st.success("Календарь создан!")
                st.rerun()


# окно создания шаблона
@st.dialog("Создать шаблон события")
def create_template_modal():
    tpl_name = st.text_input("Название шаблона")
    tpl_duration = st.number_input("Длительность (в минутах)", min_value=15, max_value=1440, value=60, step=15)
    if st.button("Сохранить шаблон", type="primary"):
        if tpl_name:
            db_query("INSERT INTO TEMPLATES (USER_ID, NAME, DURATION) VALUES (?, ?, ?)",
                     (st.session_state.user_id, tpl_name, tpl_duration))
            st.success("Шаблон создан!")
            st.rerun()
