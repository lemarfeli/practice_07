import string  # для управления символами в ключе комнаты
import random  # для генерации ключа комнаты
import telebot
from messages import text_mess
from telebot import types
from bd import SqlDB

SqlDB = SqlDB()
bot = telebot.TeleBot('7070533359:AAGUwBLIkXmrdD9ebAIm4WRb8QUHhFiIfvo')

room_registration = {}
room_inf = {}
player = {}
player_inf = {}
wish = {}
wish_inf = {}

val = {}


@bot.message_handler(commands=['start'])
def start_command(message):
    room_registration[message.chat.id] = {}
    room_inf[message.chat.id] = {}
    wish[message.chat.id] = {}
    wish_inf[message.chat.id] = {}
    player[message.chat.id] = {}
    player_inf[message.chat.id] = {}
    val[message.chat.id] = {}
    val[message.chat.id]['current_image_index'] = 0  # текущий индекс изображения для обучения

    if not SqlDB.exists_user(message.from_user.id):
        SqlDB.add_new_user(message.from_user.id)
    bot.send_message(message.chat.id, text_mess['first_mess'].format(message.from_user.first_name), parse_mode='html', reply_markup=main_markup())
    advice(message)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, text_mess['help_text'])


@bot.message_handler(commands=['rules'])
def rules_command(message):
    bot.send_message(message.chat.id, text_mess['rules_text'])


def show_image(message):
    # кнопки назад-вперед
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(text="◀️", callback_data="prev"),
        types.InlineKeyboardButton(text="▶️", callback_data="next")
    ).add(types.InlineKeyboardButton(text="Завершить", callback_data="exit_advice"))
    # путь
    val[message.chat.id]['image_path'] = f"./photo/{val[message.chat.id]['current_image_index']}.jpg"
    with open(val[message.chat.id]['image_path'], 'rb') as photo:
        bot.edit_message_media(media=types.InputMediaPhoto(photo, caption=text_mess[f"advice_text_{val[message.chat.id]['current_image_index']}"], parse_mode='html'), chat_id=message.chat.id,
                               message_id=message.message_id, reply_markup=keyboard)


@bot.message_handler(commands=['advice'])
def advice(message):
    global current_image_index
    # кнопки назад-вперед
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(text="◀️", callback_data="prev"),
        types.InlineKeyboardButton(text="▶️", callback_data="next")
    ).add(types.InlineKeyboardButton(text="Завершить", callback_data="exit_advice"))
    bot.send_photo(message.chat.id, open("./photo/0.jpg", 'rb'), caption=text_mess[f"advice_text_{val[message.chat.id]['current_image_index']}"], parse_mode='html', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "exit_advice")
def callback_handler_exit_advice(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, text_mess['advice_text_done'], reply_markup=main_markup())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "next" or call.data == "prev")
def callback_handler_next(call):
    if call.data == 'next':
        val[call.message.chat.id]['current_image_index'] += 1
        if val[call.message.chat.id]['current_image_index'] > 5:
            val[call.message.chat.id]['current_image_index'] = 0
    elif call.data == 'prev':
        val[call.message.chat.id]['current_image_index'] -= 1
        if val[call.message.chat.id]['current_image_index'] < 0:
            val[call.message.chat.id]['current_image_index'] = 5

    # ограничить количество !!! там где 9 - наше количество скринов
    val[call.message.chat.id]['current_image_index'] = max(0, min(val[call.message.chat.id]['current_image_index'], 5))
    show_image(call.message)
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == 'Создать комнату🏠')
def handle_message_create_room(message):
    bot.send_message(message.chat.id,
                     text_mess['create_room_name'], parse_mode='html', reply_markup=room_name_markup())
    bot.register_next_step_handler(message, room_reg_name)


@bot.message_handler(func=lambda message: message.text == 'Войти в новую комнату🔑')
def handle_message_enter_room(message):
    bot.send_message(message.chat.id,
                     text_mess['enter_new_room'], parse_mode='html', reply_markup=back_markup())
    bot.register_next_step_handler(message, enter_room)


@bot.message_handler(func=lambda message: message.text == 'Мои комнаты🏘️')
def handle_message_my_room(message):
    if SqlDB.get_user_rooms(message.from_user.id) or SqlDB.get_org_rooms(message.from_user.id):
        bot.send_message(message.chat.id, text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, text_mess['user_room_error'])


