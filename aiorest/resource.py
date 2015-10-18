import asyncio
import json
import http
from abc import ABCMeta, abstractmethod
from aiohttp.web_exceptions import HTTPBadRequest, HTTPCreated
from aiorest.response import JSONResponse
import trafaret


class BaseResource:
    def __init__(self, app):
        self.app = app

    def register(self):
        pass


class CreateMixin(BaseResource, metaclass=ABCMeta):
    def register(self):
        super().register()
        self.app.router.add_route('POST', self.get_path(), self.create)

    @abstractmethod
    @asyncio.coroutine
    def create(self, request):
        pass


class RetrieveMixin(BaseResource, metaclass=ABCMeta):
    def register(self):
        super().register()
        path_ident = self.get_path() + r'/{ident}'
        self.app.router.add_route('GET', path_ident, self.get)

    @abstractmethod
    @asyncio.coroutine
    def get(self, request):
        pass


class ListMixin(BaseResource, metaclass=ABCMeta):
    def register(self):
        super().register()
        self.app.router.add_route('GET', self.get_path(), self.list)

    @abstractmethod
    @asyncio.coroutine
    def list(self, request):
        pass


class Resource(CreateMixin,
               RetrieveMixin,
               ListMixin,
               BaseResource):
    def register(self):
        super().register()

    @abstractmethod
    def get_path(self):
        pass


# Model resources

class ModelBaseResource(BaseResource):
    model = None
    trafaret_in = None
    trafaret_out = None

    def register(self):
        if self.model is None:
            raise Exception('model should be specified for ModelResource')
        if 'sa_engine' not in self.app:
            raise Exception('sa_engine should be specified in Application')
        super().register()

    def get_engine(self):
        return self.app['sa_engine']

    def validate(self, trafaret, instance):
        if trafaret is not None:
            try:
                instance = trafaret.check(instance)
            except trafaret.DataError as e:
                raise HTTPBadRequest(text=json.dumps(e.as_dict()))
        return instance

    @property
    def pluralname(self):
        return self.model.__name__.lower() + "s"


class CreateModelMixin(CreateMixin):
    @asyncio.coroutine
    def create(self, request):
        data = yield from request.json()
        data = self.validate(self.trafaret_in, data)

        with (yield from self.get_engine()) as conn:
            yield from conn.execute(
                self.model.__table__.insert().values(**data)
            )
        return JSONResponse(
               data,
               status=http.HTTPStatus.CREATED.value)


class RetrieveModelMixin(RetrieveMixin):
    @asyncio.coroutine
    def get(self, request):
        ident = request.match_info['ident']
        with (yield from self.get_engine()) as conn:
            table = self.model.__table__
            result = yield from conn.execute(
                table.select().where(table.c.id == ident)
            )
            instance = yield from result.fetchone()
            instance = dict(instance)

        instance = self.validate(self.trafaret_out, dict(instance))
        data = json.dumps(instance).encode()
        return JSONResponse(
               data,
               status=http.HTTPStatus.OK.value)


class ListModelMixin(ListMixin):
    @asyncio.coroutine
    def list(self, request):
        with (yield from self.get_engine()) as conn:
            table = self.model.__table__
            result = yield from conn.execute(
                table.select()
            )
            instances = []
            while True:
                instance = yield from result.fetchone()
                if not instance: break
                instance = self.validate(self.trafaret_out, dict(instance))
                instances.append(instance)
        data = {self.pluralname: instances}
        return JSONResponse(
               data,
               status=http.HTTPStatus.OK.value)


class ModelResource(CreateModelMixin,
                    RetrieveModelMixin,
                    ListModelMixin,
                    ModelBaseResource):
    pass
