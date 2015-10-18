import asyncio
from aio_manager import Command
from aiopg.sa import create_engine


class CreateTables(Command):
    """
    Creates DB tables for all models
    """
    def __init__(self, app, declarative_base, user, database, host, password):
        super().__init__('init', app)
        self.declarative_base = declarative_base
        self.user = user
        self.database = database
        self.host = host
        self.password = password

    async def create_tables(self, loop):
        engine = await create_engine(user=self.user,
                                     database=self.database,
                                     host=self.host,
                                     password=self.password,
                                     loop=loop)
        await self.declarative_base.metadata.create_all(engine)

    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.create_tables(loop))


class DropTables(Command):
    """
    Creates DB tables for all models
    """
    def __init__(self, app, declarative_base, user, database, host, password):
        super().__init__('drop_tables', app)
        self.declarative_base = declarative_base
        self.user = user
        self.database = database
        self.host = host
        self.password = password

    async def create_tables(self, loop):
        engine = await create_engine(user=self.user,
                                     database=self.database,
                                     host=self.host,
                                     password=self.password,
                                     loop=loop)
        await self.declarative_base.metadata.drop_all(engine)

    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.create_tables(loop))


def configure_manager(manager, app, declarative_base, user, database, host, password):
    manager.add_command(CreateTables(app, declarative_base,
                                     user, database,
                                     host, password))
    manager.add_command(DropTables(app, declarative_base,
                                   user, database,
                                   host, password))
