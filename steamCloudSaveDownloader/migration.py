import logging
import datetime
import shutil
from zoneinfo import ZoneInfo
from . import db

logger = logging.getLogger('scsd')

class DatabaseMigrator:
    def __init__(self, db_):
        self.db_ = db_

    def backup_db(self, current_version: int = None):
        if current_version is None:
            current_version = self.db_.get_db_version()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_.db_file}.v{current_version}.{timestamp}.bak"

        logger.info(f"Backing up database to {backup_path}...")
        self.db_.commit()
        shutil.copy2(self.db_.db_file, backup_path)
        return backup_path

    def run(self):
        current_version = self.db_.get_db_version()
        target_version = db.db.LATEST_DB_VERSION

        if current_version == target_version:
            logger.info("Database is already up to date.")
            return

        logger.info(f"Migrating from database version {current_version} to {target_version}...")
        self.backup_db(current_version)

        if current_version == 0:
            logger.info("Migrating v0 to v1: Correcting legacy Pacific Time timestamps to true UTC...")
            self._migrate_v0_to_v1()
            self.db_.set_db_version(1)
            current_version = 1
            logger.info("Migration to v1 complete.")
        else:
            logger.error(f"Cannot migrate from unknown database version {current_version}.")

    def _migrate_v0_to_v1(self):
        cur = self.db_.con.cursor()
        res = cur.execute("SELECT file_id, version_num, time FROM VERSION;")
        rows = res.fetchall()

        steam_tz = ZoneInfo("America/Los_Angeles")

        for file_id, version_num, legacy_time in rows:
            if legacy_time is None:
                continue

            if isinstance(legacy_time, str):
                try:
                    legacy_time = datetime.datetime.fromisoformat(legacy_time)
                except ValueError:
                    legacy_time = datetime.datetime.strptime(legacy_time.split(".")[0], "%Y-%m-%d %H:%M:%S")

            if legacy_time.tzinfo is None:
                utc_time = legacy_time.replace(tzinfo=steam_tz).astimezone(datetime.timezone.utc)
            else:
                utc_time = legacy_time.astimezone(datetime.timezone.utc)

            # Standardize as naive UTC to match how scsd natively inserts new files
            naive_utc_time = utc_time.replace(tzinfo=None)

            cur.execute(
                "UPDATE VERSION SET time = ? WHERE file_id = ? AND version_num = ?",
                (naive_utc_time, file_id, version_num)
            )
        self.db_.con.commit()
