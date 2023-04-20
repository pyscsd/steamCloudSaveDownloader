from . import args
from . import web
import random
import time

def main(argv):
    parsed_args = args.args().parse(argv)

    web_ = web.web(parsed_args['cookie'])

    game_list = web_.get_list()

    for game in game_list:
        file_infos = web_.get_game_save(game['Link'])
        print(file_infos)
        break
        time.sleep(random.randint(2, 5))
