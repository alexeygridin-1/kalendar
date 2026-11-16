import streamlit as st
from db import db_query
from datetime import datetime, timedelta
from calendar_net import show_calendar_grid
from event_window import create_event_modal, edit_event_modal
from participants import show_event_participants, invite_users_modal

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
                    # проверяю права при показе кнопки Ред.
                    if creator_id == st.session_state.user_id or edit_rights:
                        if st.button("Ред.", key=f"edit_{ev_id}"):
                            edit_event_modal(ev_id, name, info, start, end)

                    if creator_id == st.session_state.user_id or invite_rights:
                        if st.button("Пригласить", key=f"inv_{ev_id}"):
                            invite_users_modal(ev_id)

                    # удаление связанных записей
                    if creator_id == st.session_state.user_id:
                        with st.popover("Удалить"):
                            st.write("Вы уверены?")
                            if st.button("Да, удалить", key=f"del_{ev_id}", type="primary"):
                                db_query("DELETE FROM NOTES WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM MEMBERS WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM RULES WHERE EVENT_ID = ?", (ev_id,))
                                db_query("DELETE FROM EVENTS WHERE ID = ?", (ev_id,))
                                st.rerun()
