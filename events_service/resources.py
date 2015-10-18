import asyncio
from aiohttp import web
from aiorest.resource import Resource


class Events(Resource):
    def get_path(self):
        return r'/events'

    @asyncio.coroutine
    def get(self, request, ident):
        text = "Hello world"
        return web.Response(body=text.encode('utf-8'))

    @asyncio.coroutine
    def create(self, request):
        text = "Hello world"
        return web.Response(body=text.encode('utf-8'))

    @asyncio.coroutine
    def list(self, request):
        text = "Hello world"
        return web.Response(body=text.encode('utf-8'))
