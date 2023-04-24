from . import args
from . import web
from . import db
import random # TODO Move to web
import time

def main(argv):
    parsed_args = args.args().parse(argv)

    web_ = web.web(parsed_args['cookie'])

    db_ = db.db(parsed_args['save_dir'])

    game_list = web_.get_list()

    for game in game_list:
        file_infos = web_.get_game_save(game['link'])

        if (not db_.is_game_exist(game['app_id'])):
            db_.add_new_game(game['app_id'], game['name'])

            file_tuples = [(file_info['filename'], game['app_id'], file_info['time']) for file_info in file_infos]
            print(file_tuples)
            db_.add_new_files(file_tuples)
            # TODO:Download files
            # TODO Uncomment continue, delete break
            #continue
            break

        for file_info in file_infos:
            if (not db_.is_file_outdated(game['app_id'], file_info['filename'], file_info['time'])):
                continue
            # TODO:Download files
            db_.update_file_update_time_to_now(game['app_id'], file_info['filename'])
        # TODO Remove break
        break
        time.sleep(random.randint(2, 5))
