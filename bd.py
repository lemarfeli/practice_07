from psycopg2 import *

class SqlDB:
    #соединение с бд
    def __init__(self):
        try:
            self.connection = connect(dbname='santa_bot_db', user='postgres',
                                    password='Gt83Kew0', host='localhost')
            print("Подключение к PostgreSQL успешно выполнено")
            self.cursor = self.connection.cursor()
        except Error as connection_error:
            print("Возникла ошибка: ", connection_error)

    # проверка на существование пользователя в бд
    def exists_user(self, userid):
        self.cursor.execute("SELECT COUNT(*) FROM tguser WHERE userid = %s", (userid,))
        res = int(self.cursor.fetchone()[0])
        return res > 0

    # добавление пользователя
    def add_new_user(self, userid):
        self.cursor.execute("INSERT INTO tguser VALUES (%s)", (userid,))
        return self.connection.commit()

    # проверка на существование подарокв в гл више
    def check_wish(self, userid):
        self.cursor.execute("SELECT COUNT(*) FROM globalwishlist WHERE userid = %s", (userid,))
        user_data = int(self.cursor.fetchone()[0])
        return user_data > 0

    # выборка всех подарков пользователя из гл виша
    def select_wishlist(self, userid):
        self.cursor.execute("SELECT wish, gwid FROM globalwishlist WHERE userid = %s", (userid,))
        res = self.cursor.fetchall()
        return res

    # выборка локального вишлиста
    def select_local_wishlist(self, userid):
        self.cursor.execute("SELECT wish, gwid  FROM globalwishlist WHERE userid = (SELECT userid  FROM player WHERE playerid = %s) EXCEPT SELECT globalwishlist.wish, localwishlist.gwid FROM localwishlist JOIN globalwishlist ON globalwishlist.gwid = localwishlist.gwid WHERE localwishlist.playerid = %s ", (userid, userid))
        res = self.cursor.fetchall()
        return res
        
    # выборка данных определенного подарка из гл виша
    def select_wish(self, gwid ):
        self.cursor.execute("SELECT wish, description  FROM globalwishlist WHERE gwid = %s", (gwid,))
        res = self.cursor.fetchall()
        return res
        
    # выборка всех подарков игрока из лок виша
    def presents(self, playerid):
        self.cursor.execute("SELECT globalwishlist.wish, localwishlist.gwid, globalwishlist.description FROM localwishlist JOIN globalwishlist ON globalwishlist.gwid = localwishlist.gwid WHERE localwishlist.playerid = %s", (playerid,))
        res = self.cursor.fetchall()
        return res
        
    # удаление позиции из гл виша
    def delete_wish(self, gwid ):
        self.cursor.execute("DELETE FROM globalwishlist WHERE gwid = %s", (gwid,))
        return self.connection.commit()

    # удаление позиции из лок виша
    def delete_local(self, playerid, gwid):
        self.cursor.execute("DELETE FROM localwishlist WHERE playerid = %s AND gwid = %s", (playerid, gwid,))
        return self.connection.commit()
        
    # изменение выбранного поля (select) подарка в гл више по коду подарка
    def edit_wish(self, gwid, select, item):
        self.cursor.execute(f"UPDATE globalwishlist SET {select} = %s WHERE gwid = %s", (item, gwid,))
        return self.connection.commit()
        
    # добавление нового подарка в гл виш
    def add_new_wish(self, userid, wish, description):
        self.cursor.execute("INSERT INTO globalwishlist (userid, wish, description)  VALUES (%s, %s, %s)", (userid, wish, description,))
        return self.connection.commit()

    # добавление нового подарка в лок виш
    def add_new_local_wish(self, playerid, gwid):
        self.cursor.execute("INSERT INTO localwishlist (playerid, gwid)  VALUES (%s, %s)",
                            (playerid, gwid,))
        return self.connection.commit()

    # добавление игрока
    def add_new_player(self, playerid, userid, roomid):
        self.cursor.execute("INSERT INTO player (playerid, userid, roomid) VALUES (%s, %s, %s)",
                            (playerid, userid, roomid))
        return self.connection.commit()

    def add_new_player_update(self, playerid, name, post, address):
        self.cursor.execute("UPDATE player SET name = %s, post = %s, address = %s WHERE playerid = %s",
                            (name, post, address, playerid, ))
        return self.connection.commit()

    # данные об игроке
    def player_info(self, playerid):
        self.cursor.execute("SELECT * FROM player WHERE playerid = %s", (playerid,))
        res = self.cursor.fetchall()
        return res

    # проверка на существование комнаты в бд
    def exists_room(self, roomid):
        self.cursor.execute("SELECT COUNT(*) FROM room WHERE roomid = %s", (roomid,))
        res = int(self.cursor.fetchone()[0])
        return res > 0

    # проверка на существование игрока в комнате
    def exists_player_room(self, userid, roomid):
        self.cursor.execute("SELECT COUNT(*) FROM player WHERE userid = %s AND roomid = %s", (userid, roomid,))
        res = int(self.cursor.fetchone()[0])
        return res > 0

    # подсчет количества игроков в комнате
    def player_number(self, roomid):
        self.cursor.execute("SELECT COUNT(*) FROM player WHERE roomid = %s", (roomid,))
        res = int(self.cursor.fetchone()[0])
        return res
        
    # создание комнаты
    def create_new_room(self, roomid, name, anonymity, budget, sending, meeting, organizer):
        self.cursor.execute("INSERT INTO room VALUES (%s, %s, %s, %s, %s, %s, %s)", (roomid, name, anonymity, budget, sending, meeting, organizer,))
        return self.connection.commit()

    # данные о комнате
    def room_info(self, roomid):
        self.cursor.execute("SELECT * FROM room WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        return res
        
    # изменение полей в выбранных таблице и поле по указанному полю и параметру
    def edit(self, table_name, select, field, item_id, item):
        self.cursor.execute(f"UPDATE {table_name} SET {select} = %s WHERE {field} = %s", (item, item_id,))
        return self.connection.commit()

    #удаление комнаты
    def delete_room(self, roomid):
        self.cursor.execute("DELETE FROM room WHERE roomid = %s", (roomid,))
        return self.connection.commit()

    # удаление игрока из комнаты
    def delete_player(self, playerid):
        self.cursor.execute("DELETE FROM player WHERE playerid = %s", (playerid,))
        return self.connection.commit()
        
    # все игроки комнаты
    def room_players(self, roomid):
        self.cursor.execute("SELECT playerid, name, userid FROM player WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        return res
        
    # жеребьевка
    def toss_up(self, roomid):
        self.cursor.execute("SELECT p2.playerid, p2.pair, p2.name, p1.name FROM player p1 JOIN player p2 ON p1.playerid = p2.pair  WHERE p2.roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        return res

    # проверка на существование пар у игроков в выбранной комнате
    def pair(self, roomid):
        self.cursor.execute("SELECT COUNT(pair) FROM player WHERE roomid = %s", (roomid,))
        res = int(self.cursor.fetchone()[0])
        return res > 0

    # обновление данных о паре игрока в комнате
    def update_pair(self, playerid, pair):
        self.cursor.execute(f"UPDATE player SET pair = %s WHERE playerid = %s", (pair, playerid,))
        return self.connection.commit()

    # кому дарит игрок
    def toss_up_select(self, playerid):
        self.cursor.execute("SELECT p2.pair, p1.name, p1.post, p1.address FROM player p1 JOIN player p2 ON p1.playerid = p2.pair  WHERE p2.playerid = %s", (playerid,))
        res = self.cursor.fetchall()
        return res
    # выведение всех комнат пользователя в качестве игрока
    def get_user_rooms(self, userid):
        self.cursor.execute(
            "SELECT room.roomid, room.name, player.playerid FROM room JOIN player ON room.roomid = player.roomid WHERE player.userid = %s",
            (userid,))
        res = self.cursor.fetchall()
        return res

    # выведение всех комнат пользователя в качестве организатора
    def get_org_rooms(self, userid):
        self.cursor.execute(
            "SELECT room.roomid, room.name, room.organizer FROM room WHERE room.organizer = %s",
            (userid,))
        res = self.cursor.fetchall()
        return res

    # прекратить соединение с бд
    def quiet(self):
        self.connection.close()
