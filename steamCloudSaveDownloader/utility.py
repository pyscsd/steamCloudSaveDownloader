from .err import err
from .err import err_enum

import os

def permission_checking(save_dir: str):
    if (os.access(save_dir, os.W_OK | os.X_OK)):
        return
    err_ = err(err_enum.CANNOT_WRITE_TO_SAVE_DIR)
    err_.set_additional_info(f" `{save_dir}`")
    raise err_
