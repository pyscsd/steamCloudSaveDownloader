from . import args
from . import web
from . import db
from . import storage

def main(argv):
    parsed_args = args.args().parse(argv)

    web_ = web.web(parsed_args['cookie'])

    db_ = db.db(parsed_args['save_dir'], parsed_args['rotation'])
    storage_ = storage.storage(parsed_args['save_dir'], db_)

    game_list = web_.get_list()

    for game in game_list:
        if game['app_id'] != 1761390:
            continue;
        print(f"Processing {game['name']}")
        file_infos = web_.get_game_save(game['link'])

        if (not db_.is_game_exist(game['app_id'])):
            db_.add_new_game(game['app_id'], game['name'])
            storage_.create_game_folder(game['name'], game['app_id'])

            file_tuples = [(file_info['filename'], file_info['path'], game['app_id'], file_info['time']) for file_info in file_infos]
            db_.add_new_files(file_tuples)

            for file_info in file_infos:
                print(f"  Downloading {file_info['filename']}")
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
                continue
            print(f"  Downloading {file_info['filename']}")
            storage_.rotate_file(
                game['app_id'],
                file_info['filename'],
                file_info['path'],
                file_id)
            web_.download_game_save(
                file_info['link'],
                storage_.get_filename_location(game['app_id'],
                                               file_info['filename'],
                                               file_info['path'],
                                               0)
            )
            storage_.remove_outdated(file_id)
