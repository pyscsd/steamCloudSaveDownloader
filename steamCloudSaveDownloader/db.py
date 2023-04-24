import sqlite3
import os
import datetime
from . import err
from .err import err_enum

DB_FILENAME = 'scsd.sqlite3'

'''Schema
TABLE GAMES
app_id (integer) PK, CONSTRAINT >0
game_name (text)

TABLE FILES
file_id (INT) PK
filename (chr)
app_id (INT)
last_update (datetime)
'''

class db:
    def __init__(self, db_location:str):
        self.location = db_location
        self.db_file = os.path.join(db_location, DB_FILENAME)

        self.con = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)

        if not self.schema_ok():
            self.initialize_schema()

    def __del__(self):
        self.con.close()

    def schema_ok(self) -> bool:
        cur = self.con.cursor()
        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='GAMES';")
        if res.fetchone() is None:
            return False

        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FILES';")
        if res.fetchone() is None:
            return False

        return True

    def initialize_schema(self):
        cur = self.con.cursor()
        res = cur.execute(
            "CREATE TABLE GAMES("
            "  app_id INTEGER CHECK (app_id>0),"
            "  game_name text,"
            "  PRIMARY KEY (app_id)"
            ");")

        res = cur.execute(
            "CREATE TABLE FILES("
            "  file_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  filename TEXT,"
            "  app_id INTEGER,"
            "  last_update timestamp,"
            "  FOREIGN KEY (app_id) REFERENCES GAMES(app_id)"
            ");")

        if not self.schema_ok():
            raise err.err(err_enum.CANNOT_INITIALIZE_DB)

    def add_new_game(self, app_id:int, game_name:str):
        cur = self.con.cursor()
        res = cur.execute("INSERT INTO GAMES VALUES (?, ?);", (app_id, game_name))
        self.con.commit()

    def is_game_exist(self, app_id:int):
        cur = self.con.cursor()
        res = cur.execute("SELECT app_id FROM GAMES WHERE app_id = ?;", (app_id,))
        return res.fetchone() is not None

    def get_game_files(self, app_id: int):
        pass

    # Expect [(filename, app_id, last_update_time), ...]
    def add_new_files(self, file_tuples:list):
        cur = self.con.cursor()
        res = cur.executemany("INSERT INTO FILES VALUES (NULL, ?, ?, ?);", file_tuples)
        self.con.commit()

    def is_file_outdated(self, app_id:int, filename:str, time:datetime) -> bool:
        cur = self.con.cursor()
        now = datetime.datetime.now()
        res = cur.execute("SELECT last_update FROM FILES WHERE app_id = ? AND filename = ?;", (app_id, filename))
        time_tuple = res.fetchone()
        if time_tuple is None:
            return True

        print(time_tuple[0])
        print(time)
        if time_tuple[0] < time:
            return True
        else:
            return False

    def update_file_update_time_to_now(self, app_id:int, filename:str):
        cur = self.con.cursor()
        now = datetime.datetime.now()
        now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute)
        res = cur.execute("UPDATE FILES SET last_update = ? WHERE app_id = ? AND filename = ?;", (now, app_id, filename))
        self.con.commit()
