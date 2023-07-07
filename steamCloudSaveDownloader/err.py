import sys
from enum import IntEnum
import logging

logger = logging.getLogger('scsd')

class err_enum(IntEnum):
    CANNOT_RETRIEVE_LIST = 1
    CANNOT_PARSE_LIST = 2
    CANNOT_RETRIEVE_GAME_FILES = 3
    CANNOT_PARSE_GAME_FILES = 4
    CANNOT_INITIALIZE_DB = 5
    CANNOT_CREATE_DIRECTORY = 6
    INVALID_WEBHOOK_URL = 7
    INVALID_COOKIE_FORMAT = 8,
    INVALID_CONFIG = 9,
    LOGIN_FAIL = 10,
    NO_SESSION = 11,
    CANNOT_REMOVE_OUTDATED = 12,
    REQUESTS_LIMIT_EXCEED = 13,
    LOCKED = 14,
    UNKNOWN_EXCEPTION = 256

ERR_INFO = {
    err_enum.CANNOT_RETRIEVE_LIST: [
        logging.ERROR,
        "Cannot retrieve list from Steam. Please make sure connected to Internet."
    ],
    err_enum.CANNOT_PARSE_LIST: [
        logging.ERROR,
        "Cannot parse the list. (Session expired or program outdated)"
    ],
    err_enum.CANNOT_RETRIEVE_GAME_FILES: [
        logging.ERROR,
        "Cannot get game files."
    ],
    err_enum.CANNOT_PARSE_GAME_FILES: [
        logging.ERROR,
        "Cannot parse the file list. It seems like Steam has update the webpage. Please update to the latest version or notify the author."
    ],
    err_enum.CANNOT_INITIALIZE_DB: [
        logging.ERROR,
        "Cannot initialize database"
    ],
    err_enum.CANNOT_CREATE_DIRECTORY: [
        logging.ERROR,
        "Cannot create directory"
    ],
    err_enum.INVALID_WEBHOOK_URL: [
        logging.ERROR,
        "Invalid webhook url"
    ],
    err_enum.INVALID_COOKIE_FORMAT: [
        logging.ERROR,
        "Invalid cookie format. Should be Netscape format"
    ],
    err_enum.INVALID_CONFIG: [
        logging.ERROR,
        "Invalid config format: "
    ],
    err_enum.LOGIN_FAIL: [
        logging.ERROR,
        "Login fail, please try again"
    ],
    err_enum.NO_SESSION: [
        logging.ERROR,
        "No session found. Please re-run the program with -a <username> first"
    ],
    err_enum.CANNOT_REMOVE_OUTDATED: [
        logging.WARNING,
        "Cannot remove outdated file: "
    ],
    err_enum.REQUESTS_LIMIT_EXCEED: [
        logging.ERROR,
        "Request limit exceed. Please wait until another day"
    ],
    err_enum.LOCKED: [
        logging.ERROR,
        "Cannot create lock file. Please check if another instance is running or delete if program exit unexpectedly last time."
    ],
    err_enum.UNKNOWN_EXCEPTION: [
        logging.ERROR,
        "Unknown exception"
    ]
}


class err(Exception):
    def log(self):
        msg = self.message
        if self.additional_info:
            msg += self.additional_info
        if self.level == logging.ERROR:
            logger.error(msg)
        elif self.level == logging.WARNING:
            logger.warning(msg)
        elif self.level == logging.INFO:
            logger.info(msg)
        else:
            logger.debug(msg)

    def get_msg(err_enum: err_enum) -> str:
        return ERR_INFO[err_enum][1]

    def get_msg(self) -> str:
        if self.additional_info is None:
            return self.message
        else:
            return self.message + self.additional_info

    def num(self):
        return self.err_enum.value

    def __init__(self, err_enum_:err_enum):
        self.err_enum = err_enum_
        self.message = ERR_INFO[self.err_enum][1]
        self.level = ERR_INFO[self.err_enum][0]
        self.additional_info = None
        super().__init__(self.message)

    def set_additional_info(self, info:str):
        self.additional_info = info
