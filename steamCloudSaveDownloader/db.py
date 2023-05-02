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
dir_name (text)

TABLE FILES
file_id (INT) PK
filename (TEXT)
path (TEXT)
app_id (INT)

TABLE VERSION
version_id (INT) PK AUTOINC
file_id foreign key
time (datetime)
version_num (INT) >= 0

'''

class db:
    def __init__(self, db_location:str, rotation:int):
        self.location = db_location
        self.rotation = rotation
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

        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='VERSION';")
        if res.fetchone() is None:
            return False

        return True

    def initialize_schema(self):
        cur = self.con.cursor()
        res = cur.execute(
            "CREATE TABLE GAMES("
            "  app_id INTEGER CHECK (app_id>0),"
            "  game_name text,"
            "  dir_name text,"
            "  PRIMARY KEY (app_id)"
            ");")

        res = cur.execute(
            "CREATE TABLE FILES("
            "  file_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  filename TEXT,"
            "  path TEXT,"
            "  app_id INTEGER,"
            "  FOREIGN KEY (app_id) REFERENCES GAMES(app_id)"
            ");")

        res = cur.execute(
            "CREATE TABLE VERSION("
            "  version_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  file_id INTEGER,"
            "  time timestamp,"
            "  version_num INTEGER CHECK (version_num>=0),"
            "  FOREIGN KEY (file_id) REFERENCES FILES(file_id)"
            ");")

        if not self.schema_ok():
            raise err.err(err_enum.CANNOT_INITIALIZE_DB)

    def add_new_game(self, app_id:int, game_name:str):
        cur = self.con.cursor()
        res = cur.execute("INSERT INTO GAMES VALUES (?, ?, NULL);", (app_id, game_name))
        self.con.commit()

    def set_game_dir(self, app_id:int, dir_name:str):
        cur = self.con.cursor()
        res = cur.execute("UPDATE GAMES SET dir_name = ? WHERE app_id = ?;", (dir_name, app_id))
        self.con.commit()

    def get_game_dir(self, app_id:int) -> str:
        cur = self.con.cursor()
        res = cur.execute("SELECT dir_name FROM GAMES WHERE app_id = ?;", (app_id,))
        game_dir_tuple = res.fetchone()

        if game_dir_tuple is None:
            return None

        return game_dir_tuple[0]

    def get_file_id(self, app_id:int, filename:str) -> int:
        cur = self.con.cursor()
        res = cur.execute("SELECT file_id FROM FILES WHERE app_id=? AND filename=?;", (app_id, filename))
        file_id_tuple = res.fetchone()
        if file_id_tuple is None:
            return None
        return file_id_tuple[0]

    def is_game_exist(self, app_id:int):
        cur = self.con.cursor()
        res = cur.execute("SELECT app_id FROM GAMES WHERE app_id = ?;", (app_id,))
        return res.fetchone() is not None

    def get_game_files(self, app_id: int):
        pass

    # Expect [(filename, path, app_id, last_update_time), ...]
    def add_new_files(self, file_tuples:list):
        cur = self.con.cursor()
        for tup in file_tuples:
            res = cur.execute("INSERT INTO FILES VALUES (NULL, ?, ?, ?);", tup[0:3])
            file_id = cur.lastrowid

            res = cur.execute("INSERT INTO VERSION VALUES (NULL, ?, ?, ?);", (file_id, tup[3], 0))

        self.con.commit()

    def is_file_outdated(self, file_id:int, time:datetime) -> bool:
        cur = self.con.cursor()
        res = cur.execute("SELECT time FROM VERSION WHERE file_id = ? and version_num = 0;", (file_id,))
        time_tuple = res.fetchone()
        if time_tuple is None:
            return True

        if time_tuple[0] < time:
            return True
        else:
            return False

    # +1 for each version
    # Insert 0 as now
    # Return max version
    def update_file_update_time_to_now(self, file_id:int) -> int:
        cur = self.con.cursor()
        now = datetime.datetime.now()
        now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute)

        # Increment one for all
        res = cur.execute("UPDATE VERSION SET version_num = version_num + 1 WHERE file_id = ?;", (file_id,))

        # Insert newest as 0
        res = cur.execute("INSERT INTO VERSION VALUES (NULL, ?, ?, 0)", (file_id, now))
        self.con.commit()

        res = cur.execute("SELECT COUNT(*) FROM VERSION WHERE file_id = ?", (file_id,))
        count = res.fetchone();

        if (count is None):
            return 0
        else:
            return count[0]

    # TODO Rotation
    def get_outdated_file(file_id:int):
        res = cur.execute("SELECT version_id FROM WHERE file_id = ? AND version_num >= ?", (file_id, self.rotation))

