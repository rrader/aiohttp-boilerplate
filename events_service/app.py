import asyncio
from aiohttp.web import Application, Response, StreamResponse


def build_application():
    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    # app.router.add_route('GET', '/', intro)
    # app.router.add_route('GET', '/simple', simple)
    # app.router.add_route('GET', '/change_body', change_body)
    # app.router.add_route('GET', '/hello/{name}', hello)
    # app.router.add_route('GET', '/hello', hello)

    return app


if __name__ == "__main__":
    pass
