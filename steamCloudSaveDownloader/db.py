import sqlite3
import os
import datetime
from . import err
from .err import err_enum
import logging

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

TABLE REQUESTS
id (INT) PK NOT NULL DEFAULT 0
time (datetime)
count (int)
## Enforce single row


'''
logger = logging.getLogger('scsd')
class db:
    requests_limit = 85000
    def __init__(self, db_location:str, rotation:int):
        self.location = db_location
        self.rotation = rotation
        self.db_file = os.path.join(db_location, DB_FILENAME)

        self.con = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)

        if not self.schema_ok():
            self.initialize_schema()

    def __del__(self):
        if hasattr(self, 'con'):
            self.con.close()

    def commit(self):
        self.con.commit()

    def schema_ok(self) -> bool:
        cur = self.con.cursor()
        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='GAMES';")
        if res.fetchone() is None:
            return False

        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FILES';")
        if res.fetchone() is None:
            return False

        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='REQUESTS';")
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

        res = cur.execute(
            "CREATE TABLE REQUESTS("
            "  id INTEGER PRIMARY KEY CHECK (id = 0),"
            "  time timestamp,"
            "  num int DEFAULT 0"
            ");")

        res = cur.execute("INSERT INTO REQUESTS VALUES (?, ?, 0);", (0, datetime.datetime.now()))

        self.con.commit()

        if not self.schema_ok():
            raise err.err(err_enum.CANNOT_INITIALIZE_DB)

    def add_requests_count(self, count:int):
        cur = self.con.cursor()
        res = cur.execute("SELECT time FROM REQUESTS WHERE id = 0;");
        db_time = res.fetchone()[0]

        now = datetime.datetime.now()
        if (db_time.date() == now.date()):
            res = cur.execute("UPDATE REQUESTS SET num = num + ? WHERE id = 0;", (count,))
        else:
            res = cur.execute("UPDATE REQUESTS SET num = ?, time = ? WHERE id = 0;", (count, now))
        self.con.commit()

    def is_requests_limit_exceed(self) -> bool:
        cur = self.con.cursor()
        res = cur.execute("SELECT num FROM REQUESTS WHERE id = 0;")

        count = res.fetchone()[0]

        return count >= db.requests_limit

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

    def get_file_id(self, app_id:int, path:str, filename:str) -> int:
        cur = self.con.cursor()
        res = cur.execute("SELECT file_id FROM FILES WHERE app_id=? AND path=? AND filename=?;", (app_id, path, filename))
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

            no_tz_time = tup[3].replace(tzinfo=None)
            res = cur.execute("INSERT INTO VERSION VALUES (NULL, ?, ?, ?);", (file_id, no_tz_time, 0))

        self.con.commit()

    def is_file_outdated(self, file_id:int, server_time:datetime) -> tuple:
        cur = self.con.cursor()
        res = cur.execute("SELECT time FROM VERSION WHERE file_id = ? and version_num = 0;", (file_id,))
        db_time_tuple = res.fetchone()
        if db_time_tuple is None:
            logger.warning(f'Failed to retrieve newest version time for file_id {file_id}')
            return (True, None)

        tz_db_time = db_time_tuple[0].replace(tzinfo=datetime.timezone.utc)

        logger.debug(f'DB time: {tz_db_time}, Server time: {server_time}')

        if tz_db_time < server_time:
            return (True, tz_db_time)
        else:
            return (False, tz_db_time)

    # +1 for each version
    # Insert 0 as now
    # Return max version
    def update_file_update_time_to_now(self, file_id:int, newest_file_time: datetime.datetime) -> int:
        cur = self.con.cursor()

        # Increment one for all
        res = cur.execute("UPDATE VERSION SET version_num = version_num + 1 WHERE file_id = ?;", (file_id,))

        time_without_tz = newest_file_time.replace(tzinfo=None)
        # Insert newest as 0
        res = cur.execute("INSERT INTO VERSION VALUES (NULL, ?, ?, 0)", (file_id, time_without_tz))
        self.con.commit()

        res = cur.execute("SELECT COUNT(*) FROM VERSION WHERE file_id = ?", (file_id,))
        count = res.fetchone();

        if (count is None):
            return 0
        else:
            return count[0]

    def remove_outdated_file(self, file_id:int):
        cur = self.con.cursor()
        res = cur.execute("SELECT version_num FROM VERSION WHERE file_id = ? AND version_num >= ?", (file_id, self.rotation))
        outdated_version_num = res.fetchall();

        res = cur.execute("DELETE FROM VERSION WHERE file_id = ? AND version_num >= ?", (file_id, self.rotation))

        self.con.commit()

        logger.debug(f"DB Removing version {outdated_version_num}")

        return outdated_version_num