@bot.message_handler(func=lambda message: message.text == 'Виш лист🎁')
def handle_message_wishlist(message):
    if not SqlDB.check_wish(message.from_user.id):
        wish[message.chat.id]['check'] = "global"
        bot.send_message(message.chat.id, text_mess['global_wl'], parse_mode='html', reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, wishlist)
    else:
        bot.send_message(message.chat.id, text_mess['user_wl'], reply_markup=create_buttons(message.from_user.id, "global:"))


@bot.message_handler(
    func=lambda message: message.text not in ('Создать комнату🏠', 'Войти в новую комнату🔑', 'Мои комнаты🏘️', 'Виш лист🎁'))
def handle_message_ignor(message):
    # Действия при получении другого сообщения
    bot.send_message(message.chat.id, text_mess['dont_understand'], reply_markup=main_markup())


def create_buttons(user_id, word):
    if word == "wish:":
        wishlist_data = SqlDB.presents(user_id)
    elif word == "local:":
        wishlist_data = SqlDB.select_local_wishlist(user_id)
    else:
        wishlist_data = SqlDB.select_wishlist(user_id)
    keyboard = types.InlineKeyboardMarkup()
    for wish_item in wishlist_data:
        keyboard.add(types.InlineKeyboardButton(text=wish_item[0], callback_data=str(word) + str(wish_item[1])))
    keyboard.add(types.InlineKeyboardButton(text='Добавить', callback_data='add:' + str(word)))

    return keyboard


def create_players_buttons(roomid):
    player_data = SqlDB.room_players(roomid)
    keyboard = types.InlineKeyboardMarkup()
    for player_room in player_data:
        keyboard.add(types.InlineKeyboardButton(text=player_room[1], callback_data='player:' + str(player_room[0])))
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data=f'organizer:{roomid}'))

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
    back_button = types.KeyboardButton('Назад↩️')
    markup_back.add(back_button)

    return markup_back


def main_markup():
    markup_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_create_room = types.KeyboardButton('Создать комнату🏠')
    b_enter_room = types.KeyboardButton('Войти в новую комнату🔑')
    b_my_rooms = types.KeyboardButton('Мои комнаты🏘️')
    b_wishlist = types.KeyboardButton('Виш лист🎁')
    markup_main.add(b_create_room).add(b_enter_room).add(b_my_rooms).add(b_wishlist)

    return markup_main


def room_name_markup():
    markup_room_name = types.ReplyKeyboardMarkup(resize_keyboard=True)
    name_1 = types.KeyboardButton('Тест игры⚙️')
    name_2 = types.KeyboardButton('Друзья🤩')
    name_3 = types.KeyboardButton('Коллеги📚')
    name_4 = types.KeyboardButton('Одногруппники😎')
    back = types.KeyboardButton('Назад↩️')
    markup_room_name.row(name_1, name_2).row(name_3, name_4).add(back)

    return markup_room_name


def currency_markup():
    markup_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
    rub = types.KeyboardButton('₽')
    eur = types.KeyboardButton('€')
    usd = types.KeyboardButton('$')
    kzt = types.KeyboardButton('₸')
    back = types.KeyboardButton('Назад↩️')
    markup_currency.row(rub, eur, usd, kzt).add(back)

    return markup_currency


def budget_markup():
    markup_budget = types.ReplyKeyboardMarkup(resize_keyboard=True)
    budget_300 = types.KeyboardButton('300')
    budget_500 = types.KeyboardButton('500')
    budget_1000 = types.KeyboardButton('1000')
    budget_1500 = types.KeyboardButton('1500')
    back = types.KeyboardButton('Назад↩️')
    markup_budget.row(budget_300, budget_500).row(budget_1000, budget_1500).add(back)

    return markup_budget


def sending_markup():
    markup_sending = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    post = types.KeyboardButton('Отправка почтой📦')
    ofline = types.KeyboardButton('Встреча лично🙋‍♂️')
    back = types.KeyboardButton('Назад↩️')
    markup_sending.add(post, ofline).add(back)

    return markup_sending


def room_reg_name(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['back_to_manu'], reply_markup=main_markup())
    else:
        char = 6  # количество символов в ключе
        room_key = ''.join(random.choices(string.ascii_letters + string.digits, k=char))
        room_registration[message.chat.id]['roomid'] = room_key  # ключ
        if len(message.text) <= 64:
            room_registration[message.chat.id]['name'] = message.text
            bot.send_message(message.chat.id, text_mess['create_room_cur'],
                             reply_markup=currency_markup())
            bot.register_next_step_handler(message, currency_budget)
        else:
            bot.send_message(message.chat.id, text_mess['create_room_name_error'])
            bot.register_next_step_handler(message, room_reg_name)


