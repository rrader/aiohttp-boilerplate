from aio_manager import Command


class HelloWorld(Command):
    """
    Prints 'Hello world' message
    """
    def __init__(self, app):
        super().__init__('say_hello', app)

    def run(self, app, args):
        print('Hello world')
