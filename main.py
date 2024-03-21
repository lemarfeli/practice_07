import string  # для генерации ключа комнаты
import random

import telebot
from telebot import types
bot = telebot.TeleBot('6813501562:AAF3-i5zM2LgbO_mpdy4yRYW4mr8Z0wtKic')

#'7070533359:AAGUwBLIkXmrdD9ebAIm4WRb8QUHhFiIfvo'

from bd import SqlDB
SqlDB = SqlDB()

room_registration = {}
room_inf = {}
player = {}
player_id = {}
wish = {}
wish_id = {}


@bot.message_handler(commands=['start'])
def start(message):
    if not SqlDB.exists_user(message.from_user.id):
        SqlDB.add_new_user(message.from_user.id)

    first_mess = f"""Привет <b>{message.from_user.first_name}</b>!\n
Я - твой верный Бот помощник! Моя задача помочь тебе и всем участникам провести игру честно и максимально увлекательно.\n
Играй в Тайного Санту с коллегами, семьей, друзьями или сообществе, со всеми, с кем ты хочешь разделить радость новогодней суеты!\n
Буду рядом, чтобы помочь с любыми вопросами и сделать мероприятие по-настоящему праздничным\n
Отличной игры:)"""
    
    bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=main_markup())


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = "Нужна помощь?\n" \
                "По всем вопросам: @alekatya"

    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['rules'])
def rules_command(message):
    rules_text = "Правила игры в Тайного Санту!🎅🏻\n" \
                 "  1. Участники игры заполняют свой виш-лист\n" \
                 "  2. Организатор игры нажимает кнопку Жеребьевка\n" \
                 "  3. Каждый из игроков становится тайным Сантой. Игроку высылается виш-лист его подопечного\n" \
                 "  4. Тайный Санта выбирает, покупает и запоковывает желаемый подарок из виш-листа подопечного\n" \
                 "  5. В завимисоти от договоренности, высылаете по адресу или встречаетесь в назначенное время\n" \
                 "  6. Дарите подготовленный подарок\n" \
                 "  7. Получаете свой подарок от вашего тайного Санты\n\n" \
                 "Хорошей игры!✨"

    bot.send_message(message.chat.id, rules_text)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global delete_markup
    delete_markup = telebot.types.ReplyKeyboardRemove()

    room_registration[message.chat.id] = {}
    room_inf[message.chat.id] = {}
    wish[message.chat.id] = {}
    wish_id[message.chat.id] = {}
    player[message.chat.id] = {}
    player_id[message.chat.id] = {}
    
    if message.text == 'Создать комнату':
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
        bot.send_message(message.chat.id,
                         'Вы нажали на кнопку Войти в комнату. Введите ключ комнаты, чтобы войти в нее', parse_mode='html',
                         reply_markup=delete_markup)
        bot.register_next_step_handler(message, enter_room)
        
    elif message.text == 'Мои комнаты':
        rooms = SqlDB.get_user_rooms(message.from_user.id)
        if rooms:
            bot.send_message(message.chat.id, 'Вы состоите в следующих комнатах:', reply_markup=create_rooms_buttons(rooms, message.chat.id))
        else:
            bot.send_message(message.chat.id, 'Вы не состоите ни в одной комнате. Можете создать свою комнату самостоятельно или войти в уже существующую с помощью кнопки "Войти в комнату".')

    elif message.text == 'Виш лист':
        if not SqlDB.check_wish(message.from_user.id):
            delete_markup = telebot.types.ReplyKeyboardRemove()
            wish[message.chat.id]['check'] = "global"
            bot.send_message(message.chat.id,
                             'Вы нажали на кнопку Виш лист. Заполните Ваш виш лист', parse_mode='html',
                             reply_markup=delete_markup)
            bot.register_next_step_handler(message, wishlist)
        else:
            bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))

    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=main_markup())
    else:
        # Действия при получении другого сообщения
        bot.send_message(message.chat.id, 'я вас не понимаю', parse_mode='html', reply_markup=main_markup())


