import os
import pathlib
from . import db
from . import err
from .err import err_enum

class storage:
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
            dir_name = f"{app_id}__{game_name}"

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


    # Implicitly create the path if not exist
    def get_filename_location(self, app_id:int, filename:str, file_path:str):
        db_game_dir = self.db_.get_game_dir(app_id)

        path_to_save = os.path.join(self.location, db_game_dir, file_path)

        if not os.path.isdir(path_to_save):
            os.makedirs(path_to_save)

        return os.path.join(path_to_save, filename)