def currency_budget(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['create_room_name'],
                         parse_mode='html', reply_markup=room_name_markup())
        bot.register_next_step_handler(message, room_reg_name)
    else:
        room_registration[message.chat.id]['currency'] = message.text
        bot.send_message(message.chat.id, text_mess['create_room_budget'], reply_markup=budget_markup())
        bot.register_next_step_handler(message, room_budget)


def room_budget(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['create_room_cur'],
                         reply_markup=currency_markup())
        bot.register_next_step_handler(message, currency_budget)
    else:
        try:
            budget = float(message.text.replace(',', '.'))
            if budget.is_integer():
                budget = int(budget)
            if budget <= 0:
                raise Exception
            room_registration[message.chat.id]['budget'] = budget
            bot.send_message(message.chat.id, text_mess['create_room_budget_ins'].format(budget))
            bot.send_message(message.chat.id, text_mess['create_room_sending'], parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, room_sending)
        except Exception:
            bot.send_message(message.chat.id, text_mess['create_room_budget_error'], reply_markup=budget_markup())
            bot.register_next_step_handler(message, room_budget)


def room_sending(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['create_room_budget'], reply_markup=budget_markup())
        bot.register_next_step_handler(message, room_budget)
    else:
        if message.text == 'Отправка почтой📦':
            room_registration[message.chat.id]['sending'] = True
            SqlDB.create_new_room(room_registration[message.chat.id]['roomid'],
                                  room_registration[message.chat.id]['name'],
                                  str(room_registration[message.chat.id]['budget']) + ' ' +
                                  room_registration[message.chat.id]['currency'],
                                  room_registration[message.chat.id]['sending'],
                                  None, message.from_user.id)
            bot.send_message(message.chat.id,
                             text_mess['create_room_done'].format(room_registration[message.chat.id]['roomid']),
                             parse_mode='html', reply_markup=main_markup())
        elif message.text == 'Встреча лично🙋‍♂️':
            room_registration[message.chat.id]['sending'] = False
            bot.send_message(message.chat.id, text_mess['create_room_meeting'], parse_mode='html',
                             reply_markup=back_markup())
            bot.register_next_step_handler(message, room_meeting)
        else:
            bot.send_message(message.chat.id, text_mess['dont_understand'])
            bot.send_message(message.chat.id, text_mess['create_room_sending'], parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, room_sending)


def room_meeting(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['create_room_sending'], parse_mode='html', reply_markup=sending_markup())
        bot.register_next_step_handler(message, room_sending)
    else:
        room_registration[message.chat.id]['meeting'] = message.text
        SqlDB.create_new_room(room_registration[message.chat.id]['roomid'],
                              room_registration[message.chat.id]['name'],
                              str(room_registration[message.chat.id]['budget']) + ' ' +
                              room_registration[message.chat.id]['currency'],
                              room_registration[message.chat.id]['sending'],
                              room_registration[message.chat.id]['meeting'], message.from_user.id)
        bot.send_message(message.chat.id,
                         text_mess['create_room_done'].format(room_registration[message.chat.id]['roomid']),
                         parse_mode='html', reply_markup=main_markup())


def enter_room(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['back_to_manu'], reply_markup=main_markup())
    else:
        if not SqlDB.exists_room(message.text):
            bot.send_message(message.chat.id, text_mess['enter_room_doesnt_exists'])
            bot.register_next_step_handler(message, enter_room)
        else:
            if not SqlDB.exists_player_room(message.chat.id, message.text) and not SqlDB.pair(message.text) and SqlDB.player_number(message.text) < 99:
                player[message.chat.id]['roomid'] = message.text
                room_inf[message.chat.id] = SqlDB.room_info(player[message.chat.id]['roomid'])[0]
                room_registration[message.chat.id]["name"] = room_inf[message.chat.id][1]
                room_registration[message.chat.id]["budget"] = room_inf[message.chat.id][2]
                room_registration[message.chat.id]["sending"] = room_inf[message.chat.id][3]
                if SqlDB.player_number(player[message.chat.id]['roomid']) < 9:
                    num = '0' + str(SqlDB.player_number(player[message.chat.id]['roomid']) + 1)
                else:
                    num = str(SqlDB.player_number(player[message.chat.id]['roomid']) + 1)
                player[message.chat.id]['playerid'] = player[message.chat.id]['roomid'] + "_" + num
                SqlDB.add_new_player(player[message.chat.id]['playerid'], message.chat.id, player[message.chat.id]['roomid'])
                bot.send_message(message.chat.id, text_mess['enter_room_name'].format(room_registration[message.chat.id]["name"]), parse_mode='html',
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, player_name)
            elif SqlDB.pair(message.text):
                bot.send_message(message.chat.id, text_mess['enter_room_toss_up'], parse_mode='html',
                                 reply_markup=main_markup())
            elif SqlDB.player_number(message.text) == 99:
                bot.send_message(message.chat.id, text_mess['enter_room_error_num'], parse_mode='html',
                                 reply_markup=main_markup())
            else:
                bot.send_message(message.chat.id, text_mess['enter_room_error'], parse_mode='html',
                                 reply_markup=main_markup())


