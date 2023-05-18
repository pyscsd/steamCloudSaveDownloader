from . import args
from . import web
from . import db
from . import storage
from .auth import auth
from . import err
from .notifier import notifier
from .config import config
import logging
import sys
import os
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
        auth_ = auth(parsed_args['save_dir'])
        auth_.new_session(parsed_args['auth'])
        exit(0)

    if parsed_args['conf'] is not None:
        parsed_args = config(parsed_args['conf']).get_conf()

    return parsed_args

def __main__():
    global logger

    notifier_ = None

    try:
        setup_logger()
        parsed_args = parse()

        logger.setLevel(args.args.convert_log_level(parsed_args['log_level']))
        logger.debug(parsed_args)

        notifier_ = notifier.create_instance(
            parsed_args['notifier'],
            **parsed_args)

        main(parsed_args)
    except err.err as e:
        if notifier_:
            notifier_.send(e.get_msg(), False)
        e.log()
        exit(e.num())
    except Exception:
        if notifier_:
            notifier_.send(traceback.format_exc(), False)
        exit(e.num())

    end_msg = "Process ended noramlly"
    logger.info(end_msg)
    notifier_.send(end_msg, True)
    exit(0)

def main(parsed_args):

    auth_ = auth(parsed_args['save_dir'])

    session_pkl = auth_.get_session_path()
    if not os.path.isfile(session_pkl):
        raise err.err(err.err_enum.NO_SESSION)
    web_ = web.web(session_pkl)

    db_ = db.db(parsed_args['save_dir'], parsed_args['rotation'])
    storage_ = storage.storage(parsed_args['save_dir'], db_)

    game_list = web_.get_list()

    for game in game_list:
        # DBG
        if game['app_id'] != 1761390:
            continue;
        logger.info(f"Processing {game['name']}")
        file_infos = web_.get_game_save(game['link'])

        if (not db_.is_game_exist(game['app_id'])):
            db_.add_new_game(game['app_id'], game['name'])
            storage_.create_game_folder(game['name'], game['app_id'])

            file_tuples = [(file_info['filename'], file_info['path'], game['app_id'], file_info['time']) for file_info in file_infos]
            db_.add_new_files(file_tuples)

            for file_info in file_infos:
                logger.info(f"  Downloading {file_info['filename']}")
                web_.download_game_save(
                    file_info['link'],
                    storage_.get_filename_location(game['app_id'],
                                                   file_info['filename'],
                                                   file_info['path'],
                                                   0),
                )
            continue

        for file_info in file_infos:
            file_id = db_.get_file_id(game['app_id'], file_info['filename'])
            if (not db_.is_file_outdated(file_id, file_info['time'])):
                logger.info(f"Ignore {file_info['filename']} (no change)")
                continue
            logger.info(f"Downloading {file_info['filename']}")
            storage_.rotate_file(
                game['app_id'],
                file_info['filename'],
                file_info['path'],
                file_id,
                file_info['time'])
            web_.download_game_save(
                file_info['link'],
                storage_.get_filename_location(game['app_id'],
                                               file_info['filename'],
                                               file_info['path'],
                                               0)
            )
            storage_.remove_outdated(
                game['app_id'],
                file_info['filename'],
                file_info['path'],
                file_id)
