import sqlite3

def get_product_data(token):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    # Выполняем запрос к базе данных
    cur.execute("SELECT * FROM tokens WHERE token = ?", (token,))

    # Получаем результат запроса
    product_data = cur.fetchone()

    cur.close()
    conn.close()

    return product_data