from .logger import logger
from .auth import auth
from . import db
from . import err
from . import storage
from . import web
from .summary import summary

from functools import wraps
import os

def downloader_locker(method):
    @wraps(method)
    def impl(self, *args, **kwargs):
        try:
            self.create_lock_file()
            retval = method(self, *args, **kwargs)
            self.delete_lock_file()
            return retval
        except err.err as e:
            if e.num() != err.err_enum.LOCKED.value:
                try:
                    self.delete_lock_file()
                except:
                    pass
            raise e
        except (KeyboardInterrupt, Exception) as e:
            try:
                self.delete_lock_file()
            except:
                pass
            raise e
    return impl


class downloader:
    lock_file_name = ".scsd.lock"

    def __init__(self, p_parsed_args: dict):
        self.parsed_args = p_parsed_args

        self.summary = None
        self.notifier = None

        self.auth = auth(
            p_parsed_args['General']['config_dir'],
            p_parsed_args['General']['2fa'])

        self.auth.refresh_session()
        session_pkl = self.auth.get_session_path()
        self.web = web.web(
            session_pkl,
            p_parsed_args['Danger Zone']['wait_interval'])

        self.db = db.db(p_parsed_args['General']['config_dir'],
                    p_parsed_args['Rotation']['rotation'])
        self.storage = storage.storage(p_parsed_args['General']['save_dir'], self.db)

        logger.info("Getting Game Save List")
        self.game_list = self.web.get_list()

    def create_lock_file(self):
        lock_path = os.path.join(self.parsed_args['General']['config_dir'], downloader.lock_file_name)
        if os.path.isfile(lock_path):
            exception = err.err(err.err_enum.LOCKED)
            exception.set_additional_info(f" (Path: {lock_path})")
            raise exception

        with open(lock_path, 'w') as f:
            pass

    def delete_lock_file(self):
        lock_path = os.path.join(self.parsed_args['General']['config_dir'], downloader.lock_file_name)
        if os.path.isfile(lock_path):
            os.remove(lock_path)

    def show_summary(self, p_notifier):
        self.notifier = p_notifier
        self.summary = summary(int(self.parsed_args['Notifier']['level']))

    def should_process_appid(self, p_app_id: int) -> bool:
        if self.parsed_args['Target']['mode'] == '':
            return True

        if self.parsed_args['Target']['mode'] == 'include':
            return p_app_id in self.parsed_args['Target']['list']
        elif self.parsed_args['Target']['mode'] == 'exclude':
            return p_app_id not in self.parsed_args['Target']['list']

        return True

    def get_overall_target_counts(self, p_game_list:list) -> int:
        return len([game for game in p_game_list if self.should_process_appid(game['app_id'])])

    @downloader_locker
    def download_all_games(self):
        target_count = self.get_overall_target_counts(self.game_list)

        current_game_index = 1

        for game in self.game_list:
            if self.db.is_requests_limit_exceed():
                raise err.err(err.err_enum.REQUESTS_LIMIT_EXCEED)
            if not self.should_process_appid(game['app_id']):
                logger.debug(f"Ignoring {game['name']} ({game['app_id']})")
                continue

            logger.info(f"({current_game_index}/{target_count}) Processing {game['name']}")
            current_game_index += 1
            self.download_game(game)
        self.send_summary()


    @downloader_locker
    def download_games(self, p_games: list):
        for game in self.game_list:
            if game['app_id'] not in p_games:
                continue
            logger.info(f"Processing {game['name']}")
            self.download_game(game)


    def download_game(self, p_game):
        self.update_game(p_game)

    '''
    Return true if updated
    '''
    def update_game(self, p_game: dict):
        file_infos = self.web.get_game_save(p_game['link'])

        if file_infos is None:
            logger.warning(f"Unable to retrieve {p_game['name']} file list. Skipped.")
            return

        if (not self.db.is_game_exist(p_game['app_id'])):
            self.add_new_game(p_game, file_infos)
            return

        self.db.set_game_last_checked_time_to_now(p_game['app_id'])

        requests_count = 1
        for file_info in file_infos:
            file_id = self.db.get_file_id(p_game['app_id'], file_info['path'], file_info['filename'])
            if file_id is None:
                file_tuples = [(file_info['filename'],
                                file_info['path'],
                                p_game['app_id'],
                                file_info['time'])]
                self.db.add_new_files(file_tuples)
                logger.info(f"New file {file_info['filename']} added")
                file_id = self.db.get_file_id(p_game['app_id'], file_info['path'], file_info['filename'])
                self.download_game_save(p_game, file_info)

                self.add_summary(p_game, [file_info], None)
            else:
                outdated, db_time = self.db.is_file_outdated(file_id, file_info['time'])
                if (not outdated):
                    logger.debug(f"Ignore {file_info['filename']} (no change)")
                    continue

                self.storage.rotate_file(
                    p_game['app_id'],
                    file_info['filename'],
                    file_info['path'],
                    file_id,
                    file_info['time'])
                self.download_game_save(p_game, file_info)
                self.storage.remove_outdated(
                    p_game['app_id'],
                    file_info['filename'],
                    file_info['path'],
                    file_id)

                self.add_summary(p_game, [file_info], db_time)

            requests_count += 1

        self.db.add_requests_count(requests_count)

        return

    def add_new_game(self, p_game, p_file_infos):
        self.db.add_new_game(p_game['app_id'], p_game['name'])
        self.storage.create_game_folder(p_game['name'], p_game['app_id'])

        file_tuples = [(file_info['filename'], file_info['path'], p_game['app_id'], file_info['time']) for file_info in p_file_infos]
        self.db.add_new_files(file_tuples)

        for file_info in p_file_infos:
            self.download_game_save(p_game, file_info)

        self.add_summary(p_game, p_file_infos, None)
        self.db.add_requests_count(len(p_file_infos) + 1)

    def download_game_save(self, p_game, p_file_info):
        logger.info(f"Downloading {p_file_info['filename']}")
        self.web.download_game_save(
            p_file_info['link'],
            self.storage.get_filename_location(p_game['app_id'],
                                        p_file_info['filename'],
                                        p_file_info['path'],
                                        0),
        )

    def add_summary(self,
        p_game: dict,
        p_file_infos: list,
        p_db_time):
        if self.summary is None:
            return
        self.summary.add_game(p_game['name'])

        for file_info in p_file_infos:
            self.summary.add_game_file(
                p_game['name'],
                file_info['filename'],
                p_db_time,
                file_info['time'])

    def send_summary(self):
        if self.summary is None or self.notifier is None:
            return

        if self.summary.has_changes():
            summary_str = self.summary.get()
            if summary_str and len(summary_str) != 0:
                self.notifier.send(summary_str, True)
        else:
            if self.parsed_args['Notifier']['notify_if_no_change']:
                self.notifier.send("No changes", True)

    def update_new_games_to_db(self):
        for game in self.game_list:
            if (self.db.is_game_exist(game['app_id'])):
                continue
            self.db.add_new_game(game['app_id'], game['name'])
            self.storage.create_game_folder(game['name'], game['app_id'])

def download_games(p_parsed_args: dict, p_app_ids: list):
    downloader_ = downloader(p_parsed_args)
    downloader_.download_games(p_app_ids)

def download_all_games(p_parsed_args: dict, p_notifier):
    downloader_ = downloader(p_parsed_args)
    downloader_.show_summary(p_notifier)
    downloader_.download_all_games()

def get_game_list_and_update(p_parsed_args: dict):
    downloader_ = downloader(p_parsed_args)
    downloader_.update_new_games_to_db()
    return downloader_.game_list

def get_account_id(p_parsed_args: dict):
    account_id_file = os.path.join(p_parsed_args['General']['config_dir'], 'account_id')
    if os.path.isfile(account_id_file):
        with open(account_id_file, 'r') as f:
            content = f.read()
        return int(content)

    auth_ = auth(
        p_parsed_args['General']['config_dir'],
        p_parsed_args['General']['2fa'])
    auth_.refresh_session()
    web_ = web.web(auth_.get_session_path(), p_parsed_args['Danger Zone']['wait_interval'])
    account_id = web_.get_account_id()
    with open(account_id_file, 'w') as f:
        f.write(str(account_id))
    return account_id