from enum import Enum
from .err import err
from .err import err_enum
import logging
from discord_webhook import DiscordWebhook
import importlib.metadata

__version__ = None
try:
    __version__ = importlib.metadata.version("scsd")
except:
    pass

logger = logging.getLogger(__name__)

class notify_method(Enum):
    Nop = 0
    Discord = 1

class notifier:

    '''
    Method: Nop (Do nothing)
    Method: Discord
        Required: webhook
    '''
    instance = None

    def get_enum(name:str):
        if name.lower() == 'discord':
            return notify_method.Discord
        else:
            return None

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
        if (self.method == notify_method.Discord):
            assert 'webhook' in kwargs, 'Discord method requires webhook'
            self.webhook = kwargs['webhook']

            if len(self.webhook) == 0:
                logger.error(err.get_msg(err_enum.INVALID_WEBHOOK_URL))
                exit(1)
        else:
            assert False, 'Unsupported notifier method'

    def discord_send(self, msg:str):
        webhook = DiscordWebhook(url=self.webhook, content=msg)
        webhook = webhook.execute()

    def send(self, msg:str, ok:bool):
        if __version__ is None:
            actual_msg = f'[scsd] '
        else:
            actual_msg = f'[scsd-{__version__}] '
        if ok:
            actual_msg += ":white_check_mark: "
        else:
            actual_msg += ":x: "
        actual_msg += f' {msg}'
        if self.method == notify_method.Discord:
            self.discord_send(actual_msg)
        else:
            assert False
