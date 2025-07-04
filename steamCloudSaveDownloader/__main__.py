from . import args
from .auth import auth
from . import config
from . import db
from . import err
from .notifier import notifier
from . import storage
from . import stored
from .summary import summary
from . import utility
from . import ver
from . import web

import logging
import logging.handlers
import os
import sys
import traceback

logger = None

g_lock_file_name = ".scsd.lock"
g_logger_format = '%(asctime)s [%(levelname)s] %(message)s'
g_logger_datefmt = '%Y-%m-%d %H:%M:%S'
g_logger_formatter = logging.Formatter(
    fmt=g_logger_format, datefmt=g_logger_datefmt)

def setup_logger():
    global logger

    logger = logging.getLogger('scsd')
    sh = logging.StreamHandler()
    sh.setFormatter(g_logger_formatter)
    logger.addHandler(sh)
    logger.info(f'scsd-{ver.__version__} started')
    logger.setLevel(logging.INFO)

def setup_logger_post_config(parsed_args):
    global logger

    fh = logging.handlers.RotatingFileHandler(
        os.path.join(parsed_args['General']['save_dir'], 'scsd.log'),
        maxBytes=10485760, # 10MB
        backupCount=5)
    fh.setFormatter(g_logger_formatter)
    logger.addHandler(fh)
    logger.setLevel(args.args.convert_log_level(parsed_args['Log']['log_level']))

def in_container_check(parsed_args):
    if os.path.isfile("/.scsd_dockerenv") and os.getenv("SCSD_DOCKER") is None:
        logger.warning("Detect container environment. Please run scsd with `/opt/run.sh` and authentication with `scsd_auth`")

def parse():
    parsed_args = args.args().parse(sys.argv[1:])

    def is_stored_specified(parsed_args):
        if parsed_args == [-1]:
            return None
        elif parsed_args == None:
            return []
        else:
            return parsed_args


    if parsed_args['conf'] is not None:
        parsed_args = \
            config.config(
                parsed_args['conf'],
                auth=parsed_args['auth'],
                stored=is_stored_specified(parsed_args['stored'])
            ).get_conf()
    else:
        logger.info(f'Config file not provided')
        parsed_args = \
            config.config(
                stored=is_stored_specified(parsed_args['stored'])
            ).load_from_arg(parsed_args)

    in_container_check(parsed_args)
    return parsed_args

def should_process_appid(p_target:dict(), p_input:int) -> bool:
    if p_target['mode'] == '':
        return True

    if p_target['mode'] == 'include':
        return p_input in p_target['list']
    elif p_target['mode'] == 'exclude':
        return p_input not in p_target['list']

    return True

def get_overall_target_counts(p_target:dict, p_game_list:list) -> int:
    return len([game for game in p_game_list if should_process_appid(p_target, game['app_id'])])


def __main__():
    global logger

    notifier_ = None

    exit_num = 0
    try:
        setup_logger()
        parsed_args = parse()

        utility.save_dir_permission_checking(parsed_args['General']['save_dir'])

        setup_logger_post_config(parsed_args)

        logger.info(f'Options: {parsed_args}')

        logger.info(f"CWD: {os.getcwd()}")
        logger.info(f"Files will be saved to '{parsed_args['General']['save_dir']}'")


        notifier_ = notifier.create_instance(
            parsed_args['Notifier']['notifier'],
            **parsed_args['Notifier'])

        create_lock_file(parsed_args['General']['save_dir'])
        main(parsed_args, notifier_)
    except err.err as e:
        if notifier_:
            if not notifier_.send(e.get_msg(), False):
                logger.warning("Notifier not working as intended. Exception:")
                logger.warning(notifier_.exception)
        e.log()
        exit_num = e.num()
    except KeyboardInterrupt:
        exit_num = err.err_enum.KB_INTERRUPT.value
        print("Keyboard interrupt received", file=sys.stderr)
    except Exception as e:
        ec = \
            "".join(
                traceback.TracebackException.from_exception(
                    e,
                    capture_locals=True).format())
        if notifier_:
            if not notifier_.send(f"\n```{ec}```", False):
                logger.warning("Notifier not working as intended. Exception:")
                logger.warning(notifier_.exception)
        if logger:
            logger.error(ec)
        else:
            print(ec)
        exit_num = err.err_enum.UNKNOWN_EXCEPTION.value
    if exit_num != err.err_enum.LOCKED.value:
        try:
            delete_lock_file(parsed_args['General']['save_dir'])
        except:
            pass
    sys.exit(exit_num)

