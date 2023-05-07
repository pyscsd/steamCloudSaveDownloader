import argparse
import os
import pathlib
import logging

class args:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
            default=15,
            help="The amount of version for each file to keep"
        )

        self.parser.add_argument(
            "-l",
            metavar="log_level",
            dest="log_level",
            type=int,
            default=2,
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
        return vars(parsed_args)

    def is_path(self, arg):
        if os.path.isdir(arg):
            return pathlib.Path(arg)
        else:
            self.parser.error(f"The directory '{arg}' does not exist.")