def player_name(message):
    if len(message.text) <= 64:
        player[message.chat.id]['name'] = message.text
        if room_registration[message.chat.id]["sending"]:
            player[message.chat.id]['post'] = True
            bot.send_message(message.chat.id, text_mess['enter_room_sending'])
            bot.register_next_step_handler(message, player_address)
        else:
            bot.send_message(message.chat.id, text_mess['enter_room_post'], parse_mode='html', reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)
    else:
        bot.send_message(message.chat.id, text_mess['enter_room_name_error'])
        bot.register_next_step_handler(message, player_name)


def player_sending(message):
    if message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text_mess['enter_room_name'], parse_mode='html',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, player_name)
    else:
        if message.text == 'Отправка почтой📦':
            player[message.chat.id]['post'] = True
            bot.send_message(message.chat.id, text_mess['enter_room_sending'], reply_markup=back_markup())
            bot.register_next_step_handler(message, player_address)
        elif message.text == 'Встреча лично🙋‍♂️':
            player[message.chat.id]['post'] = False
            player[message.chat.id]['address'] = None
            SqlDB.add_new_player_update(player[message.chat.id]['playerid'], player[message.chat.id]['name'],
                                        player[message.chat.id]['post'], player[message.chat.id]['address'])
            if not SqlDB.check_wish(message.from_user.id):
                wish[message.chat.id]['check'] = "local"
                bot.send_message(message.chat.id, text_mess['loc_w_new'],
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, wishlist)
            else:
                bot.send_message(message.chat.id, text_mess['enter_room_done'],
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.send_message(message.chat.id, text_mess['loc_w_add'], parse_mode='html',
                                 reply_markup=create_buttons(player[message.chat.id]["playerid"], "local:"))
        else:
            bot.send_message(message.chat.id, text_mess['dont_understand'])
            bot.send_message(message.chat.id, text_mess['enter_room_post'], parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)


def player_address(message):
    if message.text == 'Назад↩️':
        room_info = SqlDB.room_info(player[message.chat.id]['roomid'])
        if room_info[0][3]:
            bot.send_message(message.chat.id, text_mess['enter_room_sending'])
            bot.register_next_step_handler(message, player_address)
        else:
            bot.send_message(message.chat.id, text_mess['enter_room_post'], parse_mode='html',
                             reply_markup=sending_markup())
            bot.register_next_step_handler(message, player_sending)
    else:
        player[message.chat.id]['address'] = message.text
        SqlDB.add_new_player_update(player[message.chat.id]['playerid'], player[message.chat.id]['name'],
                                    player[message.chat.id]['post'], player[message.chat.id]['address'])
        if not SqlDB.check_wish(message.from_user.id):
            wish[message.chat.id]['check'] = "local"
            bot.send_message(message.chat.id, text_mess['loc_w_new'],
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, wishlist)
        else:
            bot.send_message(message.chat.id, text_mess['loc_w_add'].format(room_registration[message.chat.id]["budget"]), parse_mode='html',
                             reply_markup=create_buttons(player[message.chat.id]["playerid"], "local:"))


def wishlist(message):
    wish[message.chat.id]['wish'] = message.text
    markup_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    skip = types.KeyboardButton('Пропустить')
    markup_skip.add(skip)
    bot.send_message(message.chat.id, text_mess['wish_description'], reply_markup=markup_skip)
    bot.register_next_step_handler(message, wish_description)


def wish_description(message):
    if message.text == 'Пропустить':
        wish[message.chat.id]['description'] = ""
    else:
        wish[message.chat.id]['description'] = message.text
    SqlDB.add_new_wish(message.from_user.id, wish[message.chat.id]['wish'], wish[message.chat.id]['description'])
    if wish[message.chat.id]['check'] == "local":
        bot.send_message(message.chat.id, text_mess['loc_w_add'], parse_mode='html',
                         reply_markup=create_buttons(player[message.chat.id]["playerid"], "local:"))
    else:
        markup_wish = types.ReplyKeyboardMarkup(resize_keyboard=True)
        new_wish = types.KeyboardButton('Добавить новый подарок')
        menu = types.KeyboardButton('Вернуться в меню')
        markup_wish.add(new_wish).add(menu)
        bot.send_message(message.chat.id, text_mess['wish_ins'].format(wish[message.chat.id]['wish'],
                                                                       wish[message.chat.id]['description']),
                         reply_markup=markup_wish)
        bot.register_next_step_handler(message, wish_menu)


def wish_menu(message):
    if message.text == 'Добавить новый подарок':
        wish[message.chat.id]['check'] = "global"
        bot.send_message(message.chat.id, text_mess['loc_w_new'])
        bot.register_next_step_handler(message, wishlist)
    elif message.text == 'Вернуться в меню':
        bot.send_message(message.chat.id, text_mess['back_to_manu'],
                         reply_markup=main_markup())


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "back")
def handle_back_button(call):
    if call.data.split(":")[1] == 'wish':
        keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                                callback_data='participant:' + player[call.message.chat.id][
                                                    "playerid"]))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_loc_w'],
                              reply_markup=keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_wl'], reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "delete")
