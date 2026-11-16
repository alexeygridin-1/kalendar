import streamlit as st
from db import db_query
from datetime import datetime, timedelta
import time

# окно создания события
@st.dialog("Создать новое событие", width="large")
def create_event_modal(selected_ids):
    if not selected_ids:
        st.error("Сначала выберите календарь слева.")
        return

    cal_options = {}
    for cid in selected_ids:
        res = db_query("SELECT NAME, DEFAULT_DURATION FROM CALENDARS WHERE ID = ?", (cid,), fetch=True)
        if res:
            cal_options[res[0][0]] = (cid, res[0][1])

    target_name = st.selectbox("В какой календарь добавить?", options=list(cal_options.keys()))
    target_id, cal_default_duration = cal_options[target_name]

    default_name = ""
    if cal_default_duration:
        default_duration = cal_default_duration
    else:
        default_duration = 30
    default_all_day = False
    if st.session_state.get('selected_template_name'):
        default_name = st.session_state.selected_template_name
        default_duration = st.session_state.get('selected_template_duration', 60)
        default_all_day = st.session_state.get('selected_template_all_day', False)

    ev_name = st.text_input("Название события", value=default_name, key=f"ev_name_{default_name}_{default_duration}")
    ev_desc = st.text_area("Описание")

    is_all_day = st.toggle("Весь день", value=default_all_day)

    col1, col2 = st.columns(2)
    now = datetime.now()
    with col1:
        start_date = st.date_input("Дата начала", now)
    with col2:
        end_date = st.date_input("Дата окончания", now)

    if not is_all_day:
        c1, c2 = st.columns(2)
        with c1:
            start_time = st.time_input("Время начала", now.time())
        with c2:
            end_time = st.time_input("Время окончания", (now + timedelta(minutes=default_duration)).time())
    else:
        start_time = datetime.min.time()
        end_time = datetime.min.time()

    repeat = st.selectbox("Повторение",["Не повторять", "Каждый день", "Каждый будний день", "Каждую неделю", "Каждые 2 недели",
                           "Каждый месяц"])
    is_busy = st.toggle("Занят", value=True)
    remind_minutes = st.number_input("Напомнить за (мин)", min_value=0, value=15)

    # права для участников
    st.write("Права для участников:")
    c_ed, c_inv = st.columns(2)
    with c_ed:
        edit_rights = st.toggle("Могут редактировать", value=False)
    with c_inv:
        invite_rights = st.toggle("Могут приглашать", value=False)

    if st.button("Сохранить", type="primary"):
        if ev_name:
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)

            res = db_query("""INSERT INTO EVENTS (CALENDAR_ID, CREATOR_ID, NAME, INFO, START_TIME, END_TIME,
                    ALL_DAY, BUSY, EDIT_RIGHTS, INVITE_RIGHTS) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING ID
                    """, (target_id, st.session_state.user_id, ev_name, ev_desc, start_dt, end_dt,
                                 is_all_day, is_busy, edit_rights, invite_rights), fetch=True)

            if res:
                event_id = res[0][0]
                if repeat != "Не повторять":
                    final_freq, final_interval = "", 1
                    if repeat == "Каждый день":
                        final_freq = "DAILY"
                    elif repeat == "Каждый будний день":
                        final_freq = "WEEKDAYS"
                    elif repeat == "Каждую неделю":
                        final_freq = "WEEKLY"
                    elif repeat == "Каждые 2 недели":
                        final_freq, final_interval = "WEEKLY", 2
                    elif repeat == "Каждый месяц":
                        final_freq = "MONTHLY"
                    db_query("INSERT INTO RULES (EVENT_ID, FREQUENCY, INTERVAL) VALUES (?, ?, ?)",
                             (event_id, final_freq, final_interval))

                if remind_minutes > 0:
                    db_query("INSERT INTO NOTES (EVENT_ID, USER_ID, MINUTES, CHANNEL) VALUES (?, ?, ?, ?)",
                             (event_id, st.session_state.user_id, remind_minutes, "Push"))

                st.success("Событие создано!")
                st.session_state.selected_template_name = None
                st.session_state.show_create_modal = False
                time.sleep(1) # чтобы я успел увидеть
                st.rerun()


#  окно редактирования события
@st.dialog("Редактировать событие", width="large")
def edit_event_modal(ev_id, name, info, start, end):
    new_name = st.text_input("Название", value=name)
    new_info = st.text_area("Описание", value=info if info else "")
    new_start_date = st.date_input("Дата начала", value=start.date())
    new_start_time = st.time_input("Время начала", value=start.time())
    new_end_date = st.date_input("Дата окончания", value=end.date())
    new_end_time = st.time_input("Время окончания", value=end.time())

    if st.button("Сохранить изменения", type="primary"):
        new_start_dt = datetime.combine(new_start_date, new_start_time)
        new_end_dt = datetime.combine(new_end_date, new_end_time)
        db_query("UPDATE EVENTS SET NAME=?, INFO=?, START_TIME=?, END_TIME=? WHERE ID=?",
                 (new_name, new_info, new_start_dt, new_end_dt, ev_id))
        st.success("Обновлено!")
        time.sleep(1)
        st.rerun()
