from . import err
import requests
import sys
from http.cookiejar import MozillaCookieJar
from bs4 import BeautifulSoup
import pickle # Remove After Mock

g_web_link = "https://store.steampowered.com/account/remotestorage"

class web_parser:
    def __init__(self):
        pass

    def parse_index(self, content):
        try:
            return self._parse_index(content)
        except Exception as e:
            print(err.ERR_CANNOT_PARSE_LIST_MSG, file=sys.stderr)
            exit(err.ERR_CANNOT_PARSE_LIST)

    def _parse_index(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        account_tbody = soup.find(id='main_content').table.tbody
        if (account_tbody is None):
            raise Exception()

        data = list()

        rows = account_tbody.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            data.append({"Game": cols[0].text.strip(), "Link": cols[3].a['href']})
        return data

class web:
    def __init__(self, cookie):
        self.cookie_file = cookie.name
        self.cookie = MozillaCookieJar(self.cookie_file)
        self.cookie.load()
        self.web_parser = web_parser()

    def get_list(self):

        response = None
        #response = requests.get(g_web_link, cookies=self.cookie)
        #if (response.status_code != 200):
        #    print(err.ERR_CANNOT_RETRIEVE_LIST_MSG, file=sys.stderr)
        #    exit(err.ERR_CANNOT_RETRIEVE_LIST)

        # --- Start of DBG Block ---
        #with open('response.pkl', 'wb') as f:
        #    pickle.dump(response, f)

        with open('response.pkl', 'rb') as f:
            response = pickle.load(f)
        # --- End of DBG Block ---

        return self.web_parser.parse_index(response.text)

