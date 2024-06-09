import os
import re
import sqlite3

import telebot
from telebot import types

import checkUser
import config
import editUser
import getInfAboutProduct


user_states = {}

bot = telebot.TeleBot(config.TOKEN)
bot.set_webhook()


def mainKeyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bottom1 = types.KeyboardButton("Главная")
    bottom2 = types.KeyboardButton("Консультация")
    bottom3 = types.KeyboardButton("Заказ")
    markup.row(bottom1, bottom2)
    markup.add(bottom3)
    bot.send_message(message.chat.id, "Доступные команды:", reply_markup=markup)


@bot.message_handler(commands=['start', 'main', 'hello'])
@bot.message_handler(func=lambda message: message.text.lower() == 'главная')
def welcome(message):
    # DB
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(255), tgId varchar(20) '
        'unique not null, phone varchar(20), has_card integer default(0))')

    conn.commit()
    cur.close()
    conn.close()
    ###

    user_states[message.chat.id] = {'name': None, 'phone': None, 'tgId': None, 'card': 0, 'size': None}
    sti = open('static/welcome.webp', 'rb')

    bot.send_sticker(message.chat.id, sti)
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\n "
                                      "Я - <b>электронный сотрудник магазина по продаже тканей</b>, бот, созданный, чтобы помочь вам сделать заказ.".format(
        message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=types.ReplyKeyboardRemove())

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Статус посылки", callback_data='status')
    btn2 = types.InlineKeyboardButton("Сделать заказ", callback_data='order')

    markup.row(btn1, btn2)
    bot.send_message(message.chat.id,
                     "{0.first_name}, если вы хотите получить информацию по доставке вашего заказа, нажмите на <b>Статус посылки</b>.\n"
                     "Если хотите сделать заказ, нажмите на <b>Сделать заказ</b>".format(message.from_user,
                                                                                         bot.get_me()),
                     parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['order'])
@bot.message_handler(func=lambda message: message.text.lower() in {'заказ', 'заказать еще'})
def order(message):
    user_states[message.chat.id] = {'token': None}
    bot.send_message(message.chat.id, "Введите, пожалуйста, <b>артикул</b> товара\n"
                                      "<b>Пример ввода: 875234</b>\n\n"
                                      "Если вы забыли артикул товара, то можете перейти обратно в основной канал и посмотреть его\n"
                                      "<b>Вот ссылка -> https://t.me/bravissimo_nn</b>", parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_token)
    # Обработка индефикатора и подтверждение правильности выбора товара


