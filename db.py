from firebird.driver import connect
import streamlit as st

DB_CONFIG = {
    'database': 'localhost:/db/kalendar.fdb',
    'user': 'SYSDBA',
    'password': 'masterkey'
}

# текст sql команд, данные для подстановки, флаг с запросом данных из бд или просто сохранить
def db_query(query, params=(), fetch=False):
    # попробуй сделать что ниже, если не получится то переход в except и вывод ошибки
    try:
        # дверь к бд, with закрывает когда выхожу
        with connect(
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        ) as con:
            if con is None:
                st.error("Не удалось подключиться к базе данных.")
                return None
            cur = con.cursor()
            cur.execute(query, params)  # команда выполняю действие, текст и данные которые я подставлю
            # если просил данные то fetchall их забирает, сохраняет и возвращает
            if fetch:
                result = cur.fetchall()
                con.commit() # кнопка сохранить
                return result

            con.commit()
            return True
    except Exception as e:
        st.error(f"Ошибка базы данных: {e}")
        return None