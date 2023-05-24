import configparser
import os
import pathlib
from .err import err
from .err import err_enum
from .notifier import notifier, notify_method

Defaults = {
    'Required': {
    },
    'Rotation': {
        "rotation": 15
    },
    'Log': {
        "log_level": 2
    },
    'Notifier': {
        "notifier": "",
        "webhook": ""
    },
    'Target': {
        "mode": None,
        "list": None
    }
}

class config:
    def raise_err(self, additional_info=""):
        self.parse_error.set_additional_info(additional_info)
        raise self.parse_error
    def __init__(self, file=None):
        self.parse_error = err(err_enum.INVALID_CONFIG)

        self.config_file = file
        self.parser = configparser.ConfigParser()

        if self.config_file is not None:
            try:
                self.parser.read(self.config_file)
            except configparser.MissingSectionHeaderError as e:
                self.raise_err("[PLACEHOLDER_TEXT] section required for entire file")
        else:
            self.parser = None

        self.parsed = dict()
        for key in Defaults.keys():
            self.parsed[key] = dict()

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

    def load_default(self, p_section:str, p_entry:str):
        self.parsed[p_section][p_entry] = Defaults[p_section][p_entry]

    def parse_required(self):
        if 'Required' not in self.parser:
            self.raise_err("No [Required] section found")
        required = self.parser['Required']

        self.check_and_raise(required, 'save_dir')
        self.parsed['Required']['save_dir'] = self.is_path(required['save_dir'])

    def parse_optional_section(self, p_section:str, p_entries:list):
        if self.parser is not None and p_section in self.parser:
            section = self.parser[p_section]
        else:
            section = dict()

        for entry in p_entries:
            if entry in section:
                self.parsed[p_section][entry] = section[entry]
            else:
                self.load_default(p_section, entry)

    def parse_log(self):
        self.parse_optional_section('Log', ['log_level'])

    def parse_rotation(self):
        self.parse_optional_section('Rotation', ['rotation'])

    def parse_notifier(self):
        self.parse_optional_section('Notifier', ['notifier', 'webhook'])
        if not notifier.is_supported(self.parsed['Notifier']['notifier']):
            self.raise_err(f"Unsupported notifier method '{self.parsed['Notifier']['notifier']}'")

    def delimit_list(self, p_input:str) -> list:
        if p_input is None:
            return None
        return [int(x) for x in p_input.strip().split(',')]

    def parse_target(self):
        self.parse_optional_section('Target', ['mode', 'list'])
        self.parsed['Target']['list'] = self.delimit_list(self.parsed['Target']['list'])

    def get_conf(self):
        self.parse_required()
        self.parse_log()
        self.parse_rotation()
        self.parse_notifier()
        self.parse_target()
        return self.parsed

    def load_from_arg(self, parsed_args:dict):
        self.parsed['Required']['save_dir'] = parsed_args['save_dir']
        self.parse_log()
        self.parsed['Log']['log_level'] = parsed_args['log_level']
        self.parse_rotation()
        self.parsed['Rotation']['rotation'] = parsed_args['rotation']
        self.parse_notifier()
        self.parse_target()
        if 'auth' in parsed_args:
            self.parsed['auth'] = parsed_args['auth']
        return self.parsed
