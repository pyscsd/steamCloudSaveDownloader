from . import db
from .logger import logger

class stored:
    def __init__(self, staged_args, config_dir):
        self.target = staged_args
        self.config_dir = config_dir
        self.db = db.db(config_dir)

    def get_result(self):
        id_and_names = self.db.get_stored_game_names(self.target)
        for app_id, game_name in id_and_names:
            print(f"- {game_name}({app_id})")
            files_info = \
                self.db.get_files_info_by_appid(app_id)
            for file_id, filename, location in files_info:
                print(f"  - {location}/{filename}")
                version_info = \
                    self.db.get_file_version_by_file_id(file_id)
                for version_date, version_num in version_info:
                    print(f"    - {version_num} : {version_date}")
