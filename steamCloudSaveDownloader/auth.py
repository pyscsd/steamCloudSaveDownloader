#import steam.webauth as wa
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

guard.generate_one_time_code = generate_one_time_code_override

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
        print("2FA code on Steam Authenticator (Please get the 5 digits code manually)")
        self.two_factor_code = input("2FA code (case insensitive): ")
        self.two_factor_code = self.two_factor_code.upper()
        try:
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
