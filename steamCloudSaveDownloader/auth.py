import steam.webauth as wa
from .err import err
from .err import err_enum
import pathlib
import os
import pickle

class auth:
    s_session_filename = 'session.sb'
    def __init__(self, data_dir:pathlib.Path):
        self.data_dir = data_dir

    def new_session(self, username:str):
        print("This program will NOT save your credential locally")
        print("2FA codes is case SENSITIVE")
        self.username = username
        self.user = wa.WebAuth(username)
        try:
            self.session = self.user.cli_login()
        except:
            raise err(err_enum.LOGIN_FAIL)

        prev_umask = os.umask(0O0077)
        with open(self.get_session_path(), 'wb') as f:
            pickle.dump(self.session.cookies, f)
        os.umask(prev_umask)
        print("Login success. Please rerun scsd to start downloading")

    def get_session_path(self):
        return os.path.join(self.data_dir, auth.s_session_filename)
