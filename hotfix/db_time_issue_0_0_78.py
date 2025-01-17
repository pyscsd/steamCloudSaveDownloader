import sqlite3
import sys
import os

res = input("Please make sure to backup your Game Files and DB(scsd.sqlite3) before proceed (y/N)")

if res.lower() != 'y':
    sys.exit(1)

res = input("Please input scsd.sqlite3 location (e.g. ./scsd.sqlite3), (/data/scsd.sqlite3)")

if not os.path.isfile(res):
    print("DB file not exist")
    sys.exit(1)

con = sqlite3.connect(res, detect_types=sqlite3.PARSE_DECLTYPES)
cur = con.cursor()
db_res = cur.execute("UPDATE VERSION SET time = '2024-12-30 00:00:00' WHERE time >= date('now')")
con.commit()
print("Done")