def add_new_game(db_, storage_, web_, game, file_infos, summary_):
    db_.add_new_game(game['app_id'], game['name'])
    storage_.create_game_folder(game['name'], game['app_id'])

    file_tuples = [(file_info['filename'], file_info['path'], game['app_id'], file_info['time']) for file_info in file_infos]
    db_.add_new_files(file_tuples)

    summary_.add_game(game['name'])

    for file_info in file_infos:
        download_game_save(storage_, web_, game, file_info)
        summary_.add_game_file(
            game['name'],
            file_info['filename'],
            None,
            file_info['time'])

    db_.add_requests_count(len(file_infos) + 1)

def download_game_save(storage_, web_, game, file_info):
    global logger
    logger.info(f"Downloading {file_info['filename']}")
    web_.download_game_save(
        file_info['link'],
        storage_.get_filename_location(game['app_id'],
                                       file_info['filename'],
                                       file_info['path'],
                                       0),
    )

'''
Return true if updated
'''
def update_game(db_, storage_, web_, game, summary_):
    global logger
    file_infos = web_.get_game_save(game['link'])

    if file_infos is None:
        logger.warning(f"Unable to retrieve {game['name']} file list. Skipped.")
        return


    if (not db_.is_game_exist(game['app_id'])):
        add_new_game(db_, storage_, web_, game, file_infos, summary_)
        return

    requests_count = 1
    for file_info in file_infos:
        file_id = db_.get_file_id(game['app_id'], file_info['path'], file_info['filename'])
        if file_id is None:
            file_tuples = [(file_info['filename'],
                            file_info['path'],
                            game['app_id'],
                            file_info['time'])]
            db_.add_new_files(file_tuples)
            logger.info(f"New file {file_info['filename']} added")
            file_id = db_.get_file_id(game['app_id'], file_info['path'], file_info['filename'])
            download_game_save(storage_, web_, game, file_info)
            summary_.add_game(game['name'])
            summary_.add_game_file(
                game['name'],
                file_info['filename'],
                None,
                file_info['time'])
        else:
            outdated, db_time = db_.is_file_outdated(file_id, file_info['time'])
            if (not outdated):
                logger.debug(f"Ignore {file_info['filename']} (no change)")
                continue

            storage_.rotate_file(
                game['app_id'],
                file_info['filename'],
                file_info['path'],
                file_id,
                file_info['time'])
            download_game_save(storage_, web_, game, file_info)
            storage_.remove_outdated(
                game['app_id'],
                file_info['filename'],
                file_info['path'],
                file_id)
            summary_.add_game(game['name'])
            summary_.add_game_file(
                game['name'],
                file_info['filename'],
                db_time,
                file_info['time'])

        requests_count += 1

    db_.add_requests_count(requests_count)

    return

def create_lock_file(path_):
    lock_path = os.path.join(path_, g_lock_file_name)
    if os.path.isfile(lock_path):
        exception = err.err(err.err_enum.LOCKED)
        exception.set_additional_info(f" (Path: {lock_path})")
        raise exception

    with open(lock_path, 'w') as f:
        pass

def delete_lock_file(path_):
    lock_path = os.path.join(path_, g_lock_file_name)
    if os.path.isfile(lock_path):
        os.remove(lock_path)

def main(parsed_args, notifier_):
    global logger

    summary_ = summary(int(parsed_args['Notifier']['level']))
    auth_ = auth(
        parsed_args['General']['save_dir'],
        parsed_args['General']['2fa'])

    if 'auth' in parsed_args and \
            parsed_args['auth'] is not None and \
            len(parsed_args['auth']) != 0:
        auth_.new_session(parsed_args['auth'])
        return
    elif 'stored' in parsed_args and \
        parsed_args['stored'] is not None:
        stored_ = stored.stored(parsed_args['stored'], parsed_args['General']['save_dir'])
        stored_.get_result()
        return

    auth_.refresh_session()
    session_pkl = auth_.get_session_path()
    web_ = web.web(session_pkl, parsed_args['Danger Zone']['wait_interval'])

    db_ = db.db(parsed_args['General']['save_dir'],
                parsed_args['Rotation']['rotation'])
    storage_ = storage.storage(parsed_args['General']['save_dir'], db_)

    logger.info("Getting Game Save List")
    game_list = web_.get_list()

    target_count = get_overall_target_counts(parsed_args['Target'], game_list)

    current_game_index = 1

    for game in game_list:
        if db_.is_requests_limit_exceed():
            raise err.err(err.err_enum.REQUESTS_LIMIT_EXCEED)
        if not should_process_appid(parsed_args['Target'], game['app_id']):
            logger.debug(f"Ignoring {game['name']} ({game['app_id']})")
            continue

        logger.info(f"({current_game_index}/{target_count}) Processing {game['name']}")
        current_game_index += 1
        update_game(db_, storage_, web_, game, summary_)

    if summary_.has_changes():
        summary_str = summary_.get()
        if summary_str and len(summary_str) != 0:
            notifier_.send(summary_str, True)
    else:
        if parsed_args['Notifier']['notify_if_no_change']:
            notifier_.send("No changes", True)