def handle_delete_button(call):
    if call.data.split(":")[1] == "wish":
        SqlDB.delete_local(player[call.message.chat.id]["playerid"], wish_inf[call.message.chat.id]["id"])
        if not SqlDB.presents(player[call.message.chat.id]["playerid"]):
            wish[call.message.chat.id]['check'] = "local"
            if not SqlDB.check_wish(call.message.chat.id):
                bot.send_message(call.message.chat.id,
                                 text_mess['loc_w_new'],
                                 reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.register_next_step_handler(call.message, wishlist)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=text_mess['loc_w_new'],
                                      reply_markup=create_buttons(player[call.message.chat.id]["playerid"], "local:"))
        else:
            keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
            keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data='participant:' + player[call.message.chat.id]["playerid"]))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_mess['user_loc_w'],
                                  reply_markup=keyboard)
    else:
        SqlDB.delete_wish(wish_inf[call.message.chat.id]["id"])
        if not SqlDB.check_wish(call.message.chat.id):
            wish[call.message.chat.id]['check'] = "global"
            bot.send_message(call.message.chat.id, text_mess['empty_wl'],
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(call.message, wishlist)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_mess['user_wl'],
                                  reply_markup=create_buttons(call.message.chat.id, "global:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "add")
def handle_add_button(call):
    wish[call.message.chat.id]['check'] = call.data.split(":")[1]
    if wish[call.message.chat.id]['check'] == "wish":
        keyboard = create_buttons(player[call.message.chat.id]["playerid"], "local:")
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                                callback_data='wishlist'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['loc_w_new'],
                              reply_markup=keyboard)
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text_mess['loc_w_new'],
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
        types.InlineKeyboardButton(text='Назад↩️', callback_data=call.data.split(":")[1] + ':' + str(wish_inf[call.message.chat.id]["id"])))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['edit_select'], reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data in ('present', 'description', 'name_room', 'budget', 'meeting', 'name', 'address', 'post'))
def handle_edit_select(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['edit'])
    if call.data == 'present':
        bot.register_next_step_handler(call.message, wish_update)
    elif call.data == 'description':
        bot.register_next_step_handler(call.message, description_update)
    elif call.data == 'name_room':
        bot.register_next_step_handler(call.message, name_room_update)
    elif call.data == 'budget':
        bot.send_message(call.message.chat.id, text_mess['edit_room_cur'])
        bot.register_next_step_handler(call.message, budget_update)
    elif call.data == 'meeting':
        bot.register_next_step_handler(call.message, meeting_update)
    elif call.data == 'name':
        bot.register_next_step_handler(call.message, name_update)
    elif call.data == 'address':
        bot.register_next_step_handler(call.message, address_update)
    elif call.data == 'post':
        bot.send_message(call.message.chat.id, text_mess['enter_room_post'], reply_markup=sending_markup())
        bot.register_next_step_handler(call.message, post_update)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data.split(":")[0] == "global" or call.data.split(":")[0] == "wish")
