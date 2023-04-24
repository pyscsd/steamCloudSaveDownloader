import sys
from enum import Enum

class err_enum(Enum):
    CANNOT_RETRIEVE_LIST = 1
    CANNOT_PARSE_LIST = 2
    CANNOT_RETRIEVE_GAME_FILES = 3
    CANNOT_PARSE_GAME_FILES = 4
    CANNOT_INITIALIZE_DB = 5
    CANNOT_CREATE_DIRECTORY = 6

ERR_MSG = {
    err_enum.CANNOT_RETRIEVE_LIST: "Cannot retrieve list from steam. Please make sure connected to Internet and cookie is valid.",
    err_enum.CANNOT_PARSE_LIST: "Cannot parse the list. It seems like Steam has update the webpage. Please update to the latest version or notify the author.",
    err_enum.CANNOT_RETRIEVE_GAME_FILES: "Cannot get game files.",
    err_enum.CANNOT_PARSE_GAME_FILES: "Cannot parse the file list. It seems like Steam has update the webpage. Please update to the latest version or notify the author.",
    err_enum.CANNOT_INITIALIZE_DB: "Cannot initialize database",
    err_enum.CANNOT_CREATE_DIRECTORY: "Cannot create directory"
}

class err(Exception):
    def __init__(self, err_enum_:err_enum):
        self.err_enum = err_enum_
        self.message = ERR_MSG[self.err_enum]
        super().__init__(self.message)

    def num(self):
        return self.err_enum.value

    def print(self):
        print(ERR_MSG[self.err_enum], file=sys.stderr)
