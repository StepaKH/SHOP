import telebot
import config
import random
import sqlite3

bot = telebot.TeleBot(config.TOKEN)


def generate_unique_token():
    existing_tokens = set()
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM tokens')
    items = cur.fetchall()
    # Получаем результат запроса
    for el in items:
        existing_tokens.add(int(el[4]))
    cur.close()
    conn.close()
    available_tokens = set(range(1, 4)) - existing_tokens
    if not available_tokens:
        return None
    return random.choice(list(available_tokens))


def delete_art(token):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()
    cur.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    cur.close()
    conn.close()
