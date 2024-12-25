from . import args
from .auth import auth
from . import config
from . import downloader
from . import err
from .notifier import notifier
from . import stored
from .logger import logger, setup_logger_post_config
from . import utility

import os
import sys
import traceback

def in_container_check():
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

    in_container_check()
    return parsed_args


def __main__():
    global logger

    notifier_ = None

    exit_num = 0
    try:
        parsed_args = parse()

        utility.save_dir_permission_checking(parsed_args['General']['save_dir'])

        setup_logger_post_config(
            os.path.join(parsed_args['General']['save_dir'], 'scsd.log'),
            parsed_args['Log']['log_level'])

        logger.info(f'Options: {parsed_args}')

        logger.info(f"CWD: {os.getcwd()}")
        logger.info(f"Files will be saved to '{parsed_args['General']['save_dir']}'")


        notifier_ = notifier.create_instance(
            parsed_args['Notifier']['notifier'],
            **parsed_args['Notifier'])

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
        ec = traceback.format_exc()
        if notifier_:
            if not notifier_.send(f"\n```{ec}```", False):
                logger.warning("Notifier not working as intended. Exception:")
                logger.warning(notifier_.exception)
        if logger:
            logger.error(ec)
        else:
            print(ec)
        exit_num = err.err_enum.UNKNOWN_EXCEPTION.value
    sys.exit(exit_num)

def main(parsed_args, notifier_):
    global logger

    if 'auth' in parsed_args and \
            parsed_args['auth'] is not None and \
            len(parsed_args['auth']) != 0:
        auth_ = auth(
            parsed_args['General']['save_dir'],
            parsed_args['General']['2fa'])

        auth_.new_session(parsed_args['auth'])
        return
    elif 'stored' in parsed_args and \
        parsed_args['stored'] is not None:
        stored_ = stored.stored(parsed_args['stored'], parsed_args['General']['save_dir'])
        stored_.get_result()
        return

    downloader.download_all_games(parsed_args, notifier_)