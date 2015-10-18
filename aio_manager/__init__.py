"""
Inspired by Flask-Script and Django's manage.py
"""

import argparse
import abc


class BaseManager:
    def __init__(self):
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    def create_parser(self):
        base_parser = argparse.ArgumentParser(add_help=True)
        subparsers = base_parser.add_subparsers()
        for command in self.commands:
            subparser = subparsers.add_parser(command.name,
                                              help=command.__doc__,
                                              add_help=True)
            command.configure_parser(subparser)
            subparser.set_defaults(command=command)
        return base_parser


class Manager(BaseManager):
    def __init__(self, app=None):
        super().__init__()
        self.app = app

        from .commands.runserver import RunServer
        self.add_command(RunServer(self.app))

    def run(self):
        parser = self.create_parser()
        parsed = parser.parse_args()
        if hasattr(parsed, 'command'):
            parsed.command.execute(parsed)
        else:
            parser.print_help()


class Command(metaclass=abc.ABCMeta):
    def __init__(self, name, app):
        self.name = name
        self.app = app

    def connect_app(self, app):
        self.app = app

    def execute(self, args):
        if self.app is None:
            raise RuntimeError("Command '{}' is not connected to Application".format(self.name))
        self.run(self.app, args)

    @abc.abstractmethod
    def run(self, app, args):
        pass

    def configure_parser(self, parser):
        pass