def handle_global_button(call):
    wish_inf[call.message.chat.id]["id"] = call.data.split(":")[1]
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Удалить', callback_data='delete:' + call.data.split(":")[0]))
    keyboard.add(types.InlineKeyboardButton(text='Изменить', callback_data='edit:' + call.data.split(":")[0]))
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data='back:' + call.data.split(":")[0]))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['wish'].format(wishlist_data[0][0], wishlist_data[0][1]),
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "local")
def handle_local_button(call):
    wish_inf[call.message.chat.id]["id"] = call.data.split(":")[1]
    SqlDB.add_new_local_wish(player[call.message.chat.id]['playerid'], wish_inf[call.message.chat.id]["id"])
    wishlist_data = SqlDB.select_wish(call.data.split(":")[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Добавить еще подарок', callback_data='add_present'))
    keyboard.add(types.InlineKeyboardButton(text='Завершить', callback_data='quite_registration'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['loc_w_ins'].format(wishlist_data[0][0]), reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "add_present")
def handle_add_present_button(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['loc_w_add_2'], reply_markup=create_buttons(player[call.message.chat.id]["playerid"], "local:"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "quite_registration")
def handle_organizer_button(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, text_mess['enter_room_done_present'], reply_markup=main_markup())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "organizer")
def handle_organizer_button(call):
    room_registration[call.message.chat.id]["id"] = call.data.split(":")[1].split("_")[0]
    room_inf[call.message.chat.id] = SqlDB.room_info(room_registration[call.message.chat.id]["id"])[0]
    room_registration[call.message.chat.id]["name"] = room_inf[call.message.chat.id][1]
    room_registration[call.message.chat.id]["budget"] = room_inf[call.message.chat.id][2]
    if room_inf[call.message.chat.id][3]:
        room_registration[call.message.chat.id]["meeting"] = text_mess['user_room_post']
    else:
        room_registration[call.message.chat.id]["meeting"] = room_inf[call.message.chat.id][4]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Изменить данные', callback_data='edit_room'))
    keyboard.add(types.InlineKeyboardButton(text='Удалить комнату', callback_data='delete_room'))
    if not SqlDB.pair(room_registration[call.message.chat.id]["id"]):
        keyboard.add(types.InlineKeyboardButton(text='Список игроков (Удалить игрока)', callback_data='delete_player'))
    if SqlDB.pair(room_registration[call.message.chat.id]["id"]):
        keyboard.add(types.InlineKeyboardButton(text='Результат жеребьевки', callback_data='toss_up_result:room'))
    elif (SqlDB.player_number(room_registration[call.message.chat.id]["id"]) >= 3 and
          not SqlDB.pair(room_registration[call.message.chat.id]["id"])):
        keyboard.add(types.InlineKeyboardButton(text='Провести жеребьевку', callback_data='toss_up'))
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data='back_room'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['user_room_organizer'].format(room_registration[call.message.chat.id]['id'],
                                                                       room_registration[call.message.chat.id]['name'],
                                                                       room_registration[call.message.chat.id]['budget'],
                                                                       room_registration[call.message.chat.id][
                                                                           'meeting']), parse_mode='html',
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "toss_up")
def handle_toss_up_button(call):
    players = [row[0] for row in SqlDB.room_players(room_registration[call.message.chat.id]["id"])]
    random.shuffle(players)
    pairs = [(players[i], players[(i+1) % len(players)]) for i in range(len(players))]
    for i in range(len(pairs)):
        SqlDB.update_pair(pairs[i][1], pairs[i][0])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=text_mess['toss_up_result'], callback_data='toss_up_result:room'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['toss_up'], reply_markup=keyboard)
    for player_id in SqlDB.room_players(room_registration[call.message.chat.id]["id"]):
        bot.send_message(player_id[2], text_mess['toss_up_notification'].format(room_registration[call.message.chat.id]["name"], room_registration[call.message.chat.id]["name"]),
                         parse_mode='html', reply_markup=main_markup())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "toss_up_result")
def handle_toss_up_button(call):
    if call.data.split(":")[1] == "player":
        player[call.message.chat.id]["pair"] = SqlDB.toss_up_select(player[call.message.chat.id]["playerid"])[0]
        text = f'Вы дарите подарок игроку {player[call.message.chat.id]["pair"][1]}\n'
        if player[call.message.chat.id]["pair"][2]:
            text += f'Адрес для отправки или личной встречи {player[call.message.chat.id]["pair"][3]}\n'
        else:
            text += f'Вы сможете встретиться с игроком лично по адресу: {room_registration[call.message.chat.id]["meeting"]}\n'
        wishlist = [f"{row[0]} ({row[2]})" for row in
                   SqlDB.presents(player[call.message.chat.id]["pair"][0])]
        wish_text = ', '.join(wishlist)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                                callback_data=f'participant:{player[call.message.chat.id]["playerid"]}'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text+"Вишлист: "+wish_text, parse_mode='html',
                              reply_markup=keyboard)
    else:
        players = [f"игрок {row[2]} дарит подарок игроку {row[3]}" for row in SqlDB.toss_up(room_registration[call.message.chat.id]["id"])]
        text = '\n'.join(players)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад',
                                                callback_data=f'organizer:{room_registration[call.message.chat.id]["id"]}'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f'Результат жеребьевки\n\n<tg-spoiler>{text}</tg-spoiler>', parse_mode='html', reply_markup=keyboard)
        bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_room")
