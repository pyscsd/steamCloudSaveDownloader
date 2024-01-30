from . import err
from .err import err_enum
from .parser import web_parser
from . import config
from enum import IntEnum
import requests
import pickle
import shutil
import time
import random
import os
import logging

g_language_specifier = "l=english"
g_web_link = f"https://store.steampowered.com/account/remotestorage/?{g_language_specifier}"
g_random_sleep_interval = (3, 5)
g_retry_count = 3

logger = logging.getLogger('scsd')

class sleep_and_retry:
    class sleep_policy_e(IntEnum):
        RANDOM = 1
        EXP = 2

    def __init__(self, sleep_policy):
        assert type(sleep_policy) == self.sleep_policy_e
        self.exp = 0
        self.sleep_policy = sleep_policy

    def random_sleep_interval(self):
        global g_random_sleep_interval
        return random.randint(
            g_random_sleep_interval[0],
            g_random_sleep_interval[1])

    def exponential_sleep_interval(self):
        val = (2 ** self.exp)
        return val

    def exponential_fail(self):
        self.exp += 1

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            if self.sleep_policy == self.sleep_policy_e.RANDOM:
                sleep_func = self.random_sleep_interval
            elif self.sleep_policy == self.sleep_policy_e.EXP:
                sleep_func = self.exponential_sleep_interval
            else:
                assert False, 'Unsupported Policy'
            exception = None
            sleep_interval = sleep_func()
            for i in range(g_retry_count):
                if sleep_interval > 1 and self.sleep_policy == self.sleep_policy_e.RANDOM:
                    logger.info(f"Random sleep for {sleep_interval} seconds")
                time.sleep(sleep_interval)
                try:
                    retval = func(*args, **kwargs)
                    return retval
                except err.err as e:
                    exception = e
                    e.log()
                    self.exponential_fail()
                    sleep_interval = sleep_func()
                    logger.info(f'Retrying in {sleep_interval} seconds')
                except requests.exceptions.ConnectionError as e:
                    exception = e
                    self.exponential_fail()
                    sleep_interval = sleep_func()
                    logger.error("Connection error")
                    logger.info(f'Retrying in {sleep_interval} seconds')
                except BaseException as e:
                    exception = e
                    self.exponential_fail()
                    sleep_interval = sleep_func()
                    logger.error(e)
                    logger.info(f'Retrying in {sleep_interval} seconds')
            logger.error(f'Maximum attempt reached. Aborting')
            raise exception

        return wrapper
class web:
    # TODO: cookie is now loginExecutor
    def __init__(self, login_executor_pkl, wait_interval):
        global g_random_sleep_interval

        if not os.path.isfile(login_executor_pkl):
            raise err.err(err_enum.NO_SESSION)

        g_random_sleep_interval = (wait_interval[0], wait_interval[1])
        self.web_parser = web_parser()
        self.session = requests.Session()
        self.login_executor_pkl = login_executor_pkl
        try:
            with open(self.login_executor_pkl, 'rb') as f:
                self.session.cookies.update(pickle.load(f).session.cookies)
        except:
            raise err.err(err_enum.INVALID_COOKIE_FORMAT)

    # Return list of {"Game": name, "Link", link}
    @sleep_and_retry(sleep_and_retry.sleep_policy_e.RANDOM)
    def get_list(self):
        response = self.session.get(g_web_link)
        if (response.status_code != 200):
            raise err.err(err_enum.CANNOT_RETRIEVE_LIST)

        return self.web_parser.parse_index(response.text)

    @sleep_and_retry(sleep_and_retry.sleep_policy_e.RANDOM)
    def _get_game_save(self, game_link:str):
        response = self.session.get(game_link)
        if (response.status_code != 200):
            err.err(err_enum.CANNOT_RETRIEVE_GAME_FILES).log()
            return (None, None)

        return self.web_parser.parse_game_file(response.text)


    def get_game_save(self, game_link:str):
        # Some games have a lot of games with multiple pages
        next_page_link = game_link
        save_file_list = list()
        while True:
            partial_save_file_list, next_page_link = \
                self._get_game_save(next_page_link)
            if partial_save_file_list is None:
                return None
            save_file_list += partial_save_file_list
            if next_page_link is None:
                break
        return save_file_list

    @sleep_and_retry(sleep_and_retry.sleep_policy_e.EXP)
    def download_game_save(self, link:str, store_location:str):
        with self.session.get(link, stream=True) as r:
            with open(store_location, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
