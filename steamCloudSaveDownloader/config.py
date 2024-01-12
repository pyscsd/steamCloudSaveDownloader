import configparser
import os
import pathlib
from .err import err
from .err import err_enum
from .notifier import notifier, notify_method

Defaults = {
    'General': {
        "save_dir": (str, "./data"),
        "2fa": (str, "mobile", ("mobile", "mail"))
    },
    'Rotation': {
        "rotation": (int, 15)
    },
    'Log': {
        "log_level": (int, 2)
    },
    'Notifier': {
        "notify_if_no_change": (bool, False),
        "notifier": (str, ""),
        "webhook": (str, ""),
        "path": (str, ""),
        "level": (int, 1)
    },
    'Target': {
        "mode": (str, ""),
        "list": (list, "")
    },
    'Danger Zone': {
        "wait_interval": (list, "3, 5")
    }
}

class config:
    def raise_err(self, additional_info=""):
        self.parse_error.set_additional_info(additional_info)
        raise self.parse_error
    def __init__(self, file=None, auth=None):
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

        if auth:
            self.parsed['auth'] = auth

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

    def delimit_list(self, p_input:str) -> list:
        if p_input is None or len(p_input) == 0:
            return None
        return [int(x) for x in p_input.strip().split(',')]

    def enumeration_check(self, p_section, p_entry, p_val):
        if len(Defaults[p_section][p_entry]) != 3:
            return
        enum = Defaults[p_section][p_entry][2]

        if p_val not in enum:
            self.raise_err(f"Field '{p_entry}' should have these values '{enum}'. Got value '{p_val}' instead")

    def type_convert(self, p_entry, p_type, p_val):
        try:
            if (p_type == str):
                return str(p_val)
            elif (p_type == int):
                return int(p_val)
            elif (p_type == bool):
                return bool(p_val)
            elif (p_type == list):
                return self.delimit_list(p_val)
            else:
                assert False, 'Unsupported type'
        except ValueError as e:
            self.raise_err(f"Field '{p_entry}' of value '{p_val}' should have type '{p_type.__name__}'")


    def load_default(self, p_section:str, p_entry:str):
        tup = Defaults[p_section][p_entry]
        self.parsed[p_section][p_entry] = \
            self.type_convert(p_entry, tup[0], tup[1])

    def parse_optional_section(self, p_section:str):
        if self.parser is not None and p_section in self.parser:
            section = self.parser[p_section]
        else:
            section = dict()

        for entry in Defaults[p_section]:
            type_ = Defaults[p_section][entry][0]
            if entry in section:
                val = \
                    self.type_convert(entry, type_, section[entry])
                self.enumeration_check(
                    p_section,
                    entry,
                    val)
                self.parsed[p_section][entry] = val
            else:
                self.load_default(p_section, entry)

    def parse_general(self):
        self.parse_optional_section('General')

    def parse_log(self):
        self.parse_optional_section('Log')

    def parse_rotation(self):
        self.parse_optional_section('Rotation')

    def parse_notifier(self):
        self.parse_optional_section('Notifier')
        if not notifier.is_supported(self.parsed['Notifier']['notifier']):
            self.raise_err(f"Unsupported notifier method '{self.parsed['Notifier']['notifier']}'")

    def parse_target(self):
        self.parse_optional_section('Target')

    def parse_danger_zone(self):
        self.parse_optional_section('Danger Zone')

    def get_conf(self):
        self.parse_general()
        self.parse_log()
        self.parse_rotation()
        self.parse_notifier()
        self.parse_target()
        self.parse_danger_zone()
        return self.parsed

    def load_from_arg(self, parsed_args:dict):
        self.parse_general()
        self.parsed['General']['save_dir'] = parsed_args['save_dir']
        self.parse_log()
        self.parsed['Log']['log_level'] = parsed_args['log_level']
        self.parse_rotation()
        self.parsed['Rotation']['rotation'] = parsed_args['rotation']
        self.parse_notifier()
        self.parse_target()
        self.parse_danger_zone()
        if 'auth' in parsed_args:
            self.parsed['auth'] = parsed_args['auth']
        return self.parsed
