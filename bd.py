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
        res = self.cursor.fetchone()[0]
        return res > 0

    # добавление пользователя
    def add_new_user(self, userid):
        self.cursor.execute("INSERT INTO tguser VALUES (%s)", (userid,))
        return self.connection.commit()

    def check_wish(self, userid):
        self.cursor.execute("SELECT COUNT(*) FROM globalwishlist WHERE userid = %s", (userid,))
        user_data = self.cursor.fetchone()[0]
        return user_data > 0

    def select_wishlist(self, userid):
        self.cursor.execute("SELECT * FROM globalwishlist WHERE userid = %s", (userid,))
        res = self.cursor.fetchall()
        return res
    def select_wish(self, gwid ):
        self.cursor.execute("SELECT wish, description  FROM globalwishlist WHERE gwid = %s", (gwid,))
        res = self.cursor.fetchall()
        return res
    def delete_wish(self, gwid ):
        self.cursor.execute("DELETE FROM globalwishlist WHERE gwid = %s", (gwid,))
        return self.connection.commit()
    def edit_wish(self, gwid, select, item):
        self.cursor.execute(f"UPDATE globalwishlist SET {select} = %s WHERE gwid = %s", (item, gwid,))
        return self.connection.commit()
    def add_new_wish(self, userid, wish, description):
        self.cursor.execute("INSERT INTO globalwishlist (userid, wish, description)  VALUES (%s, %s, %s)", (userid, wish, description,))
        return self.connection.commit()

    # добавление игрока
    def add_new_player(self, playerid, userid, roomid, name, wishlist, address, pair):
        self.cursor.execute("INSERT INTO player VALUES (%s, %s, %s, %s, %s, %s, %s)", (playerid, userid, roomid, name, wishlist, address, pair,))
        return self.connection.commit()

    # данные об игроке
    def player_info(self, userid, roomid):
        self.cursor.execute("SELECT * FROM player WHERE userid = %s AND roomid = %s",(userid, roomid,))
        res = self.cursor.fetchall()
        return res

    # проверка на существование комнаты в бд
    def exists_room(self, roomid):
        self.cursor.execute("SELECT COUNT(*) FROM room WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchone()[0]
        return res > 0

    # создание комнаты
    def create_new_room(self, roomid, name, anonymity, budget, sending, meeting, organizer):
        self.cursor.execute("INSERT INTO room VALUES (%s, %s, %s, %s, %s, %s, %s)", (roomid, name, anonymity, budget, sending, meeting, organizer,))
        return self.connection.commit()

    # данные о комнате
    def room_info(self, roomid):
        self.cursor.execute("SELECT * FROM room WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        return res

    # все игроки комнаты
    def room_players(self, roomid):
        self.cursor.execute("SELECT * FROM room WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        result = []
        for row in res:
            result.append(row)
        return result

    # жеребьевка
    def toss_up(self, roomid):
        self.cursor.execute("SELECT playerid, pair FROM player WHERE roomid = %s", (roomid,))
        res = self.cursor.fetchall()
        result = []
        for row in res:
            result.append(row)
        return result

    # кому дарит игрок
    def toss_up_select(self, roomid, userid):
        self.cursor.execute("SELECT pair FROM player WHERE roomid = %s AND userid = %s", (roomid, userid,))
        res = self.cursor.fetchall()
        return res

    # прекратить соединение с бд
    def quiet(self):
        self.connection.close()