def get_token(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['token'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['token']):
            mainKeyboard(message)
        else:
            user_states[message.chat.id]['product_data'] = getInfAboutProduct.get_product_data(
                user_states[message.chat.id]['token'])
            # Проверка на существование
            if not user_states[message.chat.id]['product_data']:
                bot.send_message(message.chat.id, f'К сожалению, такого артикула не существует😢\n'
                                                  f'Попробуйте снова!')
                order(message)
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                bottom1 = types.KeyboardButton("Верно")
                bottom2 = types.KeyboardButton("Неверно")
                bottom3 = types.KeyboardButton("Консультация")
                markup.row(bottom1, bottom2)
                markup.add(bottom3)

                bot.send_message(message.chat.id, "Проверьте, пожалуйста, что вы правильно ввели артикул\n"
                                                  "Данные по данному артикулу:")

                # Отправка сообщения с данными о товаре и фотографией
                file_path = os.path.join('photos',
                                         f'{user_states[message.chat.id]["product_data"][4]}.jpg')  # Путь к файлу в новой папке
                img = open(f"{file_path}", 'rb')

                bot.send_photo(message.chat.id, img,
                               caption=f'Название: {user_states[message.chat.id]["product_data"][1]}\n Цена: {user_states[message.chat.id]["product_data"][2]}\n Длина отреза: {user_states[message.chat.id]["product_data"][3]}\n Артикул: {user_states[message.chat.id]["product_data"][4]}',
                               reply_markup=markup)
                # Проверка на правильный выбор
                bot.register_next_step_handler(message, check_product)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Введите, пожалуйста, текстом")
        order(message)


def check_product(message):
    if message.content_type == 'text':
        if re.match('^/', message.text.strip()):
            mainKeyboard(message)
        elif message.text.strip() == 'Неверно':
            order(message)
        elif message.text.strip() == 'Верно':
            get_info_user(message)
        elif message.text.strip() == 'Консультация':
            consult2(message)
        else:
            bot.send_message(message.chat.id,
                             "Выберите одну из кнопок: Верно или Неверно, либо выберите кнопку Консультация, чтобы перейти в чат с менеджером")
            bot.register_next_step_handler(message, check_product)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Введите, пожалуйста, текстом")
        bot.register_next_step_handler(message, check_product)


def get_info_user(message):
    # Register users
    user_states[message.chat.id]['user_data'] = checkUser.get_user_data(message.from_user.id)
    if user_states[message.chat.id]['user_data']:
        user_states[message.chat.id]['waiting_for_button'] = True
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Изменились', callback_data='edit_data')
        markup.row(bottom1, bottom2)

        user_states[message.chat.id]['name'] = user_states[message.chat.id]['user_data'][1]
        user_states[message.chat.id]['phone'] = user_states[message.chat.id]['user_data'][3]
        user_states[message.chat.id]['tgId'] = message.from_user.id

        bot.send_message(message.chat.id, f'Вы уже были в нашем магазине, и у нас есть ваши данные😁',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, f'Проверьте, пожалуйста, текущие данные на корректность:\n\n'
                                          f'ФИО: {user_states[message.chat.id]["user_data"][1]}\n'
                                          f'Номер мобильного телефона: {user_states[message.chat.id]["user_data"][3]}',
                         reply_markup=markup)
        bot.register_next_step_handler(message, check_button_press)
    else:
        bot.send_message(message.chat.id, "Сейчас нужно вас зарегистрировать!\n"
                                          "Введите, пожалуйста, через пробел с большой буквы свое ФИО\n"
                                          "Пример ввода: Иванов Иван Иванович\n",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, user_name)


def user_name(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['name'] = message.text.strip()

        if re.match('^/', user_states[message.chat.id]['name']):
            mainKeyboard(message)

        elif re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
            # Ввод пользователя соответствует формату Фамилия Имя Отчество
            bot.send_message(message.chat.id, "Введите свой номер телефона в формате:\n"
                                              "79*********")
            bot.register_next_step_handler(message, user_phone)
        else:
            # Ввод пользователя не соответствует формату ФИО
            bot.send_message(message.chat.id, "Пожалуйста, введите свое ФИО в правильном формате.")
            bot.register_next_step_handler(message, user_name)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите свое ФИО в правильном формате.")
        bot.register_next_step_handler(message, user_name)


def user_phone(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['phone'] = message.text.strip()
        if re.match('^/', user_states[message.chat.id]['phone']):
            mainKeyboard(message)

        elif re.match(r'^79\d{9}$', user_states[message.chat.id]['phone']):
            user_states[message.chat.id]['waiting_for_button'] = True
            user_states[message.chat.id]['tgId'] = message.from_user.id
            markup = types.InlineKeyboardMarkup()
            bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
            bottom2 = types.InlineKeyboardButton('Неверно', callback_data='false_enter')
            markup.row(bottom1, bottom2)

            bot.send_message(message.chat.id, f'Мы закончили небольшую регистрацию🔥')
            bot.send_message(message.chat.id,
                             f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]["name"]}\n Номер мобильного телефона: {user_states[message.chat.id]["phone"]}',
                             reply_markup=markup)
            bot.register_next_step_handler(message, check_button_press)
        else:
            # Неверный формат номера телефона
            bot.send_message(message.chat.id,
                             "Пожалуйста, введите корректный номер мобильного телефона (номер должен содержать 11 цифр и начинаться на 79).")
            bot.register_next_step_handler(message, user_phone)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите корректный номер телефона (номер должен содержать 11 цифр и начинаться на 79).")
        bot.register_next_step_handler(message, user_phone)


def consult2(message):
    file_path = os.path.join('photos',
                             f'{user_states[message.chat.id]["product_data"][4]}.jpg')  # Путь к файлу в новой папке
    img = open(f"{file_path}", 'rb')
    # Отправка сообщения с данными о товаре и фотографией
    bot.send_photo(config.manager_id, img,
                   caption=f'Консультация!\n'
                           f'Информация о заказе с артикулом - {user_states[message.chat.id]["product_data"][4]}:\n'
                           f'Название: {user_states[message.chat.id]["product_data"][1]}\n'
                           f'Цена: {user_states[message.chat.id]["product_data"][2]}\n'
                           f'Длина отреза: {user_states[message.chat.id]["product_data"][3]}\n\n'

                           f'Информация о пользователе:\n'
                           f'Ник пользователя - {message.from_user.username}\n')

    bot.send_message(message.chat.id,
                     f'Перейдите по следующей ссылке, чтобы связаться с менеджером. Обязательно представьтесь и отправьте артикул своего товара, чтобы менеджер смог вас понять)\n\n'
                     f'<b>Переходите сюда</b> -> https://t.me/Artv1d', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['pochta'])
@bot.message_handler(func=lambda message: message.text.lower() == 'почта россии')
def pochta(message):
    bot.send_message(message.chat.id, "Перейдите, пожалуйста, по ссылке -> https://www.pochta.ru/tracking\n"
                                      "На сайте в поле *номер заказа* нужно ввести трек-номер вашего заказа, больше от вас ничего не потребуется)",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['sdek'])
@bot.message_handler(func=lambda message: message.text.lower() == 'сдэк')
def sdek(message):
    bot.send_message(message.chat.id,
                     "Перейдите, пожалуйста, по ссылке -> https://www.cdek.ru/ru/tracking/\n"
                     "На сайте в поле *номер заказа* нужно ввести трек-номер вашего заказа, больше от вас ничего не потребуется)",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['advice'])
@bot.message_handler(func=lambda message: message.text.lower() == 'консультация')
def consult(message):
    bot.send_message(message.chat.id,
                     f'Перейдите по следующей ссылке, чтобы связаться с менеджером. Обязательно отправьте артикул своего товара, чтобы менеджер смог вас понять)\n\n'
                     f'<b>Переходите сюда</b> -> https://t.me/Artv1d', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['end'])
@bot.message_handler(func=lambda message: message.text.lower() == 'закончить')
def end(message):
    bot.send_message(message.chat.id, f'Были рады видеть вас в нашем магазине, приходите еще😊',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(content_types=['photo', 'video', 'audio', 'sticker', 'emoji'])
def noneContent(message):
    bot.reply_to(message, f'Извините, {message.from_user.first_name}, я не умею обрабатывать такие сообщения((')


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'status':
        markup10 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item10 = types.KeyboardButton("Почта России")
        item01 = types.KeyboardButton("СДЭК")
        markup10.add(item10)
        markup10.add(item01)
        bot.send_message(callback.message.chat.id,
                         "Если ваш заказ отправлен службой доставки *Почта России*, нажмите на кнопку <b>Почта России</b>, если ваш заказ отправлен службой доставки *СДЭК*, нажмите на кнопку <b>СДЭК</b>",
                         parse_mode='html', reply_markup=markup10)

    elif callback.data == 'order':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Заказ")
        markup1.add(item1)
        bot.send_message(callback.message.chat.id,
                         "Чтобы сделать заказ, отправьте команду <b>/order</b> или нажмите на кнопку <b>Заказ</b>",
                         parse_mode='html', reply_markup=markup1)
    elif callback.data == 'true_enter':
        if not user_states[callback.message.chat.id]['user_data']:
            # Доделать
            conn = sqlite3.connect('shop.sql')
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO users(name, tgId, phone, has_card) VALUES ('{user_states[callback.message.chat.id]['name']}', '{user_states[callback.message.chat.id]['tgId']}', '{user_states[callback.message.chat.id]['phone']}', '{0}')")
            conn.commit()
            cur.close()
            conn.close()
            user_states[callback.message.chat.id]['card'] = 0
        else:
            user_states[callback.message.chat.id]['card'] = user_states[callback.message.chat.id]['user_data'][4]

        if user_states[callback.message.chat.id]['card'] == 1:
            consultation(callback)
        else:
            check_card(callback)
    elif callback.data == 'card_true':
        user_states[callback.message.chat.id]['card'] = 1
        editUser.update_user_card(user_states[callback.message.chat.id]['card'],
                                  user_states[callback.message.chat.id]['tgId'])
        consultation(callback)
    elif callback.data == 'card_false':
        user_states[callback.message.chat.id]['waiting_for_button'] = True
        user_states[callback.message.chat.id]['card'] = 0
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Хочу', callback_data='create_card')
        bottom2 = types.InlineKeyboardButton('Не хочу', callback_data='continue_without_card')
        markup.row(bottom1, bottom2)

        bot.send_message(callback.message.chat.id, f'Это очень грустно, что у вас нет нашей дисконтной карты😞 '
                                                   f'Предлагаем вам создать ее, чтобы в дальнейшем приобретать наш товар по более выгодной цене)',
                         reply_markup=markup)
    elif callback.data == 'card_ignorance':
        user_states[callback.message.chat.id]['card'] = 2
        consultation(callback)
    elif callback.data == 'false_enter':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Заказ")
        markup1.add(item1)
        bot.send_message(callback.message.chat.id,
                         "Давайте заполним ваши данные заново. Отправьте, пожалуйста, команду <b>/order</b> или нажмите на кнопку <b>Заказ</b>",
                         parse_mode='html', reply_markup=markup1)
    elif callback.data == 'edit_data':
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton("ФИО", callback_data='edit_name')
        bottom2 = types.InlineKeyboardButton("Номер", callback_data='edit_phone')
        bottom3 = types.InlineKeyboardButton("Все", callback_data='edit_all')
        markup.row(bottom1, bottom2)
        markup.add(bottom3)
        bot.send_message(callback.message.chat.id, f'Выберите, пожалуйста, какие данные поменялись🙃',
                         reply_markup=markup)
    elif callback.data == 'create_card':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id, "Введите, пожалуйста, вашу дату рождения в формате: ДД.ММ.ГГГГ\n"
                                                   "Пример ввода: 10.10.2000")
        bot.register_next_step_handler(callback.message, lambda message: process_birthday_input(callback, message))
    elif callback.data == 'continue_without_card':
        consultation(callback)
    elif callback.data == 'end_of_buy':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id,
                         f'Введите сколько товара вы хотите заказать в САНТИМЕТРАХ', parse_mode='html',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(callback.message, end_of_work)
    elif callback.data == 'advice':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        file_path = os.path.join('photos',
                                 f'{user_states[callback.message.chat.id]["product_data"][4]}.jpg')  # Путь к файлу в новой папке
        img = open(f"{file_path}", 'rb')
        # Отправка сообщения с данными о товаре и фотографией
        bot.send_photo(config.manager_id, img,
                       caption=f'Консультация!\n'
                               f'Информация о заказе с артикулом - {user_states[callback.message.chat.id]["product_data"][4]}:\n'
                               f'Название: {user_states[callback.message.chat.id]["product_data"][1]}\n'
                               f'Цена: {user_states[callback.message.chat.id]["product_data"][2]}\n'
                               f'Длина отреза: {user_states[callback.message.chat.id]["product_data"][3]}\n\n'

                               f'Информация о пользователе:\n'
                               f'Ник пользователя - {callback.message.chat.username}\n'
                               f'ФИО - {user_states[callback.message.chat.id]["name"]}\n'
                               f'Номер телефона - {user_states[callback.message.chat.id]["phone"]}\n'
                               f'Информация о наличии карты - {"Есть карта" if user_states[callback.message.chat.id]["card"] == 1 else ("Нужно проверить о наличии" if user_states[callback.message.chat.id]["card"] == 2 else "Нет карты")}')

        bot.send_message(callback.message.chat.id,
                         f'Перейдите по следующей ссылке, чтобы связаться с менеджером. Обязательно отправьте артикул своего товара, чтобы менеджер смог вас понять)\n\n'
                         f'<b>Переходите сюда</b> -> https://t.me/Artv1d', parse_mode='html',
                         reply_markup=types.ReplyKeyboardRemove())
    elif callback.data == 'edit_name':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id, "Введите, пожалуйста, через пробел с большой буквы свое ФИО\n"
                                                   "Пример ввода: Иванов Иван Иванович\n",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(callback.message, get_name)
    elif callback.data == 'edit_phone':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id, "Введите, пожалуйста, новый номер в формате 79*********",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(callback.message, get_phone)
    elif callback.data == 'edit_all':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id, "Введите, пожалуйста, через пробел с большой буквы свое ФИО\n"
                                                   "Пример ввода: Иванов Иван Иванович\n",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(callback.message, get_name_from_all)
    elif callback.data == 'end':
        user_states[callback.message.chat.id]['waiting_for_button'] = False
        bot.send_message(callback.message.chat.id, f'Были рады видеть вас в нашем магазине, приходите еще😊',
                         reply_markup=types.ReplyKeyboardRemove())

    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Далее....',
                          reply_markup=None)


