import argparse
import sys
from nearuplib.net_argparser import create_net_argparser
from nearuplib.localnet import entry
from nearuplib.nodelib import setup_and_run, stop, show_logs
import os


class NearupArgParser(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Nearup',
            usage='''nearup <command> [<args>]

Commands are:
    testnet    Run a testnet node
    betanet    Run a betanet node
    devnet     Run a devnet node
    localnet   Run a network with several nodes locally
    stop       Stop the currently running node
    logs       Show logs of currently running non docker node

Run nearup <command> --help to see help for specific command
''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command', file=sys.stderr)
            parser.print_help(sys.stderr)
            exit(2)
        self.command = args.command
        getattr(self, args.command)()

    def localnet(self):
        self.args = None

    def testnet(self):
        parser = create_net_argparser(
            netname='testnet', description='Run a testnet node')
        self.args = parser.parse_args(sys.argv[2:])

    def betanet(self):
        parser = create_net_argparser(
            netname='betanet', description='Run a betanet node')
        self.args = parser.parse_args(sys.argv[2:])

    def devnet(self):
        parser = create_net_argparser(
            netname='devnet', description='Run a devnet node')
        self.args = parser.parse_args(sys.argv[2:])

    def stop(self):
        parser = argparse.ArgumentParser(
            description='Stop the currently running node')
        self.args = parser.parse_args(sys.argv[2:])

    def logs(self):
        self.args = sys.argv[2:]


if __name__ == '__main__':
    sys.argv[0] = 'nearup'
    nearup_arg_parser = NearupArgParser()
    command, args = nearup_arg_parser.command, nearup_arg_parser.args
    if command in ['devnet', 'betanet', 'testnet']:
        if args.local:
            print("Flag --local deprecated, please use --nodocker")
        nodocker = args.nodocker or args.local
        args.home = os.path.abspath(args.home)
        setup_and_run(nodocker, args.binary_path, args.image, args.home,
                      init_flags=[f'--chain-id={command}'],
                      boot_nodes=args.boot_nodes,
                      verbose=args.verbose)
    elif command == 'localnet':
        entry()
    elif command == 'stop':
        stop()
    elif command == 'logs':
        show_logs(len(args) > 0 and (
            args[0] == '-f' or args[0] == '--follow'))
