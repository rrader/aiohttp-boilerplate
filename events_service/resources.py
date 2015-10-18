import trafaret as t
from aiorest.resource import ModelResource
from events_service.models import Test


class Events(ModelResource):
    model = Test
    trafaret_in = t.Dict(text=t.String(256))
    trafaret_out = t.Dict(text=t.String(), id=t.Int())

    def get_path(self):
        return r'/test'
