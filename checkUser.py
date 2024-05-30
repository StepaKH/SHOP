import sqlite3
def get_user_data(user_id):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    # Выполняем запрос к базе данных
    cur.execute("SELECT * FROM users WHERE tgId = ?", (user_id,))

    # Получаем результат запроса
    user_data = cur.fetchone()

    cur.close()
    conn.close()

    return user_data