from http import HTTPStatus
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

# Body of the original function, instead code_type set to 2 (mail)
def _update_steam_guard_mail_override(self, login_response: requests.Response) -> None:
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

# 2025/2/14 Hotfix
from rsa import PublicKey
from steampy.exceptions import ApiException
def _fetch_rsa_params_override(self, current_number_of_repetitions: int = 0) -> dict:
    self.session.get(SteamUrl.COMMUNITY_URL)
    request_data = {'account_name': self.username}
    response = self._api_call('GET', 'IAuthenticationService', 'GetPasswordRSAPublicKey', params=request_data)

    if response.status_code == HTTPStatus.OK and 'response' in response.json():
        key_data = response.json()['response']
        # Steam may return an empty 'response' value even if the status is 200
        if 'publickey_mod' in key_data and 'publickey_exp' in key_data and 'timestamp' in key_data:
            rsa_mod = int(key_data['publickey_mod'], 16)
            rsa_exp = int(key_data['publickey_exp'], 16)
            return {'rsa_key': PublicKey(rsa_mod, rsa_exp), 'rsa_timestamp': key_data['timestamp']}

    maximal_number_of_repetitions = 5
    if current_number_of_repetitions < maximal_number_of_repetitions:
        return self._fetch_rsa_params(current_number_of_repetitions + 1)

    raise ApiException(f'Could not obtain rsa-key. Status code: {response.status_code}')
LoginExecutor._fetch_rsa_params = _fetch_rsa_params_override

def _perform_redirects_override(self, response_dict: dict) -> None:
    parameters = response_dict.get('transfer_info')
    if parameters is None:
        raise Exception('Cannot perform redirects after login, no parameters fetched')
    for pass_data in parameters:
        pass_data['params'].update({'steamID': response_dict['steamID']})
        multipart_fields = {
            key: (None, str(value))
            for key, value in pass_data['params'].items()
        }
        self.session.post(pass_data['url'], files = multipart_fields)
LoginExecutor._perform_redirects = _perform_redirects_override

from requests import Response
def _finalize_login_override(self) -> Response:
    community_domain = SteamUrl.COMMUNITY_URL[8:]
    sessionid = self.session.cookies.get_dict(domain=community_domain)['sessionid']
    redir = f'{SteamUrl.COMMUNITY_URL}/login/home/?goto='
    files = {
        'nonce': (None, self.refresh_token),
        'sessionid': (None, sessionid),
        'redir': (None, redir)
    }
    headers = {
        'Referer': redir,
        'Origin': 'https://steamcommunity.com'
    }
    return self.session.post("https://login.steampowered.com/jwt/finalizelogin", headers = headers, files = files)
LoginExecutor._finalize_login = _finalize_login_override

class auth:
    s_session_filename = 'session.sb'
    def __init__(
        self,
        data_dir:pathlib.Path,
        two_factor_method: str):
        self.data_dir = data_dir
        self.two_factor_method = two_factor_method

    def new_session(self, username:str):
        self.session = requests.Session()
        self.session.cookies.set('steamRememberLogin', 'true')
        self.username = username

        print("This program will NOT save your credential locally")
        print(f'Username: {self.username}')

        self.password = getpass.getpass()

        if self.two_factor_method == 'mail':
            LoginExecutor._update_steam_guard = \
                _update_steam_guard_mail_override
            # Trigger 2FA mail send with emtpy 2FA code
            login_executor = LoginExecutor(
                self.username,
                self.password,
                "",
                requests.Session())
            try:
                login_executor.login()
            except:
                pass

        print("2FA code on Steam Authenticator (Please get the 5 digits code manually)")
        self.two_factor_code = input("2FA code (case insensitive): ")
        self.two_factor_code = self.two_factor_code.upper()
        try:
            self.login_executor = LoginExecutor(
                self.username,
                self.password,
                self.two_factor_code,
                self.session)
            sess = self.login_executor.login()
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
        if not os.path.isfile(self.get_session_path()):
            raise err(err_enum.NO_SESSION)

        logger.info('Refreshing session')

        with open(self.get_session_path(), 'rb') as f:
            self.login_executor = pickle.load(f)

        self.login_executor._perform_redirects(self.login_executor._finalize_login().json())

        with open(self.get_session_path(), 'wb') as f:
            pickle.dump(self.login_executor, f)
