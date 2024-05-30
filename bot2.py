import os
import re
import sqlite3

import telebot
from telebot import types

import config
import getInfAboutProduct
import takeToken

name_product = None
photo_product = None
price_product = None
width_product = None

button_states = True

bot = telebot.TeleBot(config.TOKEN2)
bot.set_webhook()


def mainKeyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bottom1 = types.KeyboardButton("главная")
    bottom2 = types.KeyboardButton("удалить товар")
    bottom3 = types.KeyboardButton("получить артикул")
    markup.row(bottom1, bottom2)
    markup.add(bottom3)
    bot.send_message(message.chat.id, "Доступные команды:", reply_markup=markup)


@bot.message_handler(commands=['start', 'main', 'hello'])
@bot.message_handler(func=lambda message: message.text.lower() == 'главная')
def start(message):
    global button_states
    button_states = True
    # DB
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS tokens (id int auto_increment primary key, name varchar(255), '
        'price varchar(20) default(NULL), width varchar(20) default(NULL), token varchar(20) default(NULL))')

    conn.commit()
    cur.close()
    conn.close()
    ###

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Получить артикул")
    btn2 = types.KeyboardButton("Удалить товар")
    markup.row(btn1, btn2)

    bot.send_message(message.chat.id,
                     "Нажмите на кнопку <b><u>получить артикул</u></b>, после чего внесите все необходимые данные, или нажмите на кнопку <b><u>удалить товар</u></b>, после чего внесите артикул товара, который нужно убрать из базы данных",
                     parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['delete'])
@bot.message_handler(func=lambda message: message.text.lower() == 'удалить товар')
def getart(message):
    global button_states
    button_states = True
    bot.send_message(message.chat.id, "Введите, пожалуйста, aртикул товара, который требуется удалить",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, delete_articul)


def delete_articul(message):
    if message.content_type == 'text':
        num_del = str(message.text.strip())
        if re.match('^/.*$', num_del):
            mainKeyboard(message)
        else:
            token = getInfAboutProduct.get_product_data(num_del)
            if token:
                takeToken.delete_art(num_del)
                os.remove('photos' + '/' + f'{token[1]}.jpg')
                bot.send_message(message.chat.id, "Товар успешно удален!")
            else:
                bot.send_message(message.chat.id, f'К сожалению такого артикула не существует😢\n'
                                                  f'Попробуйте снова!')
                bot.register_next_step_handler(message, delete_articul)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите aртикул товара в правильном формате.")
        bot.register_next_step_handler(message, delete_articul)


