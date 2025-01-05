from .err import err
from .err import err_enum

import os

def dir_permission_checking(save_dir: str):
    err_ = err(err_enum.CANNOT_WRITE_TO_SAVE_DIR)
    err_.set_additional_info(f" `{save_dir}`")

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except:
            raise err_
    if not os.access(save_dir, os.W_OK | os.X_OK):
        raise err_
