from . import err
from .err import err_enum
from .parser import web_parser
import requests
from http.cookiejar import MozillaCookieJar
import pickle # Remove After Mock

g_web_link = "https://store.steampowered.com/account/remotestorage"

class web:
    def __init__(self, cookie):
        self.cookie_file = cookie.name
        self.cookie = MozillaCookieJar(self.cookie_file)
        self.cookie.load()
        self.web_parser = web_parser()

    # Return list of {"Game": name, "Link", link}
    def get_list(self):

        response = None
        #response = requests.get(g_web_link, cookies=self.cookie)
        #if (response.status_code != 200):
        #    print(err.ERR_MSG[err_enum.ERR_CANNOT_RETRIEVE_LIST_MSG], file=sys.stderr)
        #    exit(err_enum.ERR_CANNOT_RETRIEVE_LIST.value)

        # --- Start of DBG Block ---
        #with open('game_list_response.pkl', 'wb') as f:
        #   pickle.dump(response, f)

        with open('game_list_response.pkl', 'rb') as f:
            response = pickle.load(f)
        # --- End of DBG Block ---

        return self.web_parser.parse_index(response.text)

    def get_game_save(self, game_link:str):
        response = None
        #response = requests.get(game_link, cookies=self.cookie)
        #if (response.status_code != 200):
        #    err.err(ERR_CANNOT_RETRIEVE_GAME_FILES).print()
        #    return None

        # --- Start of DBG Block ---
        #with open('game_file_response.pkl', 'wb') as f:
        #    pickle.dump(response, f)

        with open('game_file_response.pkl', 'rb') as f:
           response = pickle.load(f)
        #--- End of DBG Block ---

        return self.web_parser.parse_game_file(response.text)
