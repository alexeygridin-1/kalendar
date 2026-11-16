import streamlit as st
from db import db_query
from streamlit_calendar import calendar

def show_calendar_grid(start_filter, end_filter):
    if not st.session_state.selected_calendar_ids: return
    placeholders = ""
    for _ in range(len(st.session_state.selected_calendar_ids)):
        placeholders = placeholders + "?,"
    placeholders = placeholders[:-1]
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