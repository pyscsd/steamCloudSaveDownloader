#import steam.webauth as wa
from http import HTTPStatus
from steampy.login import LoginExecutor
from steampy import guard
import requests
from .err import err
from .err import err_enum
import pathlib
import os
import pickle
import getpass

def generate_one_time_code_override(p_input):
    return p_input

def _update_steam_guard_override(self, login_response: requests.Response) -> None:
    client_id = login_response.json()['response']['client_id']
    steamid = login_response.json()['response']['steamid']
    request_id = login_response.json()['response']['request_id']
    code_type = 2
    code = guard.generate_one_time_code(self.shared_secret)

    update_data = {'client_id': client_id, 'steamid': steamid, 'code_type': code_type, 'code': code}
    response = self._api_call(
        'POST', 'IAuthenticationService', 'UpdateAuthSessionWithSteamGuardCode', params=update_data
    )
    if response.status_code == HTTPStatus.OK:
        self._pool_sessions_steam(client_id, request_id)
    else:
        raise Exception('Cannot update Steam guard')

guard.generate_one_time_code = generate_one_time_code_override
LoginExecutor._update_steam_guard = _update_steam_guard_override

class auth:
    s_session_filename = 'session.sb'
    def __init__(self, data_dir:pathlib.Path):
        self.data_dir = data_dir

    def new_session(self, username:str):
        self.session = requests.Session()
        self.username = username

        print("This program will NOT save your credential locally")
        print(f'Username: {self.username}')

        self.password = getpass.getpass()

        try:
            login_executor = LoginExecutor(
                self.username,
                self.password,
                "")
            login_executor.login()
        except:
            pass
        print("2FA code on Steam Authenticator (Please get the 5 digits code manually)")
        self.two_factor_code = input("2FA code (case insensitive): ")
        self.two_factor_code = self.two_factor_code.upper()
        try:
            self.session = requests.Session()
            login_executor = LoginExecutor(
                self.username,
                self.password,
                self.two_factor_code,
                self.session)
            login_executor.login()
        except:
            raise err(err_enum.LOGIN_FAIL)

        prev_umask = os.umask(0O0077)
        with open(self.get_session_path(), 'wb') as f:
            pickle.dump(self.session.cookies, f)
        os.umask(prev_umask)
        print("Login success. Please rerun scsd to start downloading")

    def get_session_path(self):
        return os.path.join(self.data_dir, auth.s_session_filename)
