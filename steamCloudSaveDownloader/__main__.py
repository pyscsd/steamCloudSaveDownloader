from . import args
from . import web
from . import db
from . import storage
import random # TODO Move to web

def main(argv):
    parsed_args = args.args().parse(argv)

    web_ = web.web(parsed_args['cookie'])

    db_ = db.db(parsed_args['save_dir'])
    storage_ = storage.storage(parsed_args['save_dir'], db_)

    game_list = web_.get_list()

    for game in game_list:
        print(f"Processing {game['name']}")
        file_infos = web_.get_game_save(game['link'])

        if (not db_.is_game_exist(game['app_id'])):
            db_.add_new_game(game['app_id'], game['name'])
            storage_.create_game_folder(game['name'], game['app_id'])

            file_tuples = [(file_info['filename'], game['app_id'], file_info['time']) for file_info in file_infos]
            db_.add_new_files(file_tuples)

            for file_info in file_infos:
                print(f"  Downloading {file_info['filename']}")
                web_.download_game_save(file_info['link'], storage_.get_filename_location(game['app_id'], file_info['filename']))
            # TODO Uncomment continue, delete break
            #continue
            break

        for file_info in file_infos:
            if (not db_.is_file_outdated(game['app_id'], file_info['filename'], file_info['time'])):
                continue
            print(f"  Downloading {file_info['filename']}")
            web_.download_game_save(file_info['link'], storage_.get_filename_location(game['app_id'], file_info['filename']))
            db_.update_file_update_time_to_now(game['app_id'], file_info['filename'])
        # TODO Remove break
        break
