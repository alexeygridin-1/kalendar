import streamlit as st
from auth import show_auth_screen
from calendars import show_sidebar
from events import show_events_ui

# открываю новую вкладку и называю календарь
st.set_page_config(page_title="Мой Календарь", layout="wide")

# память сайта: логин и пароль, календарь с галочкой, цвет календаря и т.д.
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = ""

if 'selected_calendar_ids' not in st.session_state:
    st.session_state.selected_calendar_ids = []

if 'selected_color' not in st.session_state:
    st.session_state.selected_color = "#3498db"

if 'show_create_modal' not in st.session_state:
    st.session_state.show_create_modal = False

if 'selected_template_name' not in st.session_state:
    st.session_state.selected_template_name = None

if 'selected_template_duration' not in st.session_state:
    st.session_state.selected_template_duration = None

if 'selected_template_all_day' not in st.session_state:
    st.session_state.selected_template_all_day = False
# программа смотрит в блокнот памяти. если там пусто то показывает экран входа иначе календари и сообытия
if st.session_state.user_id is None:
    show_auth_screen()
else:
    show_sidebar() # левое меню
    show_events_ui() # правая часть