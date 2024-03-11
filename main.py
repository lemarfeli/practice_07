import string  # для генерации ключа комнаты
import random

import telebot
from telebot import types
bot = telebot.TeleBot('6813501562:AAF3-i5zM2LgbO_mpdy4yRYW4mr8Z0wtKic')

#'7070533359:AAGUwBLIkXmrdD9ebAIm4WRb8QUHhFiIfvo'

from bd import SqlDB
SqlDB = SqlDB()

room = {}
player = {}
wish = {}
global id

@bot.message_handler(commands=['start'])
def start(message):
    if (not SqlDB.exists_user(message.from_user.id)):
        SqlDB.add_new_user(message.from_user.id)

    first_mess = f"""Привет <b>{message.from_user.first_name}</b>!\n
Я - твой верный Бот помощник! Моя задача помочь тебе и всем участникам провести игру честно и максимально увлекательно.\n
Играй в Тайного Санту с коллегами, семьей, друзьями или сообществе, со всеми, с кем ты хочешь разделить радость новогодней суеты!\n
Буду рядом, чтобы помочь с любыми вопросами и сделать мероприятие по-настоящему праздничным\n
Отличной игры:)"""
    global markup_main
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_create_room = types.KeyboardButton('Создать комнату')
    b_enter_room = types.KeyboardButton('Войти в комнату')
    b_my_rooms = types.KeyboardButton('Мои комнаты')
    b_wishlist = types.KeyboardButton('Виш лист')

    markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)
    bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=markup_main)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global delete_markup
    delete_markup = telebot.types.ReplyKeyboardRemove()
    if message.text == 'Создать комнату':
        room[message.chat.id] = {}

        markup_room_name = types.ReplyKeyboardMarkup(resize_keyboard=True)
        name_1 = types.KeyboardButton('Тест игры⚙️')
        name_2 = types.KeyboardButton('Друзья🤩')
        name_3 = types.KeyboardButton('Коллеги📚')
        name_4 = types.KeyboardButton('Одногруппники😎')
        back = types.KeyboardButton('Назад')

        markup_room_name.row(name_1, name_2).row(name_3, name_4).add(back)
        bot.send_message(message.chat.id, 'Вы нажали на кнопку Создать комнату. Введите название комнаты или выберите из предложенных',
                         parse_mode='html', reply_markup=markup_room_name)

        bot.register_next_step_handler(message, room_reg_name)

    elif message.text == 'Войти в комнату':
        bot.send_message(message.chat.id, 'Вы нажали на кнопку Войти в комнату')

    elif message.text == 'Мои комнаты':
        bot.send_message(message.chat.id, 'Вы нажали на кнопку Мои комнаты')

    elif message.text == 'Виш лист':
        wish[message.chat.id] = {}
        if not SqlDB.check_wish(message.from_user.id):
            delete_markup = telebot.types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id,
                             'Вы нажали на кнопку Виш лист. Заполните Ваш виш лист', parse_mode='html',
                             reply_markup=delete_markup)
            bot.register_next_step_handler(message, wishlist)
        else:
            bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id))

    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=markup_main)
    else:
        # Действия при получении другого сообщения
        bot.send_message(message.chat.id, 'я вас не понимаю', parse_mode='html', reply_markup=markup_main)

bot.set_my_commands([
    types.BotCommand("/start", "Перезапуск бота"),
    types.BotCommand("/help", "Помощь"),
    types.BotCommand("/rules", "Правила игры"),
    types.BotCommand("/advice", "Советы")
])

def create_buttons(user_id):
    wishlist_data = SqlDB.select_wishlist(user_id)
    keyboard = types.InlineKeyboardMarkup()
    for wish_item in wishlist_data:
        keyboard.add(types.InlineKeyboardButton(text=wish_item[2], callback_data=str(wish_item[0])))
    keyboard.add(types.InlineKeyboardButton(text='Добавить', callback_data='add'))
    return keyboard
def room_reg_name(message):
    global markup_main
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=markup_main)
    else:
        char = 6  # количество символов в ключе
        room_key = ''.join(random.choices(string.ascii_letters + string.digits, k=char))
        room[message.chat.id]['roomid'] = room_key  # ключ
        room[message.chat.id]['name'] = message.text

        global markup_anonymity

        markup_anonymity = types.ReplyKeyboardMarkup(resize_keyboard=True)
        anonym = types.KeyboardButton('Анонимная')
        public = types.KeyboardButton('Публичная')
        markup_anonymity.row(anonym, public)

        bot.send_message(message.chat.id, 'Отлично! Анонимная или публичная игра? ', reply_markup=markup_anonymity)
        bot.register_next_step_handler(message, room_anonymity)
