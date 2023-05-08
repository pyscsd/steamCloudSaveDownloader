import argparse
import os
import pathlib
import logging
from .notifier import notifier
from . import config

class args:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        # Config file has highest priority
        self.parser.add_argument(
            "-f",
            metavar="conf",
            dest="conf",
            type=self.is_file,
            default="",
            help="Path to config file. If given, use the settings and ignroe all command arguments"
        )

        options, remainder = self.parser.parse_known_args()

        # Break if config file is given
        if options.conf is not None:
            return

        self.parser.add_argument(
            "-c",
            metavar="cookie_file",
            dest="cookie",
            type=argparse.FileType('r'),
            required=True,
            help="Netscape HTTP Cookie File of store.steampowered.com"
        )

        self.parser.add_argument(
            "-d",
            metavar="save_dir",
            dest="save_dir",
            type=self.is_path,
            required=True,
            help="Directory to save the downloaded saves and db"
        )

        self.parser.add_argument(
            "-r",
            metavar="rotation_count",
            dest="rotation",
            type=int,
            default=config.Defaults['rotation'],
            help="The amount of version for each file to keep"
        )

        self.parser.add_argument(
            "-l",
            metavar="log_level",
            dest="log_level",
            type=int,
            default=config.Defaults['log_level'],
            help="How detail should the log be"
        )

        self.parser.add_argument(
            "-n",
            metavar="notifier",
            dest="notifier",
            type=self.supported_notifier,
            default=config.Defaults['notifier'],
            help="Supported notifier: Discord"
        )

        self.parser.add_argument(
            "--webhook",
            metavar="webhook",
            dest="webhook",
            default=config.Defaults['webhook'],
            required=False,
            help="Notifier option"
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
