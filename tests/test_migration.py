import datetime
import os
import pytest
import sqlite3
from zoneinfo import ZoneInfo
from steamCloudSaveDownloader import db
from steamCloudSaveDownloader.migration import DatabaseMigrator
from steamCloudSaveDownloader.__main__ import setup_logger

@pytest.fixture(autouse=True)
def init_logger():
    setup_logger()


class TestMigration:
    def test_migration_v0_to_v1(self, tmp_path):
        db_location = str(tmp_path)
        # 1. Create a sqlite file with db.py
        db_ = db.db(db_location=db_location, rotation=5)
        db_file = os.path.join(db_location, db.DB_FILENAME)

        # Simulate a pre-migration database (version 0)
        db_.set_db_version(0)
        assert db_.get_db_version() == 0

        # Create rows before migration (timestamps representing Pacific Time)
        db_.add_new_game(1001, "Test Game")

        # Summer time (PDT: UTC-7) -> 2023-07-15 14:30:00 PDT should convert to 21:30:00 UTC
        # Winter time (PST: UTC-8) -> 2023-01-15 10:15:00 PST should convert to 18:15:00 UTC
        pdt_time = datetime.datetime(2023, 7, 15, 14, 30, 0)
        pst_time = datetime.datetime(2023, 1, 15, 10, 15, 0)

        payload = [
            ("file_pdt.sav", "./save", 1001, pdt_time),
            ("file_pst.sav", "./save", 1001, pst_time),
        ]
        db_.add_new_files(payload)

        # Add an older version for file_pdt
        older_pdt_time = datetime.datetime(2023, 7, 14, 12, 0, 0)
        db_.update_file_update_time_to_now(1, older_pdt_time)

        assert len(list(tmp_path.glob(f"{db.DB_FILENAME}.v0.*.bak"))) == 0

        # 2. Perform migration
        migrator = DatabaseMigrator(db_)
        migrator.run()

        # Check that backup file was created
        assert len(list(tmp_path.glob(f"{db.DB_FILENAME}.v0.*.bak"))) == 1

        # Check DB version is now updated to 1
        assert db_.get_db_version() == 1

        # Check query results after migration are converted to expected UTC
        cur = db_.con.cursor()

        # file_pdt (file_id 1):
        # version 0 (newest, older_pdt_time: 12:00 PDT -> 19:00 UTC)
        # version 1 (previous, pdt_time: 14:30 PDT -> 21:30 UTC)
        res = cur.execute(
            "SELECT version_num, time FROM VERSION WHERE file_id = 1 ORDER BY version_num ASC;"
        ).fetchall()
        assert len(res) == 2
        assert res[0][0] == 0
        assert res[0][1] == datetime.datetime(2023, 7, 14, 19, 0, 0)
        assert res[1][0] == 1
        assert res[1][1] == datetime.datetime(2023, 7, 15, 21, 30, 0)

        # file_pst (file_id 2):
        # version 0 (pst_time: 10:15 PST -> 18:15 UTC)
        res = cur.execute(
            "SELECT version_num, time FROM VERSION WHERE file_id = 2;"
        ).fetchall()
        assert len(res) == 1
        assert res[0][0] == 0
        assert res[0][1] == datetime.datetime(2023, 1, 15, 18, 15, 0)

        # Verify idempotency: running migration again does nothing and keeps version at 1
        migrator.run()
        assert db_.get_db_version() == 1

    def test_unmigrated_db_raises_error_in_main(self, tmp_path):
        from steamCloudSaveDownloader.__main__ import main
        from steamCloudSaveDownloader import err
        from steamCloudSaveDownloader.notifier import notifier

        db_ = db.db(db_location=str(tmp_path), rotation=5)
        db_.set_db_version(0)

        parsed_args = {
            'General': {'save_dir': str(tmp_path), '2fa': 'mail'},
            'Rotation': {'rotation': 5},
            'Notifier': {'level': 1, 'notifier': '', 'notify_if_no_change': False},
            'Danger Zone': {'wait_interval': [0, 0]},
            'Target': {'mode': '', 'list': []},
            'migration': False,
        }

        with pytest.raises(err.err) as exc_info:
            main(parsed_args, notifier.create_instance(""))
        assert exc_info.value.num() == err.err_enum.NEED_DB_MIGRATION

    def test_migration_flag_confirmation(self, tmp_path, monkeypatch):
        from steamCloudSaveDownloader.__main__ import main
        from steamCloudSaveDownloader.notifier import notifier

        db_ = db.db(db_location=str(tmp_path), rotation=5)
        db_.set_db_version(0)

        parsed_args = {
            'General': {'save_dir': str(tmp_path), '2fa': 'mail'},
            'Rotation': {'rotation': 5},
            'Notifier': {'level': 1, 'notifier': '', 'notify_if_no_change': False},
            'Danger Zone': {'wait_interval': [0, 0]},
            'Target': {'mode': '', 'list': []},
            'migration': True,
        }

        # User denies
        monkeypatch.setattr('builtins.input', lambda prompt: 'n')
        main(parsed_args, notifier.create_instance(""))
        assert db_.get_db_version() == 0

        # User confirms
        monkeypatch.setattr('builtins.input', lambda prompt: 'y')
        main(parsed_args, notifier.create_instance(""))
        assert db_.get_db_version() == 1

    def test_backup_db_pattern(self, tmp_path):
        db_location = str(tmp_path)
        db_ = db.db(db_location=db_location, rotation=5)
        db_.set_db_version(0)

        migrator = DatabaseMigrator(db_)
        backup_path = migrator.backup_db(0)

        assert os.path.isfile(backup_path)
        assert backup_path.startswith(f"{db_.db_file}.v0.")
        assert backup_path.endswith(".bak")
