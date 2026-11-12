import streamlit as st
from db import db_query

# показываю кто приглашен, достаю список людей
def show_event_participants(event_id, creator_id):
    members = db_query("""SELECT U.ID, U.NAME, U.SURNAME, M.STATUS FROM MEMBERS M
                    JOIN USERS U ON M.USER_ID = U.ID WHERE M.EVENT_ID = ?""", (event_id,), fetch=True)

    if members:
        st.write("Участники:")
        for m in members:
            user_id, name, surname, status = m

            if status == 'accepted':
                status_text = ":green[Пойдет]"
            elif status == 'declined':
                status_text = ":red[Не пойдет]"
            else:
                status_text = ":orange[Ожидает]"

            if user_id == st.session_state.user_id:
                st.write(f"- {surname} {name} (Вы) — {status_text}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Пойду", key=f"acc_{event_id}"):
                        db_query("UPDATE MEMBERS SET STATUS = 'accepted' WHERE EVENT_ID = ? AND USER_ID = ?",
                                 (event_id, user_id))
                        st.rerun()
                with col2:
                    if st.button("Не пойду", key=f"dec_{event_id}"):
                        db_query("UPDATE MEMBERS SET STATUS = 'declined' WHERE EVENT_ID = ? AND USER_ID = ?",
                                 (event_id, user_id))
                        st.rerun()
            else:
                st.write(f"- {surname} {name} — {status_text}")


@st.dialog("Пригласить участников")
def invite_users_modal(event_id):
    all_users = db_query("SELECT EMAIL, NAME, SURNAME FROM USERS WHERE ID != ?", (st.session_state.user_id,),
                         fetch=True)

    if all_users:
        # создаю пустой список и циклом заполняю его
        emails = []
        for u in all_users:
            email_str = u[2] + " " + u[1] + " (" + u[0] + ")"
            emails.append(email_str)

        selected_emails = st.multiselect("Выберите пользователей", options=emails)

        if st.button("Пригласить", type="primary"):
            for full_str in selected_emails:
                parts = full_str.split('(')
                email = parts[1].rstrip(')')

                user = db_query("SELECT ID FROM USERS WHERE EMAIL = ?", (email,), fetch=True)
                if user:
                    existing = db_query("SELECT ID FROM MEMBERS WHERE EVENT_ID = ? AND USER_ID = ?",
                                        (event_id, user[0][0]), fetch=True)
                    if not existing:
                        db_query("INSERT INTO MEMBERS (EVENT_ID, USER_ID, STATUS) VALUES (?, ?, 'pending')",
                                 (event_id, user[0][0]))
            st.success("Участники приглашены!")
            st.rerun()