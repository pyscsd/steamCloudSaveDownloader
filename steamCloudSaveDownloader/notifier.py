from enum import Enum
from .err import err
from .err import err_enum
from . import ver
import logging
from discord_webhook import DiscordWebhook
import subprocess
import os

logger = logging.getLogger(__name__)

class notify_method(Enum):
    Nop = 0
    Discord = 1
    Script = 2

class notifier:

    '''
    Method: Nop (Do nothing)
    Method: Discord
        Required: webhook
    Method: Script
        Required: path
    '''
    instance = None

    def get_enum(name:str):
        if name.lower() == 'discord':
            return notify_method.Discord
        elif name.lower() == 'script':
            return notify_method.Script
        else:
            return notify_method.Nop

    def is_supported(name:str):
        if len(name) == 0:
            return True
        enum_ = notifier.get_enum(name)
        if enum_ is None:
            return False
        else:
            return True

    def get_instance():
        return notifier.instance

    def create_instance(method:str, **kwargs):
        method_enum = notifier.get_enum(method)
        notifier.instance = notifier(method_enum, **kwargs)

        return notifier.instance

    def __init__(self, method:notify_method, **kwargs):
        self.method = method
        if (self.method == notify_method.Nop):
            pass
        elif (self.method == notify_method.Discord):
            assert 'webhook' in kwargs, 'Discord method requires webhook'
            self.webhook = kwargs['webhook']

            if len(self.webhook) == 0:
                raise(err(err_enum.INVALID_WEBHOOK_URL))
        elif (self.method == notify_method.Script):
            assert 'path' in kwargs, 'Script method requires path'
            self.path = kwargs['path']

            if len(self.path) == 0 or not os.path.isfile(self.path):
                raise(err(err_enum.INVALID_SCRIPT_PATH))
        else:
            assert False, 'Unsupported notifier method'

    def discord_send(self, msg:str):
        webhook = DiscordWebhook(url=self.webhook, content=msg)
        webhook = webhook.execute()

    def script_send(self, msg:str):
        try:
            subprocess.run([self.path, msg])
        except FileNotFoundError:
            raise(err(err_enum.INVALID_SCRIPT_PATH))

    def send(self, msg:str, ok:bool) -> bool:
        actual_msg = f'[scsd-{ver.__version__}] '
        if ok:
            actual_msg += ":white_check_mark: "
        else:
            actual_msg += ":x: "
        actual_msg += f' {msg}'
        try:
            if self.method == notify_method.Nop:
                pass
            elif self.method == notify_method.Discord:
                self.discord_send(actual_msg)
            elif self.method == notify_method.Script:
                self.script_send(actual_msg)
            else:
                assert False
            return True
        except Exception as e:
            self.exception = e
            return False
