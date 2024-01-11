#import steam.webauth as wa
from steampy.login import LoginExecutor
from steampy import guard
from steampy.models import SteamUrl
import requests
from .err import err
from .err import err_enum
import pathlib
import os
import pickle
import getpass
import logging

logger = logging.getLogger('scsd')

def generate_one_time_code_override(p_input):
    return p_input

guard.generate_one_time_code = generate_one_time_code_override

class auth:
    s_session_filename = 'session.sb'
    def __init__(self, data_dir:pathlib.Path):
        self.data_dir = data_dir

    def new_session(self, username:str):
        self.session = requests.Session()
        self.session.cookies.set('steamRememberLogin', 'true')
        self.username = username

        print("This program will NOT save your credential locally")
        print(f'Username: {self.username}')

        self.password = getpass.getpass()
        print("2FA code on Steam Authenticator (Please get the 5 digits code manually)")
        self.two_factor_code = input("2FA code (case insensitive): ")
        self.two_factor_code = self.two_factor_code.upper()
        try:
            self.login_executor = LoginExecutor(
                self.username,
                self.password,
                self.two_factor_code,
                self.session)
            self.login_executor.login()
        except Exception as e:
            raise err(err_enum.LOGIN_FAIL)

        prev_umask = os.umask(0O0077)
        with open(self.get_session_path(), 'wb') as f:
            pickle.dump(self.login_executor, f)
        os.umask(prev_umask)
        print("Login success. Please rerun scsd to start downloading")

    def get_session_path(self):
        return os.path.join(self.data_dir, auth.s_session_filename)

    def refresh_session(self):
        logger.info('Refreshing session')

        with open(self.get_session_path(), 'rb') as f:
            self.login_executor = pickle.load(f)

        sessionid = self.login_executor.session.cookies.get('sessionid', domain='store.steampowered.com')
        redir = f'{SteamUrl.COMMUNITY_URL}/login/home/?goto='
        finalized_data = {'nonce': self.login_executor.refresh_token, 'sessionid': sessionid, 'redir': redir}
        finalized_response = self.login_executor.session.post(SteamUrl.LOGIN_URL + '/jwt/finalizelogin', data=finalized_data)

        self.login_executor._perform_redirects(finalized_response.json())

        with open(self.get_session_path(), 'wb') as f:
            pickle.dump(self.login_executor, f)
