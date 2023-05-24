import os
import pathlib
from . import db
from . import err
from .err import err_enum
import datetime
import logging

logger = logging.getLogger('scsd')

class storage:
    s_version_prefix = '.scsd_'

    def __init__(self, location:str, db_:db.db):
        self.location = location
        self.db_ = db_

    def create_game_folder(self, game_name:str, app_id:int):
        db_game_dir = self.db_.get_game_dir(app_id)

        if (db_game_dir is not None):
            if os.path.isdir(os.path.join(self.location, db_game_dir)):
                return
            else:
                dir_name = db_game_dir
        else:
            dir_name = f"{app_id}"

        target_dir = os.path.join(self.location, dir_name)

        if os.path.isdir(target_dir):
            return

        try:
            os.mkdir(target_dir)
        except:
            pass

        if os.path.isdir(target_dir):
            self.db_.set_game_dir(app_id, dir_name)
            return

        # Maybe game_name contains special character fallback to app_id
        dir_name = f"{app_id}__"
        target_dir = os.path.join(self.location, dir_name)

        if os.path.isdir(target_dir):
            return

        try:
            self.db_.set_game_dir(app_id, dir_name)
            os.mkdir(target_dir)
        except:
            raise err.err(err_enum.CANNOT_CREATE_DIRECTORY)

    def get_version_suffix(self, version_num:int):
        if version_num == 0:
            return ""
        else:
            return storage.s_version_prefix + str(version_num)


    # Implicitly create the path if not exist
    def get_filename_location(self,
                              app_id:int,
                              filename:str,
                              file_path:str,
                              version_num:int):
        db_game_dir = self.db_.get_game_dir(app_id)

        version_suffix = self.get_version_suffix(version_num)

        path_to_save = os.path.join(self.location, db_game_dir, file_path)

        if not os.path.isdir(path_to_save):
            os.makedirs(path_to_save)

        return os.path.join(path_to_save, filename + version_suffix)

    def increment_file_version(self,
                               app_id:int,
                               filename:str,
                               file_path:str,
                               current_max_version:int):
        db_game_dir = self.db_.get_game_dir(app_id)

        path_to_save = os.path.join(self.location, db_game_dir, file_path)

        # if db has 5 versions
        # rename
        # version 4 -> 5
        # version 3 -> 4
        # version 2 -> 3
        # version 1 -> 2
        # version 0 -> 1
        for old, new in zip(
                range(current_max_version - 2, -1, -1),
                range(current_max_version - 1, 0, -1)):
            old_version_suffix = self.get_version_suffix(old)
            new_version_suffix = self.get_version_suffix(new)

            os.rename(
                os.path.join(path_to_save, filename + old_version_suffix),
                os.path.join(path_to_save, filename + new_version_suffix))

    # Move current version 0 to 1, 1 to 2, etc
    # Should be done before download file
    def rotate_file(self, app_id:int, filename:str, file_path:str, file_id:int, newest_file_time: datetime.datetime):
        num_of_version = self.db_.update_file_update_time_to_now(file_id, newest_file_time)
        self.increment_file_version(app_id, filename, file_path, num_of_version)

    def remove_outdated(self,
                        app_id:int,
                        filename:str,
                        file_path:str,
                        file_id:int):
        outdated_version_num = self.db_.remove_outdated_file(file_id)

        db_game_dir = self.db_.get_game_dir(app_id)
        path_to_save = os.path.join(self.location, db_game_dir, file_path)

        if outdated_version_num is None:
            return

        for version_num_tup in outdated_version_num:
            version_suffix = self.get_version_suffix(version_num_tup[0])
            logger.info(f"Remove rotated file {filename + version_suffix}")
            try:
                os.remove(os.path.join(path_to_save, filename + version_suffix))
            except:
                e = err.err(err_enum.CANNOT_REMOVE_OUTDATED)
                e.set_additional_info(filename + version_suffix)
                e.log()
