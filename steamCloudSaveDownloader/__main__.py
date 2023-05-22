from . import args
from . import web
from . import db
from . import storage
from . import ver
from .auth import auth
from . import err
from .notifier import notifier
from .config import config
import logging
import sys
import traceback

logger = None

def setup_logger():
    global logger

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger('scsd')

def parse():
    parsed_args = args.args().parse(sys.argv[1:])

    if 'auth' in parsed_args and \
            parsed_args['auth'] is not None and \
            len(parsed_args['auth']) != 0:
        auth_ = auth(parsed_args['Required']['save_dir'])
        auth_.new_session(parsed_args['auth'])
        exit(0)

    if parsed_args['conf'] is not None:
        parsed_args = config(parsed_args['conf']).get_conf()
    else:
        parsed_args = config().load_from_arg(parsed_args)

    return parsed_args

def should_process_appid(p_target:dict(), p_input:int) -> bool:
    if p_target['mode'] is None:
        return True

    if p_target['mode'] == 'include':
        return p_input in p_target['list']
    elif p_target['mode'] == 'exclude':
        return p_input not in p_target['list']

    return True

def __main__():
    global logger

    notifier_ = None

    try:
        setup_logger()
        parsed_args = parse()

        logger.setLevel(args.args.convert_log_level(parsed_args['Log']['log_level']))
        logger.info(f'scsd-{ver.__version__} started')
        logger.debug(parsed_args)

        notifier_ = notifier.create_instance(
            parsed_args['Notifier']['notifier'],
            **parsed_args['Notifier'])

        summary = main(parsed_args)
    except err.err as e:
        if notifier_:
            notifier_.send(e.get_msg(), False)
        e.log()
        exit(e.num())
    except Exception:
        if notifier_:
            notifier_.send(f"\n```{traceback.format_exc()}```", False)
        exit(err.err_enum.UNKNOWN_EXCEPTION.value)

    if summary:
        notifier_.send(summary, True)
    exit(0)

def add_new_game(db_, storage_, web_, game, file_infos, summary) -> str:
    db_.add_new_game(game['app_id'], game['name'])
    storage_.create_game_folder(game['name'], game['app_id'])

    file_tuples = [(file_info['filename'], file_info['path'], game['app_id'], file_info['time']) for file_info in file_infos]
    db_.add_new_files(file_tuples)

    summary += f"{game['name']}\n"

    for file_info in file_infos:
        summary = download_game_save(storage_, web_, game, file_info, summary)

    return summary

def download_game_save(storage_, web_, game, file_info, summary) -> str:
    logger.info(f"Downloading {file_info['filename']}")
    summary += f"↳{file_info['filename']}\n"
    web_.download_game_save(
        file_info['link'],
        storage_.get_filename_location(game['app_id'],
                                       file_info['filename'],
                                       file_info['path'],
                                       0),
    )

    return summary

'''
Return true if updated
'''
def update_game(db_, storage_, web_, game, summary) -> tuple:
    logger.info(f"Processing {game['name']}")
    file_infos = web_.get_game_save(game['link'])

    has_update = False

    if (not db_.is_game_exist(game['app_id'])):
        summary = add_new_game(db_, storage_, web_, game, file_infos, summary)
        has_update = True
        return (has_update, summary)

    for file_info in file_infos:
        file_id = db_.get_file_id(game['app_id'], file_info['filename'])
        if (not db_.is_file_outdated(file_id, file_info['time'])):
            logger.info(f"Ignore {file_info['filename']} (no change)")
            continue

        if not has_update:
            summary += f"{game['name']}\n"

        has_update = True

        storage_.rotate_file(
            game['app_id'],
            file_info['filename'],
            file_info['path'],
            file_id,
            file_info['time'])
        summary = download_game_save(storage_, web_, game, file_info, summary)

        storage_.remove_outdated(
            game['app_id'],
            file_info['filename'],
            file_info['path'],
            file_id)

    return (has_update, summary)

def main(parsed_args) -> str:

    auth_ = auth(parsed_args['Required']['save_dir'])

    session_pkl = auth_.get_session_path()
    web_ = web.web(session_pkl)

    db_ = db.db(parsed_args['Required']['save_dir'],
                parsed_args['Rotation']['rotation'])
    storage_ = storage.storage(parsed_args['Required']['save_dir'], db_)

    game_list = web_.get_list()

    summary = "\nExecute summary:\n```\n"

    has_update = False
    for game in game_list:
        if not should_process_appid(parsed_args['Target'], game['app_id']):
            logger.debug(f"Ignoring {game['name']} ({game['app_id']})")
            continue

        game_has_update, summary = \
            update_game(db_, storage_, web_, game, summary)

        has_update = has_update or game_has_update

    if has_update:
        summary += "```"
    else:
        summary = None

    return summary
