import streamlit as st
from db import db_query
from datetime import datetime, timedelta
import time
from streamlit_calendar import calendar
from participants import show_event_participants, invite_users_modal

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


def show_calendar_grid(start_filter, end_filter):
    if not st.session_state.selected_calendar_ids: return
    placeholders = ""
    for _ in range(len(st.session_state.selected_calendar_ids)):
        placeholders = placeholders + "?,"
    placeholders = placeholders[:-1]  # убираю самую последнюю запятую
    query = f"SELECT E.ID, E.NAME, E.START_TIME, E.END_TIME, C.COLOR FROM EVENTS E JOIN CALENDARS C ON E.CALENDAR_ID = C.ID WHERE E.CALENDAR_ID IN ({placeholders}) AND E.START_TIME >= ? AND E.START_TIME < ?"
    params = tuple(st.session_state.selected_calendar_ids) + (start_filter, end_filter)
    events = db_query(query, params, fetch=True)

    calendar_events = []
    if events:
        for ev in events:
            ev_id, name, start, end, color = ev
            calendar_events.append({"id": str(ev_id), "title": name, "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "end": end.strftime("%Y-%m-%dT%H:%M:%S"), "color": color if color else "#3498db"})

    calendar_options = {"headerToolbar": {"left": "today prev,next", "center": "title",
                                          "right": "dayGridMonth,timeGridWeek,timeGridDay"},
                        "initialView": "dayGridMonth", "locale": "ru",
                        "buttonText": {"today": "Сегодня", "month": "Месяц", "week": "Неделя", "day": "День"},
                        "height": "700px"}
    custom_css = """.fc .fc-button-primary { background-color: #ffffff !important; color: #333333 !important; border: 1px solid #d1d5db !important; border-radius: 8px !important; }
        .fc .fc-button-primary.fc-button-active { background-color: #111827 !important; color: #ffffff !important; }
        .fc-day-today { background-color: #fef08a !important; }"""
    calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)


def show_events_ui():
    if st.session_state.get('show_create_modal', False):
        st.session_state.show_create_modal = False
        create_event_modal(st.session_state.selected_calendar_ids)

    if not st.session_state.selected_calendar_ids:
        st.info("<- Поставьте галочку на календаре в меню слева.")
        return

    if len(st.session_state.selected_calendar_ids) == 1:
        cal_info = db_query("SELECT NAME FROM CALENDARS WHERE ID = ?", (st.session_state.selected_calendar_ids[0],),
                            fetch=True)
        title_name = cal_info[0][0] if cal_info else "Календарь"
    else:
        title_name = "Выбранные календари"

    st.title(f"События: {title_name}")

    view_mode = st.selectbox("Режим отображения", ["1 день", "3 дня", "5 дней", "7 дней", "Месяц", "Расписание"])
    today = datetime.now()
    start_filter = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if view_mode == "1 день":
        end_filter = start_filter + timedelta(days=1)
    elif view_mode == "3 дня":
        end_filter = start_filter + timedelta(days=3)
    elif view_mode == "5 дней":
        end_filter = start_filter + timedelta(days=5)
    elif view_mode == "7 дней":
        end_filter = start_filter + timedelta(days=7)
    elif view_mode == "Месяц":
        start_filter = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_filter = start_filter.replace(year=today.year + 1, month=1) if today.month == 12 else start_filter.replace(
            month=today.month + 1)
    else:
        start_filter = datetime(2000, 1, 1)
        end_filter = datetime(2100, 1, 1)

    search_query = st.text_input("Поиск по названию события", placeholder="Введите название...")
    view_type = st.radio("Вид", ["Список", "Сетка календаря"], horizontal=True)
    st.divider()

    if view_type == "Сетка календаря":
        show_calendar_grid(start_filter, end_filter)
        return

    placeholders = ""
    for _ in range(len(st.session_state.selected_calendar_ids)):
        placeholders = placeholders + "?,"
    placeholders = placeholders[:-1]
    query = f"""SELECT E.ID, E.NAME, E.START_TIME, E.END_TIME, E.INFO, E.BUSY, E.CREATOR_ID, E.EDIT_RIGHTS, E.INVITE_RIGHTS,
        R.FREQUENCY, R.INTERVAL, N.MINUTES, C.COLOR, M.STATUS as MY_STATUS FROM EVENTS E
        JOIN CALENDARS C ON E.CALENDAR_ID = C.ID LEFT JOIN RULES R ON E.ID = R.EVENT_ID
        LEFT JOIN NOTES N ON E.ID = N.EVENT_ID LEFT JOIN MEMBERS M ON E.ID = M.EVENT_ID AND M.USER_ID = ?
        WHERE E.CALENDAR_ID IN ({placeholders}) AND E.START_TIME >= ? AND E.START_TIME < ?"""
    params = [st.session_state.user_id] + list(st.session_state.selected_calendar_ids) + [start_filter, end_filter]

    if search_query:
        query += " AND E.NAME LIKE ?"
        params.append(f"%{search_query}%")
    query += " ORDER BY E.START_TIME"

    events = db_query(query, tuple(params), fetch=True)

    if not events:
        st.info(f"На этот период событий нет.")
    else:
        for ev in events:
            ev_id, name, start, end, info, busy, creator_id, edit_rights, invite_rights, freq, interval, remind_min, cal_color = ev

            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    status_color = "#e74c3c" if busy else "#2ecc71"
                    status_text = "Занят" if busy else "Свободен"

                    freq_text = ""
                    if freq:
                        if interval and interval > 1:
                            freq_text = f" | Повтор: каждые {interval} "
                            if freq == "DAILY":
                                freq_text += "дн."
                            elif freq == "WEEKLY":
                                freq_text += "нед."
                            elif freq == "MONTHLY":
                                freq_text += "мес."
                        else:
                            if freq == "DAILY":
                                freq_text = " | Повтор: каждый день"
                            elif freq == "WEEKDAYS":
                                freq_text = " | Повтор: по будням"
                            elif freq == "WEEKLY":
                                freq_text = " | Повтор: каждую неделю"
                            elif freq == "MONTHLY":
                                freq_text = " | Повтор: каждый месяц"

                    remind_text = f" | Напомнить за {remind_min} мин." if remind_min else ""

                    st.markdown(f"""
                    <div style="border-left: 5px solid {cal_color}; padding-left: 15px; margin-bottom: 10px;">
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                            <span style="color: {status_color};">{status_text}</span> {name}
                        </div>
                        <div style="color: gray; font-size: 14px; margin: 0;">
                            Время: {start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%H:%M')}{freq_text}{remind_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if info: st.write(info)

                    st.divider()
                    show_event_participants(ev_id, creator_id)

                with col_b:
                    # учитываю права edit_rights при показе кнопки Ред.
                    if creator_id == st.session_state.user_id or edit_rights:
                        if st.button("Ред.", key=f"edit_{ev_id}"):
                            edit_event_modal(ev_id, name, info, start, end)

                    if creator_id == st.session_state.user_id or invite_rights:
                        if st.button("Пригласить", key=f"inv_{ev_id}"):
                            invite_users_modal(ev_id)

                    # учитываю каскадное удаление связанных записей
                    if creator_id == st.session_state.user_id:
                        with st.popover("Удалить"):
                            st.write("Вы уверены?")
                            if st.button("Да, удалить", key=f"del_{ev_id}", type="primary"):
                                db_query("DELETE FROM NOTES WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM MEMBERS WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM RULES WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM EVENTS WHERE ID = ?", (ev_id,))
                                st.rerun()