def process_birthday_input(callback, message):
    if message.content_type == 'text':
        user_states[callback.message.chat.id]['birthday'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['birthday']):
            mainKeyboard(message)
        elif re.match(r'^(0[1-9]|1[0-9]|2[0-9]|3[0-1])\.(0[1-9]|1[0-2])\.(19[3-9][0-9]|20[01][0-9])$',
                      user_states[callback.message.chat.id]['birthday']):
            user_states[callback.message.chat.id]['waiting_for_button'] = True
            bot.register_next_step_handler(callback.message, check_button_press)
            bot.send_message(config.manager_id, f'Создать дисконтную карту!\n'
                                                f'Информация о пользователе:\n'
                                                f'Ник пользователя - {callback.message.chat.username}\n'
                                                f'ФИО - {user_states[callback.message.chat.id]["name"]}\n'
                                                f'Номер телефона - {user_states[callback.message.chat.id]["phone"]}\n'
                                                f'Дата рождения - {user_states[callback.message.chat.id]["birthday"]}')
            consultation(callback)
        else:
            bot.send_message(callback.message.chat.id,
                             f'Неверный формат даты рождения. Введите дату в формате: ДД.ММ.ГГГГ\n'
                             f'Пример ввода: 10.10.2000')
            bot.register_next_step_handler(callback.message, lambda message: process_birthday_input(callback, message))
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите дату в формате: ДД.ММ.ГГГГ")
        bot.register_next_step_handler(callback.message, lambda message: process_birthday_input(callback, message))


