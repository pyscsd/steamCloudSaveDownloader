from . import err
from .err import err_enum
from .parser import web_parser
import requests
from http.cookiejar import MozillaCookieJar
import pickle # Remove After Mock
import shutil
import time
import random

g_dbg_mode = False
g_web_link = "https://store.steampowered.com/account/remotestorage/?l=english"
g_random_sleep_interval = (2, 5)

def random_sleep(func):
    def wrapper(*args, **kwargs):
        if not g_dbg_mode:
            time.sleep(random.randint(g_random_sleep_interval[0], g_random_sleep_interval[1]))
        return func(*args, **kwargs)
    return wrapper

class web:
    def __init__(self, cookie):
        self.cookie_file = cookie.name
        self.cookie = MozillaCookieJar(self.cookie_file)
        self.cookie.load()
        self.web_parser = web_parser()


    # Return list of {"Game": name, "Link", link}
    @random_sleep
    def get_list(self):
        response = None

        if (not g_dbg_mode):
            response = requests.get(g_web_link, cookies=self.cookie)
            if (response.status_code != 200):
                print(err.ERR_MSG[err_enum.ERR_CANNOT_RETRIEVE_LIST_MSG], file=sys.stderr)
                exit(err_enum.ERR_CANNOT_RETRIEVE_LIST.value)

        # --- Start of DBG Block ---
        #with open('game_list_response.pkl', 'wb') as f:
        #   pickle.dump(response, f)

        if (g_dbg_mode):
            with open('game_list_response.pkl', 'rb') as f:
                response = pickle.load(f)
        # --- End of DBG Block ---
        return self.web_parser.parse_index(response.text)

    @random_sleep
    def _get_game_save(self, game_link:str):
        response = None
        if (not g_dbg_mode):
            response = requests.get(game_link, cookies=self.cookie)
            if (response.status_code != 200):
                err.err(ERR_CANNOT_RETRIEVE_GAME_FILES).print()
                return (None, None)

        # --- Start of DBG Block ---
        #with open('game_file_response.pkl', 'wb') as f:
        #    pickle.dump(response, f)

        if g_dbg_mode:
            with open('game_file_response.pkl', 'rb') as f:
               response = pickle.load(f)
        #--- End of DBG Block ---

        return self.web_parser.parse_game_file(response.text)


    def get_game_save(self, game_link:str):
        # Some games have a lot of games with multiple pages
        next_page_link = game_link
        save_file_list = list()
        while True:
            partial_save_file_list, next_page_link = \
                self._get_game_save(next_page_link)
            save_file_list += partial_save_file_list
            if (next_page_link is None):
                break
        print(save_file_list)
        return save_file_list

    @random_sleep
    def download_game_save(self, link:str, store_location:str):
        if g_dbg_mode:
            return
        with requests.get(link, cookies=self.cookie, stream=True) as r:
            with open(store_location, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
