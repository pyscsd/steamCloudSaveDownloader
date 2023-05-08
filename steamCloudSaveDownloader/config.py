import configparser
import os
import pathlib
from .err import err
from .err import err_enum
from .notifier import notifier

Defaults = {
    "rotation": 15,
    "log_level": 2,
    "notifier": "",
    "webhook": "",
}

class config:
    def raise_err(self, additional_info=""):
        self.parse_error.set_additional_info(additional_info)
        raise self.parse_error
    def __init__(self, file):
        self.parse_error = err(err_enum.INVALID_CONFIG)

        self.config_file = file
        self.parser = configparser.ConfigParser()
        try:
            self.parser.read(self.config_file)
        except configparser.MissingSectionHeaderError as e:
            self.raise_err("[PLACEHOLDER_TEXT] section required for entire file")
        self.parsed = dict()

    def is_file(self, arg) -> pathlib.Path:
        if os.path.isfile(arg):
            return pathlib.Path(arg)
        else:
            self.raise_err(f"File '{arg}' does not exist.")

    def is_path(self, arg) -> pathlib.Path:
        if os.path.isdir(arg):
            return pathlib.Path(arg)
        else:
            self.raise_err(f"Directory '{arg}' does not exist.")

    def check_and_raise(self, obj, entry:str):
        if entry not in obj:
            self.raise_err(f"'{entry}' required in config")

    def load_default(self, entry:str):
        self.parsed[entry] = Defaults[entry]

    def parse_required(self):
        if 'Required' not in self.parser:
            self.raise_err("No [Required] section found")
        required = self.parser['Required']

        self.check_and_raise(required, 'cookie_file')
        self.parsed['cookie_file'] = self.is_file(required['cookie_file'])

        self.check_and_raise(required, 'save_dir')
        self.parsed['save_dir'] = self.is_path(required['save_dir'])

    def parse_optional_section(self, p_section:str, p_entries:list):
        if p_section in self.parser:
            section = self.parser[p_section]
        else:
            section = dict()

        for entry in p_entries:
            if entry in section:
                self.parsed[entry] = section[entry]
            else:
                self.load_default(entry)

    def parse_log(self):
        self.parse_optional_section('Log', ['log_level'])

    def parse_rotation(self):
        self.parse_optional_section('Rotation', ['rotation'])

    def parse_notifier(self):
        self.parse_optional_section('Notifier', ['notifier', 'webhook'])
        if not notifier.is_supported(self.parsed['notifier']):
            self.raise_err(f"Unsupported notifier method '{self.parsed['notifier']}'")

    def get_conf(self):
        self.parse_required()
        self.parse_log()
        self.parse_rotation()
        self.parse_notifier()
        return self.parsed