def end_of_work(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['size'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['size']):
            mainKeyboard(message)
        elif re.match(r'^[0-9]+$', user_states[message.chat.id]['size']):
            user_states[message.chat.id]['price'] = (
                    float(user_states[message.chat.id]['product_data'][2].split(" ")[0]) *
                    float(int(user_states[message.chat.id]['size']) / 100))
            if user_states[message.chat.id]['product_data'][3].split(" ")[1] == 'м':
                user_states[message.chat.id]['size'] = str(int(user_states[message.chat.id]['size']) / 100)
            if float(user_states[message.chat.id]['size']) <= float(
                    user_states[message.chat.id]['product_data'][3].split(" ")[0]):
                file_path = os.path.join('photos',
                                         f'{user_states[message.chat.id]["product_data"][4]}.jpg')  # Путь к файлу в новой папке
                img = open(f"{file_path}", 'rb')
                # Отправка сообщения с данными о товаре и фотографией
                bot.send_photo(config.manager_id, img,
                               caption=f'Принять заказ!\n'
                                       f'Информация о заказе с артикулом - {user_states[message.chat.id]["product_data"][4]}:\n'
                                       f'Название: {user_states[message.chat.id]["product_data"][1]}\n'
                                       f'Сумма к оплате: {user_states[message.chat.id]["price"]} ₽\n'
                                       f'Длина отреза: {user_states[message.chat.id]["size"]} {user_states[message.chat.id]["product_data"][3].split(" ")[1]}\n\n'

                                       f'Информация о пользователе:\n'
                                       f'Ник пользователя - {message.from_user.username}\n'
                                       f'ФИО - {user_states[message.chat.id]["name"]}\n'
                                       f'Номер телефона - {user_states[message.chat.id]["phone"]}\n'
                                       f'Информация о наличии карты - {"Есть карта" if user_states[message.chat.id]["card"] == 1 else ("Нужно проверить о наличии" if user_states[message.chat.id]["card"] == 2 else "Нет карты")}')

                del user_states[message.chat.id]['price']
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                bottom1 = types.KeyboardButton("Заказать еще")
                bottom2 = types.KeyboardButton("Закончить")
                markup.row(bottom1, bottom2)

                bot.send_message(message.chat.id,
                                 f'Ваш заказ зарегистрирован и отправлен менеджеру. В течение 12 рабочих часов менеджер свяжется с вами для приема оплаты',
                                 parse_mode='html',
                                 reply_markup=markup)
            else:
                if user_states[message.chat.id]['price']:
                    del user_states[message.chat.id]['price']
                user_states[message.chat.id]['waiting_for_button'] = True
                markup = types.InlineKeyboardMarkup()
                bottom1 = types.InlineKeyboardButton("Ввести размер повторно", callback_data="end_of_buy")
                bottom2 = types.InlineKeyboardButton("Закончить", callback_data="end")
                markup.row(bottom1, bottom2)
                bot.send_message(message.chat.id,
                                 f"К сожалению, изначально на нашем складе нет такого количества товара, приносим свои извинения.\n"
                                 f"Нажмите на кнопку - Ввести размер повторно, и введите размер меньший, чем {user_states[message.chat.id]['product_data'][3]}\n"
                                 f"Или нажмите на кнопку - Закончить, если Вам недостаточно товара, который есть в наличии",
                                 reply_markup=markup)
                bot.register_next_step_handler(message, check_button_press)
        else:
            bot.send_message(message.chat.id,
                             "Пожалуйста, введите корректный размер ткани (он состоит ТОЛЬКО из цифр).")
            bot.register_next_step_handler(message, end_of_work)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите корректный размер ткани (он состоит ТОЛЬКО из цифр).")
        bot.register_next_step_handler(message, end_of_work)


def get_name(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['name'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['name']):
            mainKeyboard(message)
        elif re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
            user_states[message.chat.id]['waiting_for_button'] = True
            editUser.update_user_name(user_states[message.chat.id]['name'], message.from_user.id)
            markup = types.InlineKeyboardMarkup()
            bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
            bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
            markup.row(bottom1, bottom2)
            bot.send_message(message.chat.id,
                             f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]["name"]}\n Номер телефона: {user_states[message.chat.id]["phone"]}',
                             reply_markup=markup)
            bot.register_next_step_handler(message, check_button_press)
        else:
            # Ввод пользователя не соответствует формату ФИО
            bot.send_message(message.chat.id, "Пожалуйста, введите ФИО в правильном формате.")
            bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите ФИО в правильном формате.")
        bot.register_next_step_handler(message, get_name)