def handle_back_room_button(call):
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room'],
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room_error'], parse_mode='html')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "edit_room")
def handle_edit_room_button(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Название комнаты', callback_data='name_room'))
    keyboard.add(types.InlineKeyboardButton(text='Бюджет', callback_data='budget'))
    if not (room_inf[call.message.chat.id][3]):
        keyboard.add(types.InlineKeyboardButton(text='Место встречи', callback_data='meeting'))
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                            callback_data=f'organizer:{room_registration[call.message.chat.id]["id"]}'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['edit_select'],
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete_room")
def handle_delete_room_button(call):
    SqlDB.delete_room(room_registration[call.message.chat.id]["id"])
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room'],
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room_error'], parse_mode='html')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete_player")
def handle_delete_player_button(call):
    if SqlDB.room_players(room_registration[call.message.chat.id]["id"]):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['room_players'],
                              reply_markup=create_players_buttons(room_registration[call.message.chat.id]["id"]))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['room_players_doesnt_exists'],
                              reply_markup=create_players_buttons(room_registration[call.message.chat.id]["id"]))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.split(":")[0] == "player")
def handle_delete_player_button(call):
    SqlDB.delete_player(call.data.split(":")[1])
    if SqlDB.get_user_rooms(call.message.chat.id) or SqlDB.get_org_rooms(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room'],
                              reply_markup=create_rooms_buttons(call.message.chat.id))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_room_error'], parse_mode='html')
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
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Изменить данные', callback_data='edit_player'))
    keyboard.add(types.InlineKeyboardButton(text='Подарки', callback_data='wishlist'))
    if (SqlDB.room_players(room_registration[call.message.chat.id]["id"]) and
            SqlDB.pair(room_registration[call.message.chat.id]["id"])):
        keyboard.add(types.InlineKeyboardButton(text='Результат жеребьевки', callback_data='toss_up_result:player'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='Выйти из комнаты',
                                                callback_data=f'player:{player[call.message.chat.id]["playerid"]}'))
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data='back_room'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['user_room_participant'].format(player[call.message.chat.id]['name'],
                                                                         room_registration[call.message.chat.id]['id'],
                                                                         room_registration[call.message.chat.id]['name'],
                                                                         room_registration[call.message.chat.id]['budget'],
                                                                         room_registration[call.message.chat.id]['meeting']
                                                                         ),
                          parse_mode='html', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "wishlist")
