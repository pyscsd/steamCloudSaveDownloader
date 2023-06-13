import argparse
import os
import pathlib
import logging
from .notifier import notifier
from . import config
from . import ver

class args:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        self.parser.add_argument(
            "-f",
            metavar="conf",
            dest="conf",
            type=self.is_file,
            default="",
            help="Path to config file. If given, use the settings and ignore all command arguments"
        )

        self.parser.add_argument(
            "-a",
            metavar="username",
            type=str,
            dest="auth",
            help="Save authentication"
        )

        self.parser.add_argument(
            "-v",
            "--version",
            dest="version",
            action='version',
            version='%(prog)s-{version}'.format(version=ver.__version__)
        )

        self.parser.add_argument(
            "-d",
            metavar="save_dir",
            dest="save_dir",
            type=self.is_path,
            help="Directory to save the downloaded saves and db"
        )

        self.parser.add_argument(
            "-r",
            metavar="rotation_count",
            dest="rotation",
            type=int,
            default=config.Defaults['Rotation']['rotation'][1],
            help="The amount of version for each file to keep"
        )

        self.parser.add_argument(
            "-l",
            metavar="log_level",
            dest="log_level",
            type=int,
            default=config.Defaults['Log']['log_level'][1],
            help="How detail should the log be"
        )

    def convert_log_level(level:int):
        if (level == 0):
            return logging.ERROR
        elif (level == 1):
            return logging.WARNING
        elif (level == 2):
            return logging.INFO
        else:
            return logging.DEBUG

    def parse(self, raw_args):
        parsed_args = self.parser.parse_args(raw_args)
        if not (parsed_args.conf or parsed_args.auth or parsed_args.save_dir):
            self.parser.error("Either one of -a, -d or -f is required")
        if (parsed_args.auth and not (parsed_args.save_dir or parsed_args.conf)):
            self.parser.error("Either `-d save_dir` or `-f conf` is required by -a")
        return vars(parsed_args)

    def supported_notifier(self, arg):
        if notifier.is_supported(arg):
            return arg
        else:
            self.parser.error(f"Unsupported notifier '{arg}'")

    def is_file(self, arg):
        if len(arg) == 0:
            return None
        if os.path.isfile(arg):
            return pathlib.Path(arg)
        else:
            self.parser.error(f"The config file '{arg}' does not exist.")

    def is_path(self, arg):
        if os.path.isdir(arg):
            return pathlib.Path(arg)
        else:
            self.parser.error(f"The directory '{arg}' does not exist.")
