import asyncio
from aiohttp.web import Application
from aiopg.sa import create_engine
from events_service.resources import Events
from events_service.settings import DATABASE_HOST, DATABASE_PASSWORD,\
    DATABASE_NAME, DATABASE_USERNAME


@asyncio.coroutine
def setup(app):
    engine = yield from create_engine(user=DATABASE_USERNAME,
                                      database=DATABASE_NAME,
                                      host=DATABASE_HOST,
                                      password=DATABASE_PASSWORD)
    app['sa_engine'] = engine


def build_application():
    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    loop.run_until_complete(setup(app))
    Events(app).register()

    # app.router.add_route('GET', '/', intro)
    # app.router.add_route('GET', '/simple', simple)
    # app.router.add_route('GET', '/change_body', change_body)
    # app.router.add_route('GET', '/hello/{name}', hello)
    # app.router.add_route('GET', '/hello', hello)

    return app


if __name__ == "__main__":
    pass
