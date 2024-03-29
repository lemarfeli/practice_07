import string  # для генерации ключа комнаты
import random
import telebot
from telebot import types
from bd import SqlDB

SqlDB = SqlDB()
#'7070533359:AAGUwBLIkXmrdD9ebAIm4WRb8QUHhFiIfvo'
bot = telebot.TeleBot('6813501562:AAF3-i5zM2LgbO_mpdy4yRYW4mr8Z0wtKic')

room_registration = {}
room_inf = {}
player = {}
player_inf = {}
wish = {}
wish_inf = {}

budget = {}

@bot.message_handler(commands=['start'])
def start(message):
    room_registration[message.chat.id] = {}
    room_inf[message.chat.id] = {}
    wish[message.chat.id] = {}
    wish_inf[message.chat.id] = {}
    player[message.chat.id] = {}
    player_inf[message.chat.id] = {}
    
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


@bot.message_handler(func=lambda message: message.text == 'Создать комнату')
def handle_message_create_room(message):
    bot.send_message(message.chat.id,
                     'Вы нажали на кнопку Создать комнату. Введите название комнаты или выберите из предложенных',
                     parse_mode='html', reply_markup=room_name_markup())
    bot.register_next_step_handler(message, room_reg_name)


@bot.message_handler(func=lambda message: message.text == 'Войти в новую комнату')
def handle_message_enter_room(message):
    bot.send_message(message.chat.id,
                     'Вы нажали на кнопку Войти в комнату. Введите ключ комнаты, чтобы войти в нее', parse_mode='html',
                     reply_markup=back_markup())
    bot.register_next_step_handler(message, enter_room)


@bot.message_handler(func=lambda message: message.text == 'Мои комнаты')
def handle_message_my_room(message):
    if SqlDB.get_user_rooms(message.from_user.id) or SqlDB.get_org_rooms(message.from_user.id):
        bot.send_message(message.chat.id, 'Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id,
                         'Вы не состоите ни в одной комнате. Можете создать свою комнату самостоятельно или войти в уже существующую с помощью кнопки "Войти в комнату".')


@bot.message_handler(func=lambda message: message.text == 'Виш лист')
def handle_message_wishlist(message):
    if not SqlDB.check_wish(message.from_user.id):
        wish[message.chat.id]['check'] = "global"
        bot.send_message(message.chat.id,
                         'Вы нажали на кнопку Виш лист. Заполните Ваш виш лист', parse_mode='html',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, wishlist)
    else:
        bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))


@bot.message_handler(
    func=lambda message: message.text not in ('Создать комнату', 'Войти в новую комнату', 'Мои комнаты', 'Виш лист'))
def handle_message_ignor(message):
    # Действия при получении другого сообщения
    bot.send_message(message.chat.id, 'я вас не понимаю', parse_mode='html', reply_markup=main_markup())


def create_buttons(user_id, word):
    if word == "wish:":
        wishlist_data = SqlDB.presents(user_id)
    else:
        wishlist_data = SqlDB.select_wishlist(user_id)
    keyboard = types.InlineKeyboardMarkup()
    for wish_item in wishlist_data:
        keyboard.add(types.InlineKeyboardButton(text=wish_item[2], callback_data=str(word)+str(wish_item[0])))
    keyboard.add(types.InlineKeyboardButton(text='Добавить', callback_data='add:' + str(word)))
    
    return keyboard


def create_players_buttons(roomid):
    player_data = SqlDB.room_players(roomid)
    keyboard = types.InlineKeyboardMarkup()
    for player_room in player_data:
        keyboard.add(types.InlineKeyboardButton(text=player_room[1], callback_data='player:' + str(player_room[0])))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data=f'organizer:{roomid}'))
    
    return keyboard


def create_rooms_buttons(userid):
    keyboard = types.InlineKeyboardMarkup()
    rooms = SqlDB.get_user_rooms(userid)
    orgs = SqlDB.get_org_rooms(userid)
    if rooms:
        for room in rooms:
            room_name = room[1]
            player_inf = room[2]
            # кнопка для участника
            player_button_text = f"{room_name} (Участник)"
            player_callback_data = f"participant:{player_inf}"
            keyboard.add(types.InlineKeyboardButton(text=player_button_text, callback_data=player_callback_data))
    if orgs:
        for org in orgs:
            room_id = org[0]
            room_name = org[1]
            # кнопка для организатора
            organizer_button_text = f"{room_name} (Организатор)"
            organizer_callback_data = f"organizer:{room_id}"
            keyboard.add(types.InlineKeyboardButton(text=organizer_button_text, callback_data=organizer_callback_data))

    return keyboard


