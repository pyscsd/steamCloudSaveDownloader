import argparse
import os
import pathlib

class args:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
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

    def parse(self, raw_args):
        parsed_args = self.parser.parse_args(raw_args)
        return vars(parsed_args)

    def is_path(self, arg):
        if os.path.isdir(arg):
            return pathlib.Path(arg)
        else:
            self.parser.error(f"The directory '{arg}' does not exist.")