def handle_wishlist_button(call):
    if not SqlDB.presents(player[call.message.chat.id]["playerid"]):
        wish[call.message.chat.id]['check'] = "local"
        if not SqlDB.check_wish(call.message.chat.id):
            bot.send_message(call.message.chat.id,
                             text_mess['loc_w_new'], reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(call.message, wishlist)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_mess['loc_w_new'],
                                  reply_markup=create_buttons(player[call.message.chat.id]["playerid"], "local:"))
    else:
        keyboard = create_buttons(player[call.message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️', callback_data='participant:' + player[call.message.chat.id]["playerid"]))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text_mess['user_loc_w'],
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
    keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                            callback_data=f'participant:{player[call.message.chat.id]["playerid"]}'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text_mess['edit_select'],
                          reply_markup=keyboard)
    bot.answer_callback_query(call.id)


def wish_update(message):
    SqlDB.edit_wish(wish_inf[message.chat.id]["id"], "wish", message.text)
    bot.send_message(message.chat.id, text_mess['edit_done'])
    if wish[message.chat.id]['check'] == "wish":
        keyboard = create_buttons(player[message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                                callback_data='participant:' + player[message.chat.id]["playerid"]))
        bot.send_message(message.chat.id, text_mess['user_loc_w'], reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, text_mess['user_wl'], reply_markup=create_buttons(message.from_user.id, "global:"))


def description_update(message):
    SqlDB.edit_wish(wish_inf[message.chat.id]["id"], "description", message.text)
    bot.send_message(message.chat.id, text_mess['edit_done'])
    if wish[message.chat.id]['check'] == "wish":
        keyboard = create_buttons(player[message.chat.id]["playerid"], "wish:")
        keyboard.add(types.InlineKeyboardButton(text='Назад↩️',
                                                callback_data='participant:' + player[message.chat.id]["playerid"]))
        bot.send_message(message.chat.id, text_mess['user_loc_w'], reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id,  text_mess['user_wl'], reply_markup=create_buttons(message.from_user.id,
                                                                                             "global:"))


def name_room_update(message):
    if len(message.text) <= 64:
        SqlDB.edit("room",  "name", "roomid", room_registration[message.chat.id]["id"], message.text)
        bot.send_message(message.chat.id, text_mess['edit_done'])
        bot.send_message(message.chat.id, text=text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, text_mess['create_room_name_error'])
        bot.register_next_step_handler(message, room_reg_name)


def name_update(message):
    if len(message.text) <= 64:
        SqlDB.edit("player",  "name", "playerid", player[message.chat.id]["playerid"], message.text)
        bot.send_message(message.chat.id, text_mess['edit_done'])
        bot.send_message(message.chat.id, text=text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, text_mess['enter_room_name_error'])
        bot.register_next_step_handler(message, room_reg_name)


def address_update(message):
    SqlDB.edit("player", "address", "playerid", player[message.chat.id]["playerid"], message.text)
    bot.send_message(message.chat.id,  text_mess['edit_done'])
    bot.send_message(message.chat.id, text=text_mess['user_room'],
                     reply_markup=create_rooms_buttons(message.chat.id))


def post_update(message):
    if message.text == 'Отправка почтой📦':
        player[message.chat.id]['post'] = True
        SqlDB.edit("player", "post", "playerid", player[message.chat.id]["playerid"],
                   player[message.chat.id]['post'])
        bot.send_message(message.chat.id, text_mess['enter_room_sending'])
        bot.register_next_step_handler(message, address_update)
    elif message.text == 'Встреча лично🙋‍♂':
        player[message.chat.id]['post'] = False
        SqlDB.edit("player", "address", "playerid", player[message.chat.id]["playerid"], None)
        SqlDB.edit("player", "post", "playerid", player[message.chat.id]["playerid"],
                   player[message.chat.id]['post'])
        bot.send_message(message.chat.id, text_mess['edit_done'])
        bot.send_message(message.chat.id, text=text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    elif message.text == 'Назад↩️':
        bot.send_message(message.chat.id, text=text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    else:
        bot.send_message(message.chat.id, text_mess['enter_room_post'], parse_mode='html',
                         reply_markup=sending_markup())
        bot.register_next_step_handler(message, post_update)


def budget_update(message):
    val[message.chat.id]['cur'] = message.text
    bot.send_message(message.chat.id, text_mess['edit_room_bud'])
    bot.register_next_step_handler(message, budget_amount_update)


def budget_amount_update(message):
    try:
        val[message.chat.id]['amount'] = float(message.text.replace(',', '.'))
        if val[message.chat.id]['amount'].is_integer():
            val[message.chat.id]['amount'] = int(val[message.chat.id]['amount'])
        if val[message.chat.id]['amount'] <= 0:
            raise Exception
        SqlDB.edit("room", "budget", "roomid", room_registration[message.chat.id]["id"],
                        str(val[message.chat.id]['amount']) + ' ' + val[message.chat.id]['cur'])
        bot.send_message(message.chat.id, text_mess['edit_done'])
        bot.send_message(message.chat.id, text=text_mess['user_room'],
                         reply_markup=create_rooms_buttons(message.chat.id))
    except Exception:
        bot.send_message(message.chat.id, text_mess['create_room_budget_error'])
        bot.register_next_step_handler(message, budget_amount_update)


def meeting_update(message):
    SqlDB.edit("room", "meeting", "roomid", room_registration[message.chat.id]["id"], message.text)
    bot.send_message(message.chat.id, text_mess['edit_done'])
    bot.send_message(message.chat.id, text=text_mess['user_room'],
                     reply_markup=create_rooms_buttons(message.chat.id))


bot.set_my_commands([
    types.BotCommand("/start", "Перезапуск бота"),
    types.BotCommand("/help", "Помощь"),
    types.BotCommand("/rules", "Правила игры"),
    types.BotCommand("/advice", "Обучение")
])
bot.infinity_polling()