def back_markup():
    markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_button = types.KeyboardButton('Назад')
    markup_back.add(back_button)

    return markup_back


def main_markup():
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_create_room = types.KeyboardButton('Создать комнату')
    b_enter_room = types.KeyboardButton('Войти в комнату')
    b_my_rooms = types.KeyboardButton('Мои комнаты')
    b_wishlist = types.KeyboardButton('Виш лист')
    markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)
    
    return markup_main
    

def room_name_markup():
    markup_room_name = types.ReplyKeyboardMarkup(resize_keyboard=True)
    name_1 = types.KeyboardButton('Тест игры⚙️')
    name_2 = types.KeyboardButton('Друзья🤩')
    name_3 = types.KeyboardButton('Коллеги📚')
    name_4 = types.KeyboardButton('Одногруппники😎')
    back = types.KeyboardButton('Назад')
    markup_room_name.row(name_1, name_2).row(name_3, name_4).add(back)

    return markup_room_name


def currency_markup():
    markup_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
    rub = types.KeyboardButton('₽')
    eur = types.KeyboardButton('€')
    usd = types.KeyboardButton('$')
    kzt = types.KeyboardButton('₸')
    back = types.KeyboardButton('Назад')
    markup_currency.row(rub, eur, usd, kzt).add(back)

    return markup_currency


def budget_markup():
    markup_budget = types.ReplyKeyboardMarkup(resize_keyboard=True)
    budget_300 = types.KeyboardButton('300')
    budget_500 = types.KeyboardButton('500')
    budget_1000 = types.KeyboardButton('1000')
    budget_1500 = types.KeyboardButton('1500')
    back = types.KeyboardButton('Назад')
    markup_budget.row(budget_300, budget_500).row(budget_1000, budget_1500).add(back)

    return markup_budget


def sending_markup():
    markup_sending = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    post = types.KeyboardButton('Почтой')
    ofline = types.KeyboardButton('Лично')
    back = types.KeyboardButton('Назад')
    markup_sending.add(post, ofline).add(back)

    return markup_sending


def room_reg_name(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=main_markup())
    else:
        char = 6  # количество символов в ключе
        room_key = ''.join(random.choices(string.ascii_letters + string.digits, k=char))
        room_registration[message.chat.id]['roomid'] = room_key  # ключ
        if len(message.text) <= 64:
            room_registration[message.chat.id]['name'] = message.text
            bot.send_message(message.chat.id, 'Укажите валюту, в которой будет определен бюджет для подарков',
                             reply_markup=currency_markup())
            bot.register_next_step_handler(message, currency_budget)
        else:
            bot.send_message(message.chat.id, 'Название слишком длинное, попробуйте снова')
            bot.register_next_step_handler(message, room_reg_name)


def currency_budget(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id,
                         'Введите название комнаты или выберите из предложенных',
                         parse_mode='html', reply_markup=room_name_markup())
        bot.register_next_step_handler(message, room_reg_name)
    else:
        room_registration[message.chat.id]['budget'] = message.text
        bot.send_message(message.chat.id,
                         'Какой бюджет на подарки? Выберите из частых вариантов или укажите ваш лимит суммы.',
                         reply_markup=budget_markup())
        bot.register_next_step_handler(message, room_budget)


def room_budget(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Укажите валюту, в которой будет определен бюджет для подарков',
                         reply_markup=currency_markup())
        bot.register_next_step_handler(message, currency_budget)
    else:
        try:
            budget = float(message.text.replace(',', '.'))
            if budget.is_integer():
                budget = int(budget)
            if budget <= 0:
                raise Exception
            room_registration[message.chat.id]['budget'] = str(budget) + ' ' +room_registration[message.chat.id]['budget']
            bot.send_message(message.chat.id, f"Сумма {budget} успешно добавлена")    
            bot.send_message(message.chat.id, 'Выбор отправки почтой или вручение лично?',
                             parse_mode='html', reply_markup=sending_markup())
            bot.register_next_step_handler(message, room_sending)
        except Exception:
            bot.send_message(message.chat.id, 'Введите корректные данные', reply_markup=budget_markup())
            bot.register_next_step_handler(message, room_budget)
    