def create_buttons(user_id, word):
    wishlist_data = SqlDB.select_wishlist(user_id)
    keyboard = types.InlineKeyboardMarkup()
    for wish_item in wishlist_data:
        keyboard.add(types.InlineKeyboardButton(text=wish_item[2], callback_data=str(word)+str(wish_item[0])))
    keyboard.add(types.InlineKeyboardButton(text='Добавить', callback_data=str(word)+'add'))
    
    return keyboard


def create_rooms_buttons(rooms, userid):
    keyboard = types.InlineKeyboardMarkup()
    for room in rooms:
        room_id = room[0]
        room_name = room[1]
        player_inf = room[3]
        if room[2] == userid:
            # кнопка для организатора
            organizer_button_text = f"{room_name} (Организатор)"
            organizer_callback_data = f"organizer:{room_id}"
            keyboard.add(types.InlineKeyboardButton(text=organizer_button_text, callback_data=organizer_callback_data))
        # кнопка для участника
        participant_button_text = f"{room_name} (Участник)"
        participant_callback_data = f"participant:{player_inf}"
        keyboard.add(types.InlineKeyboardButton(text=participant_button_text, callback_data=participant_callback_data))

    return keyboard


def main_markup():
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_create_room = types.KeyboardButton('Создать комнату')
    b_enter_room = types.KeyboardButton('Войти в комнату')
    b_my_rooms = types.KeyboardButton('Мои комнаты')
    b_wishlist = types.KeyboardButton('Виш лист')
    markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)
    
    return markup_main
    

def room_reg_name(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=main_markup())
    else:
        char = 6  # количество символов в ключе
        room_key = ''.join(random.choices(string.ascii_letters + string.digits, k=char))
        room_registration[message.chat.id]['roomid'] = room_key  # ключ
        room_registration[message.chat.id]['name'] = message.text

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
            room_registration[message.chat.id]['anonymity'] = True
        elif message.text == 'Публичная':
            room_registration[message.chat.id]['anonymity'] = False
        global markup_currency

        markup_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rub = types.KeyboardButton('₽')
        eur = types.KeyboardButton('€')
        usd = types.KeyboardButton('$')
        kzt = types.KeyboardButton('₸')

        markup_currency.row(rub, eur, usd, kzt)

        bot.send_message(message.chat.id, 'Укажите валюту, в которой будет определен бюджет для подарков',
                         reply_markup=markup_currency)
        bot.register_next_step_handler(message, currency_budget)
    else:
        bot.send_message(message.chat.id, 'Я вас не понимаю')
        bot.send_message(message.chat.id,
                         'Анонимная или публичная игра?', parse_mode='html', reply_markup=markup_anonymity)
        bot.register_next_step_handler(message, room_anonymity)


def currency_budget(message):
    room_registration[message.chat.id]['budget'] = message.text

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
        room_registration[message.chat.id]['budget'] = str(budget) + ' ' +room_registration[message.chat.id]['budget']
        bot.send_message(message.chat.id, f"Сумма {budget} успешно добавлена")

        if room_registration[message.chat.id]['anonymity']:
            room_registration[message.chat.id]['sending'] = False
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
    global markup_sending
    if message.text == 'Почтой':
        room_registration[message.chat.id]['sending'] = True
        SqlDB.create_new_room(room_registration[message.chat.id]['roomid'], room_registration[message.chat.id]['name'],
                              room_registration[message.chat.id]['anonymity'], room_registration[message.chat.id]['budget'],
                              room_registration[message.chat.id]['sending'], None,
                              message.from_user.id)
        bot.send_message(message.chat.id, f'Ваши данные успешно сохранены!',
                         reply_markup=main_markup())
    elif message.text == 'Лично':
        room_registration[message.chat.id]['sending'] = False
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
    room_registration[message.chat.id]['meeting'] = message.text
    SqlDB.create_new_room(room_registration[message.chat.id]['roomid'], room_registration[message.chat.id]['name'],
                          room_registration[message.chat.id]['anonymity'], room_registration[message.chat.id]['budget'],
                          room_registration[message.chat.id]['sending'], room_registration[message.chat.id]['meeting'],
                          message.from_user.id)
    bot.send_message(message.chat.id, f'Ваши данные успешно сохранены!',
                     reply_markup=main_markup())