@bot.message_handler(commands=['get'])
@bot.message_handler(func=lambda message: message.text.lower() == 'получить артикул')
def get(message):
    global button_states
    button_states = True
    ## random_number = takeToken.generate_unique_token()
    ## if random_number == None:
    ##    bot.send_message(message.chat.id,
    ##                     f'К сожалению невозможно сгенерировать артикул, т.к. база данных переполненна😢\n'
    ##                    f'Удалите неактуальные товары, пожалуйста!')
    ##   getart(message)
    ## else:
    bot.send_message(message.chat.id, "Введите, пожалуйста, название товара",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    if message.content_type == 'text':
        global name_product
        name_product = message.text.strip()
        if re.match('^/.*$', name_product):
            mainKeyboard(message)
        else:
            bot.send_message(message.chat.id, "Введите цену товара")
            bot.register_next_step_handler(message, get_price)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите название товара в правильном формате.")
        bot.register_next_step_handler(message, get_name)


def get_price(message):
    if message.content_type == 'text':
        global price_product
        price_product = message.text.strip()
        if re.match('^/.*$', price_product):
            mainKeyboard(message)
        else:
            if re.match(r"^[1-9]\d+$", price_product):
                bot.send_message(message.chat.id, "Введите ширину товара в одном из следующих форматах:\n"
                                                  "Число м: Пример - 10 м\n"
                                                  "Число см: Пример - 10 см")
                bot.register_next_step_handler(message, get_width)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, введите цену товара в правильном формате.")
                bot.register_next_step_handler(message, get_price)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите цену товара в правильном формате.")
        bot.register_next_step_handler(message, get_price)


def get_width(message):
    if message.content_type == 'text':
        global width_product
        width_product = message.text.strip()
        if re.match('^/.*$', width_product):
            mainKeyboard(message)
        else:
            if re.match(r"^[1-9]\d*\sм$", width_product) or re.match(r"^[1-9]\d*\sсм$", width_product):
                bot.send_message(message.chat.id, "Введите Ваш артикул товара")
                bot.register_next_step_handler(message, get_articul)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, введите ширину товара в правильном формате.")
                bot.register_next_step_handler(message, get_width)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите ширину товара в правильном формате.")
        bot.register_next_step_handler(message, get_width)


def get_articul(message):
    if message.content_type == 'text':
        global articul_product
        articul_product = message.text.strip()
        if re.match('^/.*$', articul_product):
            mainKeyboard(message)
        else:
            if re.match(r"^\d+$", articul_product):
                bot.send_message(message.chat.id, "Введите фотографию товара")
                bot.register_next_step_handler(message, get_photo)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, введите артикул товара в правильном формате.")
                bot.register_next_step_handler(message, get_articul)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите артикул товара в правильном формате.")
        bot.register_next_step_handler(message, get_articul)


def get_photo(message):
    if message.content_type == 'photo':
        photo_folder = 'photos'

        if not os.path.exists(photo_folder):
            os.makedirs(photo_folder)

        global photo_product
        photo = message.photo[-1]  # Получаем последнюю (наибольшую по размеру) фотографию
        file_id = photo.file_id  # Получаем идентификатор файла
        file_info = bot.get_file(file_id)  # Получаем информацию о файле
        downloaded_file = bot.download_file(file_info.file_path)  # Скачиваем файл

        file_path = os.path.join(photo_folder, f'{articul_product}.jpg')  # Путь к файлу в новой папке
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        img = open(f"{file_path}", 'rb')

        global button_statesates
        button_statesates = True
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true')
        bottom2 = types.InlineKeyboardButton('Неверно', callback_data='false')
        markup.row(bottom1, bottom2)

        bot.send_message(message.chat.id, f'Проверьте, пожалуйста, введенные данные на корректность:')
        bot.send_photo(message.chat.id, img,
                       caption=f'Название: {name_product}\n Цена: {price_product} ₽/м\n Артикул: {articul_product}\n Длина отреза: {width_product}')
        bot.send_message(message.chat.id,
                         f'Какого же Ваше решение?)',
                         reply_markup=markup)
        bot.register_next_step_handler(message, check_button_press)
    else:
        bot.send_message(message.chat.id, "Введите, пожалуйста, фотографию.")
        bot.register_next_step_handler(message, get_photo)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'true':
        global button_states
        button_states = False
        ## random_number = takeToken.generate_unique_token()
        conn = sqlite3.connect('shop.sql')
        cur = conn.cursor()
        cur.execute(

            f"INSERT INTO tokens (name, price, width, token) VALUES (?, ?, ?, ?)",
            [name_product, price_product + " ₽/м", width_product, articul_product])
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(callback.message.chat.id, f"Товар успешно сохранен!")
    elif callback.data == 'false':
        button_states = False
        os.remove('photos' + '/' + f'{articul_product}.jpg')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Получить артикул")
        markup.row(btn1)

        bot.send_message(callback.message.chat.id,
                         "Нажмите на кнопку <b><u>получить артикул</u></b>, после чего внесите все необходимые данные",
                         parse_mode='html', reply_markup=markup)

    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Continue....',
                          reply_markup=None)

def check_button_press(message):
    chat_id = message.chat.id
    global button_states
    if button_states == True:
        bot.send_message(chat_id, "Пожалуйста, используйте кнопки для подтверждения или изменения данных.")
        bot.register_next_step_handler(message, check_button_press)
    else:
        return


@bot.message_handler(content_types=['video', 'audio', 'sticker', 'emoji', 'photo'])
def noneContent(message):
    bot.reply_to(message, f'Извините, {message.from_user.first_name}, я не умею обрабатывать такие сообщения((')


@bot.message_handler()
def fan(message):
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS tokens (id int auto_increment primary key, name varchar(255), '
        'price varchar(20) default(NULL), width varchar(20) default(NULL), token varchar(20) default(NULL))')

    conn.commit()
    listOfTables = cur.execute(
        """SELECT * FROM tokens""").fetchall()
    cur.close()
    conn.close()
    if listOfTables != []:
        conn = sqlite3.connect('shop.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM tokens')
        products = cur.fetchall()
        for elm in products:
            name = elm[1]
            price = elm[2]
            width = elm[3]
            token = elm[4]
            # Отправка сообщения с данными о товаре и фотографией
            file_path = os.path.join('photos', f'{token}.jpg')  # Путь к файлу в новой папке
            img = open(f"{file_path}", 'rb')
            bot.send_message(message.chat.id, f'Название: {name}, Цена: {price}, Длина отреза: {width}, Артикул: {token}')
            bot.send_photo(message.chat.id, img)
        cur.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, f'В настоящее время каталог пуст!')


bot.polling(none_stop=True)