def get_phone(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['phone'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['phone']):
            mainKeyboard(message)
        elif re.match(r'^79\d{9}$',
                      user_states[message.chat.id]['phone']):
            user_states[message.chat.id]['waiting_for_button'] = True
            editUser.update_user_phone(user_states[message.chat.id]['phone'], message.from_user.id)
            markup = types.InlineKeyboardMarkup()
            bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
            bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
            markup.row(bottom1, bottom2)
            bot.send_message(message.chat.id,
                             f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]["name"]}\n Номер мобильного телефона: {user_states[message.chat.id]["phone"]}',
                             reply_markup=markup)
            bot.register_next_step_handler(message, check_button_press)
        else:
            # Неверный формат номера телефона
            bot.send_message(message.chat.id,
                             "Пожалуйста, введите корректный номер мобильного телефона (номер должен состоять из 11 цифр и начинаться на 79).")
            bot.register_next_step_handler(message, get_phone)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите корректный номер мобильного телефона (номер должен состоять из 11 цифр и начинаться на 79).")
        bot.register_next_step_handler(message, get_phone)


def get_name_from_all(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['name'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['name']):
            mainKeyboard(message)
        elif re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
            bot.send_message(message.chat.id,
                             "Введите, пожалуйста, новый номер мобильного телефона в формате 79*********")
            bot.register_next_step_handler(message, get_all)
        else:
            # Ввод пользователя не соответствует формату ФИО
            bot.send_message(message.chat.id, "Пожалуйста, введите ФИО в правильном формате.")
            bot.register_next_step_handler(message, get_name_from_all)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите ФИО в правильном формате.")
        bot.register_next_step_handler(message, get_name_from_all)


def get_all(message):
    if message.content_type == 'text':
        user_states[message.chat.id]['phone'] = message.text.strip()
        if re.match('^/.*$', user_states[message.chat.id]['phone']):
            mainKeyboard(message)
        elif re.match(r'^79\d{9}$',
                      user_states[message.chat.id]['phone']):
            user_states[message.chat.id]['waiting_for_button'] = True
            editUser.update_user_all(user_states[message.chat.id]['phone'], user_states[message.chat.id]['name'],
                                     message.from_user.id)
            markup = types.InlineKeyboardMarkup()
            bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
            bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
            markup.row(bottom1, bottom2)
            bot.send_message(message.chat.id,
                             f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]["name"]}\n Номер мобильного телефона: {user_states[message.chat.id]["phone"]}',
                             reply_markup=markup)
            bot.register_next_step_handler(message, check_button_press)
        else:
            # Неверный формат номера телефона
            bot.send_message(message.chat.id,
                             "Пожалуйста, введите корректный номер мобильного телефона (номер должен состоять из 11 цифр и начинаться на 79).")
            bot.register_next_step_handler(message, get_all)
    else:
        bot.send_message(message.chat.id, "Я не умею обрабатывать такие сообщения(\n"
                                          "Пожалуйста, введите корректный номер телефона (номер должен состоять из 11 цифр и начинаться на 79).")
        bot.register_next_step_handler(message, get_all)