def enter_room(message):
    if not SqlDB.exists_room(message.text):
        bot.send_message(message.chat.id, 'Данная комната не существует, проверьте ключ')
        bot.register_next_step_handler(message, enter_room)
    else:
        if not SqlDB.exists_player_room(message.chat.id, message.text):
            roomid = message.text
            player[message.chat.id]['roomid'] = roomid
            if SqlDB.player_number(roomid) < 9:
                num = '0' + str(SqlDB.player_number(roomid) + 1)
            else:
                num = str(SqlDB.player_number(roomid) + 1)
            player[message.chat.id]['playerid'] = roomid + "_" + num

            bot.send_message(message.chat.id, 'Поздравляю вы вошли в комнату, теперь введите свое имя')
            bot.register_next_step_handler(message, player_name)
        else:
            bot.send_message(message.chat.id, 'Вы уже вошли в данную комнату', reply_markup=main_markup())


def player_name(message):
    player[message.chat.id]['name'] = message.text
    room_info = SqlDB.room_info(player[message.chat.id]['roomid'])
    if room_info[0][4]:
        bot.send_message(message.chat.id, 'Введите адрес для отправки')
        bot.register_next_step_handler(message, player_address)
    else:
        player[message.chat.id]['address'] = None
        SqlDB.add_new_player(player[message.chat.id]['playerid'], message.from_user.id,
                             player[message.chat.id]['roomid'], player[message.chat.id]['name'],
                             player[message.chat.id]['address'])
        if not SqlDB.check_wish(message.from_user.id):
            delete_markup = telebot.types.ReplyKeyboardRemove()
            wish[message.chat.id]['check'] = "local"
            bot.send_message(message.chat.id,
                             'Добавьте подарок в ваш виш лист', parse_mode='html',
                             reply_markup=delete_markup)
            bot.register_next_step_handler(message, wishlist)
        else:
            bot.send_message(message.chat.id, 'Теперь необходимо выбрать подарок',
                             reply_markup=create_buttons(message.chat.id, "local:"))


def player_address(message):
    player[message.chat.id]['address'] = message.text
    SqlDB.add_new_player(player[message.chat.id]['playerid'], message.from_user.id,
                         player[message.chat.id]['roomid'], player[message.chat.id]['name'],
                         player[message.chat.id]['address'])
    if not SqlDB.check_wish(message.from_user.id):
        delete_markup = telebot.types.ReplyKeyboardRemove()
        wish[message.chat.id]['check'] = "local"
        bot.send_message(message.chat.id,
                         'Добавьте подарок в ваш виш лист', parse_mode='html',
                         reply_markup=delete_markup)
        bot.register_next_step_handler(message, wishlist)
    else:
        bot.send_message(message.chat.id, 'Теперь необходимо выбрать подарок',
                         reply_markup=create_buttons(message.chat.id, "local:"))


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
    if wish[message.chat.id]['check'] == "local":
        bot.send_message(message.chat.id, 'Теперь необходимо выбрать подарок',
                         reply_markup=create_buttons(message.chat.id, "local:"))
    else:
        markup_wish = types.ReplyKeyboardMarkup(resize_keyboard=True)
        new_wish = types.KeyboardButton('Добавить новый подарок')
        menu = types.KeyboardButton('Вернуться в меню')
        markup_wish.add(new_wish).add(menu)
        bot.send_message(message.chat.id, f"Подарок: {wish[message.chat.id]['wish']}\nОписание: {wish[message.chat.id]['description']}\nбыли успешно добавлены в ваш виш-лист! Желаете добавить что-то еще?", reply_markup=markup_wish)
        bot.register_next_step_handler(message, wish_menu)


def wish_menu(message):
    if message.text  == 'Добавить новый подарок':
        wish[message.chat.id]['check'] = "global"
        bot.send_message(message.chat.id,f'Добавьте новый подарок в ваш виш-лист')
        bot.register_next_step_handler(message, wishlist)
    elif message.text  == 'Вернуться в меню':
        bot.send_message(message.chat.id, f'Вы вернулись в меню',
                         reply_markup=main_markup())


@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_back_button(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Ваш виш лист:", reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete")
def handle_delete_button(call):
    SqlDB.delete_wish(wish_id[call.message.chat.id]["id"])
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Ваш виш лист:",
                          reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[1] == "add")