def room_sending(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id,
                         'Какой бюджет на подарки? Выберите из частых вариантов или укажите ваш лимит суммы.',
                         reply_markup=budget_markup())
        bot.register_next_step_handler(message, room_budget)
    else:
        if message.text == 'Почтой':
            room_registration[message.chat.id]['sending'] = True
            SqlDB.create_new_room(room_registration[message.chat.id]['roomid'], room_registration[message.chat.id]['name'],
                                  room_registration[message.chat.id]['budget'], room_registration[message.chat.id]['sending'], 
                                  None, message.from_user.id)
            bot.send_message(message.chat.id, f'Ваши данные успешно сохранены!',
                             reply_markup=main_markup())
        elif message.text == 'Лично':
            room_registration[message.chat.id]['sending'] = False
            bot.send_message(message.chat.id, 'Теперь укажите место и дату проведения', reply_markup=back_markup())
            bot.register_next_step_handler(message, room_meeting)
    
        else:
            bot.send_message(message.chat.id, 'Я вас не понимаю')
            bot.send_message(message.chat.id,
                             'Выбор отправки почтой или вручение лично?',
                             parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, room_sending)
    

def room_meeting(message):    
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Выбор отправки почтой или вручение лично?', parse_mode='html',
                         reply_markup=sending_markup())
        bot.register_next_step_handler(message, room_sending)
    else:
    room_registration[message.chat.id]['meeting'] = message.text
    SqlDB.create_new_room(room_registration[message.chat.id]['roomid'], room_registration[message.chat.id]['name'],
                          room_registration[message.chat.id]['budget'], room_registration[message.chat.id]['sending'], 
                          room_registration[message.chat.id]['meeting'], message.from_user.id)
    bot.send_message(message.chat.id, f'Ваши данные успешно сохранены! Код комнаты {room_registration[message.chat.id]['roomid']}',
                     reply_markup=main_markup())


def enter_room(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=main_markup())
    else:
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
    
                bot.send_message(message.chat.id, 'Поздравляю вы вошли в комнату, теперь введите свое имя',  reply_markup=telebot.types.ReplyKeyboardRemove()))
                bot.register_next_step_handler(message, player_name)
            else:
                bot.send_message(message.chat.id, 'Вы уже вошли в данную комнату', reply_markup=main_markup())


def player_name(message):
    if len(message.text) <= 64:
        player[message.chat.id]['name'] = message.text
        room_info = SqlDB.room_info(player[message.chat.id]['roomid'])
        if room_info[0][3]:
            player[message.chat.id]['post'] = True
            bot.send_message(message.chat.id, 'Введите адрес для отправки')
            bot.register_next_step_handler(message, player_address)
        else:
            bot.send_message(message.chat.id, 'Хотите получить подарок лично или почтой?', parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)
    else:
        bot.send_message(message.chat.id, 'Имя слишком длинное, попробуйте снова')
        bot.register_next_step_handler(message, player_name)


