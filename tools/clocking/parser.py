from argparse import ArgumentParser
from collections.abc import Callable
from argparse import Namespace

Command = Callable[[Namespace], int]

def build_parser(clock_in: Command, clock_out: Command, status: Command, cancel: Command) -> ArgumentParser:
    """
    Returns the parser for the EPQ clock.
    """
    parser = ArgumentParser(description="Clock EPQ work into the weekly development log.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    in_parser = subcommands.add_parser("in", help="start an EPQ work session")
    in_parser.set_defaults(func=clock_in)
    out_parser = subcommands.add_parser("out", help="finish an EPQ work session")
    out_parser.set_defaults(func=clock_out)
    status_parser = subcommands.add_parser("status", help="show the active EPQ work session")
    status_parser.set_defaults(func=status)
    cancel_parser = subcommands.add_parser("cancel", help="stop the active EPQ work session")
    cancel_parser.set_defaults(func=cancel)
    
    return parser
