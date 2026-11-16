from firebird.driver import connect
import streamlit as st

DB_CONFIG = {
    'database': 'localhost:/db/kalendar.fdb',
    'user': 'SYSDBA',
    'password': 'masterkey'
}

# команды, данные для подстановки, флаг с запросом данных из бд, сохранение
def db_query(query, params=(), fetch=False):
    # если не получится сделать команды ниже то переход к except и вывод ошибки
    try:
        # закрывает базу данных
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
            # fetchall при запросе забирает, сохраняет и возвращает данные
            if fetch:
                result = cur.fetchall()
                con.commit() # кнопка сохранить
                return result

            con.commit()
            return True
    except Exception as e:
        st.error(f"Ошибка базы данных: {e}")
        return None