def player_sending(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Введите свое имя',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, player_name)
    else:
        if message.text == 'Почтой':
            player[message.chat.id]['post'] = True
            bot.send_message(message.chat.id, 'Введите адрес для отправки', reply_markup=back_markup())
            bot.register_next_step_handler(message, player_address)
        elif message.text == 'Лично':
            player[message.chat.id]['post'] = False
            player[message.chat.id]['address'] = None
            SqlDB.add_new_player(player[message.chat.id]['playerid'], message.from_user.id,
                                 player[message.chat.id]['roomid'], player[message.chat.id]['name'],
                                 player[message.chat.id]['post'], player[message.chat.id]['address'])
            if not SqlDB.check_wish(message.from_user.id):
                wish[message.chat.id]['check'] = "local"
                bot.send_message(message.chat.id,
                                 'Добавьте подарок в ваш виш лист', parse_mode='html',
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, wishlist)
            else:
                bot.send_message(message.chat.id, 'Данные были сохранены', parse_mode='html',
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.send_message(message.chat.id, 'Теперь необходимо выбрать подарок',
                                 reply_markup=create_buttons(message.chat.id, "local:"))
        else:
            bot.send_message(message.chat.id, 'Я вас не понимаю')
            bot.send_message(message.chat.id,
                             'Выбор отправки почтой или вручение лично?',
                             parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)

def player_address(message):
    if message.text == 'Назад':
        room_info = SqlDB.room_info(player[message.chat.id]['roomid'])
        if room_info[0][3]:
            bot.send_message(message.chat.id, 'Введите адрес для отправки')
            bot.register_next_step_handler(message, player_address)
        else:
            bot.send_message(message.chat.id, 'Хотите получить подарок лично или почтой?', parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)
    else:
        player[message.chat.id]['address'] = message.text
        SqlDB.add_new_player(player[message.chat.id]['playerid'], message.from_user.id,
                             player[message.chat.id]['roomid'], player[message.chat.id]['name'],
                             player[message.chat.id]['post'], player[message.chat.id]['address']), 
        if not SqlDB.check_wish(message.from_user.id):
            wish[message.chat.id]['check'] = "local"
            bot.send_message(message.chat.id,
                             'Добавьте подарок в ваш виш лист', parse_mode='html',
                             reply_markup=telebot.types.ReplyKeyboardRemove())
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


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "back")
def handle_back_button(call):
    if call.data.split(":")[1] == 'wish':
        keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад',
                                                callback_data='participant:' + player[call.message.chat.id][
                                                    "playerid"]))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Ваш список подарков:",
                              reply_markup=keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Ваш виш лист:", reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "delete")
def handle_delete_button(call):
    if call.data.split(":")[1] == "wish":
        SqlDB.delete_local(player[call.message.chat.id]["playerid"], wish_inf[call.message.chat.id]["id"])
        if not SqlDB.presents(player[call.message.chat.id]["playerid"]):
            wish[call.message.chat.id]['check'] = "local"
            if not SqlDB.check_wish(call.message.chat.id):
                bot.send_message(call.message.chat.id,
                                 'Добавьте подарок в ваш виш лист', parse_mode='html',
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.register_next_step_handler(call.message, wishlist)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Добавьте подарок в ваш виш лист',
                                      reply_markup=create_buttons(call.message.chat.id, "local:"))
        else:
            keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='participant:' + player[call.message.chat.id]["playerid"]))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Ваш список подарков:",
                                  reply_markup=keyboard)
    else:
        SqlDB.delete_wish(wish_inf[call.message.chat.id]["id"])
        if not SqlDB.check_wish(call.message.chat.id):
            wish[call.message.chat.id]['check'] = "global"
            bot.send_message(call.message.chat.id,
                             'Ваш виш лист пуст. Заполните его новыми подарками', parse_mode='html',
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(call.message, wishlist)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Ваш виш лист:",
                                  reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "add")
def handle_add_button(call):
    wish[call.message.chat.id]['check'] = call.data.split(":")[1]
    if wish[call.message.chat.id]['check'] == "wish":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Добавьте подарок в ваш виш лист',
                              reply_markup=create_buttons(call.message.chat.id, "local:"))
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f'Добавьте новый подарок в ваш виш-лист',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, wishlist)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "edit")
def handle_edit_button(call):
    keyboard = types.InlineKeyboardMarkup()
    wish[call.message.chat.id]['check'] = call.data.split(":")[1]
    keyboard.add(types.InlineKeyboardButton(text="Подарок", callback_data='present'))
    keyboard.add(types.InlineKeyboardButton(text='Описание', callback_data='description'))
    keyboard.add(
        types.InlineKeyboardButton(text='Назад', callback_data=call.data.split(":")[1] + ':' + str(wish_inf[call.message.chat.id]["id"])))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Что вы хотите изменить?",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data in ('present', 'description', 'name_room', 'budget', 'meeting', 'name', 'address', 'post'))