def handle_add_button(call):
    delete_markup = telebot.types.ReplyKeyboardRemove()
    wish[call.message.chat.id]['check'] = call.data.split(":")[0]
    bot.send_message(call.message.chat.id, f'Добавьте новый подарок в ваш виш-лист', reply_markup=delete_markup)
    bot.register_next_step_handler(call.message, wishlist)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "edit")
def handle_edit_button(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Подарок", callback_data='present'))
    keyboard.add(types.InlineKeyboardButton(text='Описание', callback_data='description'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Что вы хотите изменить?",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'present' or call.data == 'description')
def handle_edit_select(call):
    if call.data == 'present':
        bot.send_message(call.message.chat.id, 'Запишите новое значение ')
        bot.register_next_step_handler(call.message, wish_update)
    else:
        bot.send_message(call.message.chat.id, 'Запишите новое описание ')
        bot.register_next_step_handler(call.message, description_update)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "global")
def handle_global_button(call):
    wish_id[call.message.chat.id]["id"] = call.data.split(":")[1]
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Удалить', callback_data='delete'))
    keyboard.add(types.InlineKeyboardButton(text='Изменить', callback_data='edit'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Подарок: {wishlist_data[0][0]}\nОписание: {wishlist_data[0][1]}",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "local")
def handle_local_button(call):
    wish_id[call.message.chat.id]["id"] = call.data.split(":")[1]
    SqlDB.add_new_local_wish(player[call.message.chat.id]['playerid'], wish_id[call.message.chat.id]["id"])
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Подарок {wishlist_data[0][0]} был успешно добавлен в локальный виш лист")
    bot.send_message(call.message.chat.id, 'Ваши данные в комнате были сохранены', reply_markup=main_markup())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "organizer")
def handle_organizer_button(call):
    pass


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "participant")
def handle_participant_button(call):
    player[call.message.chat.id]["id"] = call.data.split(":")[1]
    room_registration[call.message.chat.id]["id"] = player[call.message.chat.id]["id"].split("_")[0]
    player[call.message.chat.id]["name"] = SqlDB.player_info(call.message.chat.id, room_registration[call.message.chat.id]["id"])[0][3]
    room_inf[call.message.chat.id] = SqlDB.room_info(room_registration[call.message.chat.id]["id"])[0]
    room_registration[call.message.chat.id]["name"] = room_inf[call.message.chat.id][1]
    room_registration[call.message.chat.id]["budget"] = room_inf[call.message.chat.id][3]
    room_registration[call.message.chat.id]["meeting"] = room_inf[call.message.chat.id][5]
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"""Наименование комнаты: {room_registration[call.message.chat.id]['name']}
Бюджет: {room_registration[call.message.chat.id]["budget"]}
Место встречи: {room_registration[call.message.chat.id]["meeting"]}
Ваше имя: {player[call.message.chat.id]["name"]}""")


def wish_update(message):
    SqlDB.edit_wish(id[message.chat.id]["id"], "wish", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))

def description_update(message):
    SqlDB.edit_wish(id[message.chat.id]["id"], "description", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))

current_image_index = 0  # текущий индекс изображения

def show_image(message, image_index):
    # путь
    image_path = f".../{image_index}.jpg"  
    
    with open(image_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    
    # кнопки назад-вперед
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(text="◀️", callback_data="prev"),
        types.InlineKeyboardButton(text="▶️", callback_data="next")
    )
    
    bot.send_message(message.chat.id, reply_markup=keyboard)

@bot.message_handler(commands=['advice'])
def advice(message):
    global current_image_index
    show_image(message, current_image_index)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global current_image_index
    
    if call.data == 'next':
        current_image_index += 1
    elif call.data == 'prev':
        current_image_index -= 1
    
    # ограничить количество !!! там где 9 - наше количество скринов
    current_image_index = max(0, min(current_image_index, 9))
    
    show_image(call.message, current_image_index)


bot.set_my_commands([
    types.BotCommand("/start", "Перезапуск бота"),
    types.BotCommand("/help", "Помощь"),
    types.BotCommand("/rules", "Правила игры"),
    types.BotCommand("/advice", "Советы")
])
bot.infinity_polling()

"""удалять кнопки"""
