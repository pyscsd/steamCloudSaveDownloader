from . import err
from .err import err_enum
from .parser import web_parser
import requests
import pickle
import shutil
import time
import random
import os
import logging

g_language_specifier = "l=english"
g_web_acc_link = f"https://store.steampowered.com/account/?{g_language_specifier}"
g_web_link = f"https://store.steampowered.com/account/remotestorage/?{g_language_specifier}"
g_random_sleep_interval = (3, 5)
g_retry_count = 3
g_random_retry_interval = (15, 30)

logger = logging.getLogger('scsd')

def random_sleep_and_retry(func):
    def wrapper(*args, **kwargs):
        time.sleep(random.randint(g_random_sleep_interval[0], g_random_sleep_interval[1]))
        exception = None
        for i in range(g_retry_count):
            try:
                retval = func(*args, **kwargs)
                return retval
            except err.err as e:
                exception = e
                e.log()
                sleep_interval = \
                    random.randint(
                        g_random_retry_interval[0],
                        g_random_retry_interval[1])
                time.sleep(sleep_interval)
                logger.info(f'Retrying in {sleep_interval} seconds')
        logger.error(f'Maximum attempt reached. Aborting')
        raise exception
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
    @random_sleep_and_retry
    def get_list(self):
        response = self.session.get(g_web_link)
        if (response.status_code != 200):
            raise err.err(err_enum.CANNOT_RETRIEVE_LIST)

        return self.web_parser.parse_index(response.text)

    @random_sleep_and_retry
    def _get_game_save(self, game_link:str):
        response = self.session.get(game_link)
        if (response.status_code != 200):
            err.err(err_enum.CANNOT_RETRIEVE_GAME_FILES).log()
            return (None, None)

        return self.web_parser.parse_game_file(response.text)


    def get_game_save(self, game_link:str):
        # Some games have a lot of games with multiple pages
        next_page_link = game_link
        save_file_list = list()
        while True:
            partial_save_file_list, next_page_link = \
                self._get_game_save(next_page_link)
            if partial_save_file_list is None:
                return None
            save_file_list += partial_save_file_list
            if next_page_link is None:
                break
        return save_file_list

    @random_sleep_and_retry
    def download_game_save(self, link:str, store_location:str):
        with self.session.get(link, stream=True) as r:
            with open(store_location, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