def handle_edit_select(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Запишите новое значение")
    if call.data == 'present':
        bot.register_next_step_handler(call.message, wish_update)
    elif call.data == 'description':
        bot.register_next_step_handler(call.message, description_update)
    elif call.data == 'name_room':
        bot.register_next_step_handler(call.message, name_room_update)
    elif call.data == 'budget':
        bot.send_message(call.message.chat.id, 'Укажите валюту в которой будет определяться бюджет')
        bot.register_next_step_handler(call.message, budget_update)
    elif call.data == 'meeting':
        bot.register_next_step_handler(call.message, meeting_update)
    elif call.data == 'name':
        bot.register_next_step_handler(call.message, name_update)
    elif call.data == 'address':
        bot.register_next_step_handler(call.message, address_update)
    elif call.data == 'post':
        bot.send_message(call.message.chat.id, 'Хотите получить подарок почтой или лично?', reply_markup=sending_markup())
        bot.register_next_step_handler(call.message, post_update)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "global" or call.data.split(":")[0] == "wish")
def handle_global_button(call):
    wish_id[call.message.chat.id]["id"] = call.data.split(":")[1]
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Удалить', callback_data='delete:' + call.data.split(":")[0]))
    keyboard.add(types.InlineKeyboardButton(text='Изменить', callback_data='edit:' + call.data.split(":")[0]))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back:' + call.data.split(":")[0]))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Подарок: {wishlist_data[0][0]}\nОписание: {wishlist_data[0][1]}",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "local")
def handle_local_button(call):
    wish_id[call.message.chat.id]["id"] = call.data.split(":")[1]
    SqlDB.add_new_local_wish(player[call.message.chat.id]['playerid'], wish_id[call.message.chat.id]["id"])
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Добавить еще подарок', callback_data='add_present'))
    keyboard.add(types.InlineKeyboardButton(text='Завершить', callback_data='quite_registration'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Подарок {wishlist_data[0][0]} был успешно добавлен в локальный виш лист", reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "add_present")
def handle_add_present_button(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Выберите подарок', reply_markup=create_buttons(call.message.chat.id, "local:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "quite_registration")
def handle_organizer_button(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, 'Ваши данные в комнате были сохранены', reply_markup=main_markup())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "organizer")
def handle_organizer_button(call):
    room_registration[call.message.chat.id]["id"] = call.data.split(":")[1].split("_")[0]
    room_inf[call.message.chat.id] = SqlDB.room_info(room_registration[call.message.chat.id]["id"])[0]
    room_registration[call.message.chat.id]["name"] = room_inf[call.message.chat.id][1]
    room_registration[call.message.chat.id]["budget"] = room_inf[call.message.chat.id][2]
    if room_inf[call.message.chat.id][3]:
        room_registration[call.message.chat.id]["meeting"] = 'Подарки отправляются почтой'
    else:
        room_registration[call.message.chat.id]["meeting"] = room_inf[call.message.chat.id][4]
    info_text = f"Ключ комнаты: {room_registration[call.message.chat.id]['id']}\n" \
                f"Наименование комнаты: {room_registration[call.message.chat.id]['name']}\n" \
                f"Бюджет: {room_registration[call.message.chat.id]['budget']}\n" \
                f"Место встречи: {room_registration[call.message.chat.id]['meeting']}\n"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Удалить комнату', callback_data='delete_room'))
    keyboard.add(types.InlineKeyboardButton(text='Удалить игрока', callback_data='delete_player'))
    keyboard.add(types.InlineKeyboardButton(text='Изменить данные', callback_data='edit_room'))
    if (SqlDB.room_players(room_registration[call.message.chat.id]["id"]) and
            SqlDB.pair(room_registration[call.message.chat.id]["id"])):
        keyboard.add(types.InlineKeyboardButton(text='Результат жеребьевки', callback_data='toss_up_result:room'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='Провести жеребьевку', callback_data='toss_up'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back_room'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=info_text, reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_room")
def handle_back_room_button(call):
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Вы состоите в следующих комнатах:',
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=
        'Вы не состоите ни в одной комнате. Можете создать свою комнату самостоятельно или войти в уже существующую с помощью кнопки "Войти в комнату".')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "edit_room")
def handle_edit_room_button(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Название комнаты', callback_data='name_room'))
    keyboard.add(types.InlineKeyboardButton(text='Бюджет', callback_data='budget'))
    if not (room_inf[call.message.chat.id][3]):
        keyboard.add(types.InlineKeyboardButton(text='Место встречи', callback_data='meeting'))
    keyboard.add(types.InlineKeyboardButton(text='Назад',
                                            callback_data=f'organizer:{room_registration[call.message.chat.id]["id"]}'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Что вы хотите изменить?",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete_room")
def handle_delete_room_button(call):
    SqlDB.delete_room(room_registration[call.message.chat.id]["id"])
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Вы состоите в следующих комнатах:',
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=
        'Вы не состоите ни в одной комнате. Можете создать свою комнату самостоятельно или войти в уже существующую с помощью кнопки "Войти в комнату".')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete_player")
def handle_delete_player_button(call):
    if SqlDB.room_players(room_registration[call.message.chat.id]["id"]):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Список участников игры:",
                              reply_markup=create_players_buttons(room_registration[call.message.chat.id]["id"]))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="В игру еще никто не вступил",
                              reply_markup=create_players_buttons(room_registration[call.message.chat.id]["id"]))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "player")
