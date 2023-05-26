from . import err
from .err import err_enum
from .parser import web_parser
import requests
import pickle
import shutil
import time
import random
import os

g_web_acc_link = "https://store.steampowered.com/account/?l=english"
g_web_link = "https://store.steampowered.com/account/remotestorage/?l=english"
g_random_sleep_interval = (1, 3)

def random_sleep(func):
    def wrapper(*args, **kwargs):
        time.sleep(random.randint(g_random_sleep_interval[0], g_random_sleep_interval[1]))
        return func(*args, **kwargs)
    return wrapper

class web:
    def __init__(self, cookie):
        if not os.path.isfile(cookie):
            raise err.err(err_enum.NO_SESSION)
        self.web_parser = web_parser()
        self.session = requests.Session()
        self.cookie_pkl = cookie
        try:
            with open(self.cookie_pkl, 'rb') as f:
                self.session.cookies.update(pickle.load(f))
        except:
            raise err.err(err_enum.INVALID_COOKIE_FORMAT)

        response = self.session.get(g_web_acc_link)

    # Return list of {"Game": name, "Link", link}
    @random_sleep
    def get_list(self):
        response = self.session.get(g_web_link)
        if (response.status_code != 200):
            raise err(err_enum.ERR_CANNOT_RETRIEVE_LIST_MSG)

        return self.web_parser.parse_index(response.text)

    @random_sleep
    def _get_game_save(self, game_link:str):
        response = self.session.get(game_link)
        if (response.status_code != 200):
            err.err_enum(err_enum.CANNOT_RETRIEVE_GAME_FILES).log
            return (None, None)

        return self.web_parser.parse_game_file(response.text)


    def get_game_save(self, game_link:str):
        # Some games have a lot of games with multiple pages
        next_page_link = game_link
        save_file_list = list()
        while True:
            partial_save_file_list, next_page_link = \
                self._get_game_save(next_page_link)
            save_file_list += partial_save_file_list
            if next_page_link is None:
                break
        return save_file_list

    @random_sleep
    def download_game_save(self, link:str, store_location:str):
        with self.session.get(link, stream=True) as r:
            with open(store_location, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