def check_card(callback):
    markup = types.InlineKeyboardMarkup()
    bottom1 = types.InlineKeyboardButton("Есть", callback_data="card_true")
    bottom2 = types.InlineKeyboardButton("Не имею", callback_data="card_false")
    bottom3 = types.InlineKeyboardButton("Не помню", callback_data="card_ignorance")
    markup.row(bottom1, bottom2)
    markup.add(bottom3)

    bot.send_message(callback.message.chat.id,
                     f'Имеется ли у вас дисконтная карта, привязанная к данному номеру - {user_states[callback.message.chat.id]["phone"]}',
                     reply_markup=markup)


def check_button_press(message):
    chat_id = message.chat.id

    if user_states[chat_id].get('waiting_for_button', True):
        bot.send_message(chat_id, "Пожалуйста, используйте кнопки для подтверждения или изменения данных.")
        bot.register_next_step_handler(message, check_button_press)
    else:
        return


def consultation(callback):
    markup111 = types.InlineKeyboardMarkup()
    bottom1 = types.InlineKeyboardButton("Консультация", callback_data='advice')
    bottom2 = types.InlineKeyboardButton("Завершение", callback_data='end_of_buy')
    markup111.row(bottom1, bottom2)

    bot.send_message(callback.message.chat.id, "Ваши данные успешно зарегистрированы)\n"
                                               "Нужна ли вам дополнительная консультация с нашим менеджером по поводу заказа?")
    bot.send_message(callback.message.chat.id,
                     "Выберите <b>Завершение</b>, если консультация не нужна.\n"
                     "Выберите <b>Консультация</b>, если нужна", parse_mode='html', reply_markup=markup111)


@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\n "
                                          "Я - <b>электронный сотрудник магазина по продаже тканей</b>, бот созданный чтобы помочь тебе сделать заказ.".format(
            message.from_user, bot.get_me()),
                         parse_mode='html')
    else:
        bot.reply_to(message, f'Извините, {message.from_user.first_name}, я не умею обрабатывать такие сообщения((')


if __name__ == "__main__":
    bot.polling(none_stop=True)