def handle_delete_player_button(call):
    SqlDB.delete_player(call.data.split(":")[1])
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Вы состоите в следующих комнатах:',
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=
        'Вы не состоите ни в одной комнате. Можете создать свою комнату самостоятельно или войти в уже существующую с помощью кнопки "Войти в комнату".')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "participant")
def handle_participant_button(call):
    player[call.message.chat.id]["playerid"] = call.data.split(":")[1]
    player_inf[call.message.chat.id] = SqlDB.player_info(player[call.message.chat.id]["playerid"])[0]
    player[call.message.chat.id]["name"] = player_inf[call.message.chat.id][3]
    room_registration[call.message.chat.id]["id"] = player[call.message.chat.id]["playerid"].split("_")[0]
    room_inf[call.message.chat.id] = SqlDB.room_info(room_registration[call.message.chat.id]["id"])[0]
    room_registration[call.message.chat.id]["name"] = room_inf[call.message.chat.id][1]
    room_registration[call.message.chat.id]["budget"] = room_inf[call.message.chat.id][2]
    if player_inf[call.message.chat.id][4]:
        room_registration[call.message.chat.id]["meeting"] = player_inf[call.message.chat.id][5]
    else:
        room_registration[call.message.chat.id]["meeting"] = room_inf[call.message.chat.id][4]
    info_text = f"Ваше имя: {player[call.message.chat.id]['name']}\n" \
                f"Ключ комнаты: {room_registration[call.message.chat.id]['id']}\n" \
                f"Наименование комнаты: {room_registration[call.message.chat.id]['name']}\n" \
                f"Бюджет: {room_registration[call.message.chat.id]['budget']}\n" \
                f"Адрес для получения подарка: {room_registration[call.message.chat.id]['meeting']}\n"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Выйти из комнаты',
                                            callback_data=f'player:{player[call.message.chat.id]["playerid"]}'))
    keyboard.add(types.InlineKeyboardButton(text='Изменить данные', callback_data='edit_player'))
    keyboard.add(types.InlineKeyboardButton(text='Подарки', callback_data='wishlist'))
    if (SqlDB.room_players(room_registration[call.message.chat.id]["id"]) and
            SqlDB.pair(room_registration[call.message.chat.id]["id"])):
        keyboard.add(types.InlineKeyboardButton(text='Результат жеребьевки', callback_data='toss_up_result:player'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='back_room'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=info_text, reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "wishlist")
def handle_wishlist_button(call):
    if not SqlDB.presents(player[call.message.chat.id]["playerid"]):
        wish[call.message.chat.id]['check'] = "local"
        if not SqlDB.check_wish(call.message.chat.id):
            bot.send_message(call.message.chat.id,
                             'Добавьте подарок в ваш виш лист', parse_mode='html',
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(call.message, wishlist)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Добавьте подарок в ваш виш лист',
                                  reply_markup=create_buttons(call.message.chat.id, "local:"))
    else:
        keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='participant:' + player[call.message.chat.id]["playerid"]))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Ваш список подарков:",
                              reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "edit_player")
