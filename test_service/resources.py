import asyncio
import trafaret as t
from aiorest.resource import ModelResource
from test_service.models import Test


class TestResource(ModelResource):
    model = Test
    trafaret_in = t.Dict(text=t.String(256))
    trafaret_out = t.Dict(text=t.String(), id=t.Int())

    def get_path(self):
        return r'/test'


@asyncio.coroutine
def setup(app):
    TestResource(app).register()
