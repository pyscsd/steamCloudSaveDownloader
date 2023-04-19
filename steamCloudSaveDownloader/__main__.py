from . import args
from . import web

def main(argv):
    parsed_args = args.args().parse(argv)

    web_ = web.web(parsed_args['cookie'])
    print(web_.get_list())