def room_anonymity(message):
    global markup_anonymity
    if message.text == 'Анонимная' or message.text == 'Публичная':
        if message.text == 'Анонимная':
            room[message.chat.id]['anonymity'] = True
        elif message.text == 'Публичная':
            room[message.chat.id]['anonymity'] = False
        global markup_currency

        markup_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rub = types.KeyboardButton('₽')
        eur = types.KeyboardButton('€')
        usd = types.KeyboardButton('$')

        markup_currency.row(rub, eur, usd)

        bot.send_message(message.chat.id, 'Укажите валюту, в которой будет определен бюджет для подарков',
                         reply_markup=markup_currency)
        bot.register_next_step_handler(message, currency_budget)
    else:
        bot.send_message(message.chat.id, 'Я вас не понимаю')
        bot.send_message(message.chat.id,
                         'Анонимная или публичная игра?', parse_mode='html', reply_markup=markup_anonymity)
        bot.register_next_step_handler(message, room_anonymity)
def currency_budget(message):
    room[message.chat.id]['budget'] = message.text

    global markup_budget

    markup_budget = types.ReplyKeyboardMarkup(resize_keyboard=True)
    budget_300 = types.KeyboardButton('300')
    budget_500 = types.KeyboardButton('500')
    budget_1000 = types.KeyboardButton('1000')
    budget_1500 = types.KeyboardButton('1500')

    markup_budget.row(budget_300, budget_500).row(budget_1000, budget_1500)

    bot.send_message(message.chat.id, 'Какой бюджет на подарки? Выберите из частых вариантов или укажите ваш лимит в рублях.', reply_markup=markup_budget)
    bot.register_next_step_handler(message, room_budget)
def room_budget(message):
    global markup_budget

    try:
        budget = float(message.text.replace(',', '.'))
        if budget.is_integer():
            budget = int(budget)
        if budget <= 0:
            raise Exception
        room[message.chat.id]['budget'] = str(budget) + ' ' +room[message.chat.id]['budget']
        bot.send_message(message.chat.id, f"Сумма {budget} успешно добавлена")

        if room[message.chat.id]['anonymity']:
            room[message.chat.id]['sending'] = False
            bot.send_message(message.chat.id, 'Теперь укажите место и дату проведения', reply_markup=delete_markup)
            bot.register_next_step_handler(message, room_meeting)
        else:
            global markup_sending

            markup_sending = types.ReplyKeyboardMarkup(resize_keyboard=True)
            post = types.KeyboardButton('Почтой')
            ofline = types.KeyboardButton('Лично')
            # back = types.KeyboardButton('Назад')

            markup_sending.add(post, ofline)  # .add(back)

            bot.send_message(message.chat.id,
                             'Выбор отправки почтой или вручение лично?',
                             parse_mode='html',
                             reply_markup=markup_sending)
            bot.register_next_step_handler(message, room_sending)
    except Exception:
        bot.send_message(message.chat.id, 'Введите корректные данные', reply_markup=markup_budget)
        bot.register_next_step_handler(message, room_budget)
def room_sending(message):
    global markup_sending, markup_main
    if message.text == 'Почтой':
        room[message.chat.id]['sending'] = True
        SqlDB.create_new_room(room[message.chat.id]['roomid'], room[message.chat.id]['name'],
                              room[message.chat.id]['anonymity'], room[message.chat.id]['budget'],
                              room[message.chat.id]['sending'], None,
                              message.from_user.id)
        bot.send_message(message.chat.id, f'Ваши данные успешно сохранены!',
                         reply_markup=markup_main)
    elif message.text == 'Лично':
        room[message.chat.id]['sending'] = False
        bot.send_message(message.chat.id, 'Теперь укажите место и дату проведения', reply_markup=delete_markup)
        bot.register_next_step_handler(message, room_meeting)

    else:
        bot.send_message(message.chat.id, 'Я вас не понимаю')
        bot.send_message(message.chat.id,
                         'Выбор отправки почтой или вручение лично?',
                         parse_mode='html',
                         reply_markup=markup_sending)
        bot.register_next_step_handler(message, room_sending)
