import steam.webauth as wa
from .err import err
from .err import err_enum
import pathlib
import os
import pickle

class auth:
    def __init__(self, username:str, data_dir:pathlib.Path):
        print(username)
        self.username = username
        self.user = wa.WebAuth(username)

        try:
            self.session = self.user.cli_login()
        except:
            raise err(err_enum.LOGIN_FAIL)

        with open(os.path.join(data_dir, 'session.sb'), 'wb') as f:
            pickle.dump(self.session.cookies, f)
