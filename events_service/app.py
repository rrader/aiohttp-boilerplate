import asyncio
from aiohttp.web import Application
from events_service import models, resources


def build_application():
    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    loop.run_until_complete(models.setup(app))
    loop.run_until_complete(resources.setup(app))
    return app


if __name__ == "__main__":
    pass
