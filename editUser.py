import sqlite3


def update_user_name(new_name, user_id):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    # Выполняем SQL-запрос на обновление имени пользователя
    cur.execute("UPDATE users SET name = ? WHERE tgId = ?", (new_name, user_id))
    conn.commit()

    cur.close()
    conn.close()


def update_user_phone(new_phone, user_id):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    # Выполняем SQL-запрос на обновление имени пользователя
    cur.execute("UPDATE users SET phone = ? WHERE tgId = ?", (new_phone, user_id))
    conn.commit()

    cur.close()
    conn.close()


def update_user_all(new_phone, new_name, user_id):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    # Выполняем SQL-запрос на обновление имени пользователя
    cur.execute("UPDATE users SET name = ? WHERE tgId = ?", (new_name, user_id))
    cur.execute("UPDATE users SET phone = ? WHERE tgId = ?", (new_phone, user_id))
    conn.commit()

    cur.close()
    conn.close()


def update_user_card(card, user_id):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    cur.execute("UPDATE users SET has_card = ? WHERE tgId = ?", (card, user_id))
    conn.commit()

    cur.close()
    conn.close()