def room_meeting(message):
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_create_room = types.KeyboardButton('Создать комнату')
    b_enter_room = types.KeyboardButton('Войти в комнату')
    b_my_rooms = types.KeyboardButton('Мои комнаты')
    b_wishlist = types.KeyboardButton('Виш лист')

    markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)
    
    room[message.chat.id]['meeting'] = message.text
    SqlDB.create_new_room(room[message.chat.id]['roomid'], room[message.chat.id]['name'],
                          room[message.chat.id]['anonymity'], room[message.chat.id]['budget'],
                          room[message.chat.id]['sending'], room[message.chat.id]['meeting'],
                          message.from_user.id)
    bot.send_message(message.chat.id, f'Ваши данные успешно сохранены!',
                     reply_markup=markup_main)

def wishlist(message):
    wish[message.chat.id]['wish'] = message.text
    markup_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    skip = types.KeyboardButton('Пропустить')
    markup_skip.add(skip)
    bot.send_message(message.chat.id, 'Отлично! Добавьте описание ', reply_markup=markup_skip)
    bot.register_next_step_handler(message, wish_description)
def wish_description(message):
    if message.text == 'Пропустить':
        wish[message.chat.id]['description'] = ""
    else:
        wish[message.chat.id]['description'] = message.text
    SqlDB.add_new_wish(message.from_user.id, wish[message.chat.id]['wish'], wish[message.chat.id]['description'])
    markup_wish = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_wish = types.KeyboardButton('Добавить новый подарок')
    menu = types.KeyboardButton('Вернуться в меню')
    markup_wish.add(new_wish).add(menu)
    bot.send_message(message.chat.id, f"Подарок: {wish[message.chat.id]['wish']}\nОписание: {wish[message.chat.id]['description']}\nбыли успешно добавлены в ваш виш-лист! Желаете добавить что-то еще?", reply_markup=markup_wish)
    bot.register_next_step_handler(message, wish_menu)
def wish_menu(message):
    if message.text  == 'Добавить новый подарок' :
        bot.send_message(message.chat.id,f'Добавьте новый подарок в ваш виш-лист')
        bot.register_next_step_handler(message, wishlist)
    elif message.text  == 'Вернуться в меню':
        markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
        b_create_room = types.KeyboardButton('Создать комнату')
        b_enter_room = types.KeyboardButton('Войти в комнату')
        b_my_rooms = types.KeyboardButton('Мои комнаты')
        b_wishlist = types.KeyboardButton('Виш лист')

        markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)
        bot.send_message(message.chat.id, f'Вы вернулись в меню',
                         reply_markup=markup_main)

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    global id
    if call.data == 'back':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Ваш виш лист:", reply_markup=create_buttons(call.message.chat.id))
    elif call.data == 'delete':
        SqlDB.delete_wish(id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Ваш виш лист:", reply_markup=create_buttons(call.message.chat.id))
    elif call.data == 'add':
        delete_markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(call.message.chat.id, f'Добавьте новый подарок в ваш виш-лист', reply_markup=delete_markup)
        bot.register_next_step_handler(call.message, wishlist)
    elif call.data == 'edit':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Подарок", callback_data='present'))
        keyboard.add(types.InlineKeyboardButton(text='Описание', callback_data='description'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Что вы хотите изменить?",
                              reply_markup=keyboard)
    elif call.data == 'present' or call.data == 'description':
        if call.data == 'present':
            bot.send_message(call.message.chat.id, 'Запишите новое значение ')
            bot.register_next_step_handler(call.message, wish_update)
        else:
            bot.send_message(call.message.chat.id, 'Запишите новое описание ')
            bot.register_next_step_handler(call.message, description_update)
    else:
        id = call.data
        wishlist_data = SqlDB.select_wish(call.data)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Удалить', callback_data='delete'))
        keyboard.add(types.InlineKeyboardButton(text='Изменить', callback_data='edit'))
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Подарок: {wishlist_data[0][0]}\nОписание: {wishlist_data[0][1]}", reply_markup=keyboard)

def wish_update(message):
    SqlDB.edit_wish(id, "wish", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id))

def description_update(message):
    SqlDB.edit_wish(id, "description", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id))

bot.infinity_polling()

"""удалять кнопки"""