def handle_edit_room_button(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Имя', callback_data='name'))
    if not (room_inf[call.message.chat.id][3]):
        keyboard.add(types.InlineKeyboardButton(text='Способ получения подарка', callback_data='post'))
    if player_inf[call.message.chat.id][4]:
        keyboard.add(types.InlineKeyboardButton(text='Адрес', callback_data='address'))
    keyboard.add(types.InlineKeyboardButton(text='Назад',
                                            callback_data=f'participant:{player[call.message.chat.id]["playerid"]}'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Что вы хотите изменить?",
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


def wish_update(message):
    SqlDB.edit_wish(wish_inf[message.chat.id]["id"], "wish", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    if wish[message.chat.id]['check'] == "wish":
        keyboard = create_buttons(player[message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад',
                                                callback_data='participant:' + player[message.chat.id]["playerid"]))
        bot.send_message(message.chat.id, "Ваш список подарков:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))


def description_update(message):
    SqlDB.edit_wish(wish_inf[message.chat.id]["id"], "description", message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    if wish[message.chat.id]['check'] == "wish":
        keyboard = create_buttons(player[message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад',
                                                callback_data='participant:' + player[message.chat.id]["playerid"]))
        bot.send_message(message.chat.id, "Ваш список подарков:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Ваш виш лист:", reply_markup=create_buttons(message.from_user.id, "global:"))


def name_room_update(message):
    if len(message.text) <= 64:
        SqlDB.edit("room",  "name", "roomid", room_registration[message.chat.id]["id"], message.text)
        bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
        bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, 'Название слишком длинное, попробуйте снова')
        bot.register_next_step_handler(message, room_reg_name)


def name_update(message):
    if len(message.text) <= 64:
        SqlDB.edit("player",  "name", "playerid", player[message.chat.id]["playerid"], message.text)
        bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
        bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, 'Имя слишком длинное, попробуйте снова')
        bot.register_next_step_handler(message, room_reg_name)


def address_update(message):
    SqlDB.edit("player", "address", "playerid", player[message.chat.id]["playerid"], message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                     reply_markup=create_rooms_buttons(message.chat.id))


def post_update(message):
    if message.text == 'Почтой':
        player[message.chat.id]['post'] = True
        SqlDB.edit("player", "post", "playerid", player[message.chat.id]["playerid"],
                   player[message.chat.id]['post'])
        bot.send_message(message.chat.id, 'Введите адрес для отправки')
        bot.register_next_step_handler(message, address_update)
    elif message.text == 'Лично':
        player[message.chat.id]['post'] = False
        SqlDB.edit("player", "address", "playerid", player[message.chat.id]["playerid"], None)
        SqlDB.edit("player", "post", "playerid", player[message.chat.id]["playerid"],
                   player[message.chat.id]['post'])
        bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
        bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, 'Хотите получить подарок почтой или лично?',
                         reply_markup=sending_markup())
        bot.register_next_step_handler(message, post_update)


def budget_update(message):
    budget[message.chat.id] = {}
    budget[message.chat.id]['cur'] = message.text
    bot.send_message(message.chat.id, 'Теперь укажите сумму')
    bot.register_next_step_handler(message, budget_amount_update)


def budget_amount_update(message):
    try:
        budget[message.chat.id]['amount'] = float(message.text.replace(',', '.'))
        if budget[message.chat.id]['amount'].is_integer():
            budget[message.chat.id]['amount'] = int(budget[message.chat.id]['amount'])
        if budget[message.chat.id]['amount'] <= 0:
            raise Exception
        SqlDB.edit("room", "budget", "roomid", room_registration[message.chat.id]["id"],
                        str(budget[message.chat.id]['amount']) + ' ' + budget[message.chat.id]['cur'])
        bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
        bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                         reply_markup=create_rooms_buttons(message.chat.id))
    except Exception:
        bot.send_message(message.chat.id, 'Введите корректные данные')
        bot.register_next_step_handler(message, budget_amount_update)


def meeting_update(message):
    SqlDB.edit("room", "meeting", "roomid", room_registration[message.chat.id]["id"], message.text)
    bot.send_message(message.chat.id, 'Отлично! Изменения внесены ')
    bot.send_message(message.chat.id, text='Вы состоите в следующих комнатах:',
                     reply_markup=create_rooms_buttons(message.chat.id))


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
