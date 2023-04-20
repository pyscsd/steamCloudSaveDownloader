import argparse

class args:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-c",
            metavar="--cookie",
            dest="cookie",
            type=argparse.FileType('r'),
            required=True
        )

    # TODO: Store dir

    def parse(self, raw_args):
        parsed_args = self.parser.parse_args(raw_args)
        return vars(parsed_args)
