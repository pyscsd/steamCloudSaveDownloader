import pytest
import pickle
import requests
from steamCloudSaveDownloader.web import web

class DummyLoginExecutor:
    def __init__(self, session):
        self.session = session

def test_web_initialization_sets_timezone_cookie(tmp_path):
    # Create a dummy login executor pickle
    dummy_session = requests.Session()
    dummy_session.cookies.set('dummy_cookie', 'dummy_value', domain='store.steampowered.com')

    dummy_pkl = tmp_path / "session.sb"
    with open(dummy_pkl, 'wb') as f:
        pickle.dump(DummyLoginExecutor(dummy_session), f)

    # Initialize web
    w = web(login_executor_pkl=str(dummy_pkl), wait_interval=(0, 0))

    # Assert original cookies are preserved
    assert w.session.cookies.get('dummy_cookie', domain='store.steampowered.com') == 'dummy_value'

    # Assert timezoneOffset cookie is injected to force true UTC
    assert w.session.cookies.get('timezoneOffset', domain='store.steampowered.com') == '0,0'
