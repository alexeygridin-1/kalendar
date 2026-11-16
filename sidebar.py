import streamlit as st
from db import db_query
from calendar_window import create_calendar_modal, create_template_modal, calendar_settings_modal

# левое меню
def show_sidebar():
    with st.sidebar:
        # профиль пользователя и кнопка выхода
        col_user, col_logout = st.columns([3, 1])
        with col_user:
            st.markdown(f"{st.session_state.user_name}")
        with col_logout:
            # очистка памяти и переход на экран входа
            if st.button("Выйти", key="logout_btn", type="secondary"):
                st.session_state.user_id = None
                st.session_state.selected_calendar_ids = []
                st.rerun()

        st.divider()

        st.markdown("""<style>
            div.st-key-create_btn button {
                background-color: #ffdb4d !important; color: #000000 !important;
                font-weight: bold !important; border-radius: 8px !important;
                border: none !important; padding: 10px !important; margin-bottom: 20px;
            }
            div.st-key-create_btn button:hover { background-color: #ffcc00 !important; }
            div[data-testid="stPopoverBody"] .stButton > button {
                border: none !important; background-color: transparent !important;
                text-align: left !important; justify-content: flex-start !important;
                padding: 8px 10px !important; font-weight: normal !important;
                font-size: 14px !important; color: inherit !important;
            }
            div[data-testid="stPopoverBody"] .stButton > button:hover { background-color: rgba(128, 128, 128, 0.1) !important; }
            div[data-testid="stPopoverBody"] div[class*="st-key-del_"] button { color: #e74c3c !important; }
            div[data-testid="stPopoverBody"] div[class*="st-key-del_"] button:hover { background-color: rgba(231, 76, 60, 0.1) !important; }
            .stCheckbox { margin-bottom: -15px; }
            </style>""", unsafe_allow_html=True)
        # открытие окна создания в правой части
        if st.button("+ Создать событие", key="create_btn", use_container_width=True):
            st.session_state.selected_template_name = None
            st.session_state.selected_template_duration = None
            st.session_state.selected_template_all_day = False
            st.session_state.show_create_modal = True

        col_title, col_add = st.columns([4, 1])
        with col_title:
            st.markdown("Мои календари")
        with col_add:
            if st.button("+", help="Добавить календарь", key="add_cal_btn"):
                create_calendar_modal()
        # достаю список календарей по алфавиту
        calendars = db_query("""SELECT C.ID, C.NAME, C.COLOR, U.MAIN_CALENDAR_ID, C.OWNER_ID, S.ROLE
        FROM CALENDARS C JOIN USERS U ON C.OWNER_ID = U.ID LEFT JOIN SHARES S ON C.ID = S.CALENDAR_ID AND S.USER_ID = ?
        WHERE C.OWNER_ID = ? OR S.USER_ID = ? ORDER BY C.NAME
            """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id), fetch=True)

        # основной календарь ставлю на первое место
        if calendars:
            main_cals = []
            other_cals = []

            for c in calendars:
                if c[0] == c[3]:  # если ID календаря совпадает с ID основного
                    main_cals.append(c)
                else:
                    other_cals.append(c)

            calendars = main_cals + other_cals

        if calendars:
            if not st.session_state.selected_calendar_ids:
                for cal in calendars:
                    if cal[3] == cal[0]:
                        st.session_state.selected_calendar_ids.append(cal[0])
                        break

            for cal in calendars:
                cal_id, name, color, main_cal_id, owner_id, shared_role = cal
                is_main = (cal_id == main_cal_id)
                label = f"{name} (Осн.)" if is_main else name

                col_cb, col_menu = st.columns([5, 1])
                with col_cb:
                    st.markdown(
                        f"""<div style="display: flex; align-items: center;"><div style="background-color:{color}; width:14px; height:14px; border-radius:50%; margin-right:8px; margin-top:-15px;"></div></div>""",
                        unsafe_allow_html=True)
                    # рисую галочку, при нажатии id календаря добавляю или удаляю из памяти
                    is_checked = st.checkbox(label, value=(cal_id in st.session_state.selected_calendar_ids),
                                             key=f"cb_{cal_id}")
                    if is_checked and cal_id not in st.session_state.selected_calendar_ids:
                        st.session_state.selected_calendar_ids.append(cal_id)
                        st.rerun()
                    elif not is_checked and cal_id in st.session_state.selected_calendar_ids:
                        st.session_state.selected_calendar_ids.remove(cal_id)
                        st.rerun()

                with col_menu:
                    if owner_id == st.session_state.user_id:
                        # кнопка доп настройки - 3 точки рядом с календарем
                        with st.popover("⋮"):
                            st.markdown("<p style='margin-bottom: 5px; font-size: 14px;'>Цвет:</p>",
                                        unsafe_allow_html=True)
                            c_cols = st.columns(7)
                            palette = ["#e74c3c", "#2ecc71", "#e67e22", "#9b59b6", "#3498db", "#f1c40f", "#95a5a6"]
                            for i, p_col in enumerate(c_cols):
                                with p_col:
                                    st.markdown(f"""<style>
                                        div[data-testid="stPopoverBody"] div.st-key-upd_color_{cal_id}_{i} button {{
                                            background-color: {palette[i]} !important; color: transparent !important;
                                            border-radius: 50% !important; width: 24px !important; height: 24px !important;
                                            min-width: 24px !important; min-height: 24px !important; padding: 0 !important;
                                            border: 2px solid {'white' if color == palette[i] else 'transparent'} !important;
                                            margin: 0 auto !important;
                                        }}
                                        div[data-testid="stPopoverBody"] div.st-key-upd_color_{cal_id}_{i} button p {{ display: none !important; }}
                                        </style>""", unsafe_allow_html=True)
                                    if st.button(" ", key=f"upd_color_{cal_id}_{i}"):
                                        db_query("UPDATE CALENDARS SET COLOR = ? WHERE ID = ?", (palette[i], cal_id))
                                        st.rerun()

                            st.divider()

                            if st.button("Показать только этот календарь", key=f"only_{cal_id}",
                                         use_container_width=True):
                                st.session_state.selected_calendar_ids = [cal_id]
                                for c in calendars:
                                    if f"cb_{c[0]}" in st.session_state: del st.session_state[f"cb_{c[0]}"]
                                st.rerun()

                            if not is_main:
                                if st.button("Сделать основным календарём", key=f"main_{cal_id}",
                                             use_container_width=True):
                                    db_query("UPDATE USERS SET MAIN_CALENDAR_ID = ? WHERE ID = ?",
                                             (cal_id, st.session_state.user_id))
                                    st.rerun()

                            if st.button("Открыть настройки", key=f"settings_{cal_id}", use_container_width=True):
                                calendar_settings_modal(cal_id)

                            st.divider()

                            if st.button("Удалить календарь", key=f"del_{cal_id}", use_container_width=True):
                                events = db_query("SELECT ID FROM EVENTS WHERE CALENDAR_ID = ?", (cal_id,), fetch=True)
                                if events:
                                    for e in events:
                                        db_query("DELETE FROM NOTES WHERE EVENT_ID = ?", (e[0],))
                                        db_query("DELETE FROM MEMBERS WHERE EVENT_ID = ?", (e[0],))
                                        db_query("DELETE FROM RULES WHERE EVENT_ID = ?", (e[0],))
                                db_query("DELETE FROM EVENTS WHERE CALENDAR_ID = ?", (cal_id,))
                                db_query("DELETE FROM SHARES WHERE CALENDAR_ID = ?", (cal_id,))
                                db_query("DELETE FROM CALENDARS WHERE ID = ?", (cal_id,))
                                if cal_id in st.session_state.selected_calendar_ids:
                                    st.session_state.selected_calendar_ids.remove(cal_id)
                                st.rerun()

        st.divider()
        col_tpl, col_add_tpl = st.columns([4, 1])
        with col_tpl:
            st.markdown("Шаблоны событий")
        with col_add_tpl:
            if st.button("+", help="Создать свой шаблон", key="add_tpl_btn"):
                create_template_modal()

        db_templates = db_query("SELECT ID, NAME, DURATION FROM TEMPLATES WHERE USER_ID = ?",
                                (st.session_state.user_id,), fetch=True)
        if db_templates:
            for tpl in db_templates:
                tpl_id, tpl_name, tpl_duration = tpl
                if st.button(f"{tpl_name}\n{tpl_duration} мин.", key=f"tpl_db_{tpl_id}", use_container_width=True):
                    st.session_state.selected_template_name = tpl_name
                    st.session_state.selected_template_duration = tpl_duration
                    st.session_state.selected_template_all_day = False
                    st.session_state.show_create_modal = True
                    st.rerun()

        default_templates = [
            {"id": 1, "title": "День рождения", "subtitle": "Весь день • ежегодно", "bg": "#fce4ec", "fg": "#d81b60",
             "duration": 1440, "all_day": True},
            {"id": 2, "title": "Не забыть", "subtitle": "Весь день", "bg": "#fff9c4", "fg": "#fbc02d", "duration": 1440,
             "all_day": True},
            {"id": 3, "title": "Запись к врачу", "subtitle": "15:00–16:00", "bg": "#e3f2fd", "fg": "#1976d2",
             "duration": 60, "all_day": False},
            {"id": 4, "title": "Тренировка", "subtitle": "18:00–19:00 • пн/ср/пт", "bg": "#e8f5e9", "fg": "#388e3c",
             "duration": 60, "all_day": False}
        ]

        for tpl in default_templates:
            btn_key = f"hardcoded_tpl_{tpl['id']}"
            st.markdown(f"""<style>
                div.st-key-{btn_key} button {{
                    background-color: {tpl['bg']} !important; border: none !important;
                    border-radius: 10px !important; padding: 10px 15px !important;
                    width: 100% !important; text-align: left !important; display: block !important;
                    height: auto !important; margin-bottom: 5px !important;
                }}
                div.st-key-{btn_key} button:focus:not(:active) {{ border-color: transparent !important; }}
                div.st-key-{btn_key} button p {{ color: {tpl['fg']} !important; margin: 0 !important; text-align: left !important; }}
                div.st-key-{btn_key} button p:first-child {{ font-weight: bold !important; font-size: 14px !important; margin-bottom: 2px !important; }}
                div.st-key-{btn_key} button p:last-child {{ font-size: 12px !important; opacity: 0.8 !important; }}
                div.st-key-{btn_key} button:hover {{ opacity: 0.8 !important; background-color: {tpl['bg']} !important; }}
                </style>""", unsafe_allow_html=True)

            if st.button(f"{tpl['title']}\n{tpl['subtitle']}", key=btn_key, use_container_width=True):
                st.session_state.selected_template_name = tpl['title']
                st.session_state.selected_template_duration = tpl['duration']
                st.session_state.selected_template_all_day = tpl['all_day']
                st.session_state.show_create_modal = True
                st.rerun()
