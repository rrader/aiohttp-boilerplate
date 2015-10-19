import asyncio
import json
import http
from abc import ABCMeta, abstractmethod
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound
from trafaret import DataError
from rest_utils.response import JSONResponse
from rest_utils.validator import ModelValidator, ValidationError, ModelSerializer


class BaseResource:
    def __init__(self, app):
        self.app = app

    def register(self):
        pass


class CreateMixin(BaseResource, metaclass=ABCMeta):
    create_routename = None

    def register(self):
        super().register()
        self.app.router.add_route('POST', self.get_path(),
                                  self.create, name=self.create_routename)

    @abstractmethod
    @asyncio.coroutine
    def create(self, request):
        pass


class RetrieveMixin(BaseResource, metaclass=ABCMeta):
    get_routename = None

    def register(self):
        super().register()
        path_ident = self.get_path() + r'/{ident}'
        self.app.router.add_route('GET', path_ident,
                                  self.get, name=self.get_routename)

    @abstractmethod
    @asyncio.coroutine
    def get(self, request):
        pass


class ListMixin(BaseResource, metaclass=ABCMeta):
    list_routename = None

    def register(self):
        super().register()
        self.app.router.add_route('GET', self.get_path(),
                                  self.list, name=self.list_routename)

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
        if 'db_engine' not in self.app:
            raise Exception('db_engine should be specified in Application')
        super().register()

    def get_engine(self):
        return self.app['db_engine']

    def validate(self, instance):
        try:
            instance = self.validator.check(instance)
        except DataError as e:
            raise HTTPBadRequest(text=json.dumps(e.as_dict()))
        return instance

    def serialize(self, instance):
        try:
            instance = self.serializer.serialize(instance)
        except DataError as e:
            raise HTTPBadRequest(text=json.dumps(e.as_dict()))
        return instance

    @property
    def singlename(self):
        return self.model.__name__.lower()

    @property
    def pluralname(self):
        return self.model.__name__.lower() + "s"

    @property
    def validator(self):
        return ModelValidator(self.model)

    @property
    def serializer(self):
        return ModelSerializer(self.model)

    list_serializer = serializer

    @asyncio.coroutine
    def get_instance(self, ident):
        with (yield from self.get_engine()) as conn:
            table = self.model.__table__
            result = yield from conn.execute(
                table.select().where(table.c.id == ident)  # TODO: via metadata??
            )
            instance = yield from result.fetchone()
        return instance


class CreateModelMixin(CreateMixin):
    @asyncio.coroutine
    def create(self, request):
        data = yield from request.json()
        # data = self.validate(self.trafaret_in, data)
        data = self.validate(data)

        with (yield from self.get_engine()) as conn:
            results = yield from conn.execute(
                self.model.__table__.insert().values(**data)
            )
            created_id = yield from results.scalar()
        response = web.Response(
               status=http.HTTPStatus.CREATED.value)
        if hasattr(self, 'get_routename'):
            created_path = self.app.router[self.get_routename].\
                url(parts={'ident': created_id})
            location = "{}://{}{}".format(request.scheme, request.host, created_path)
            response.headers.extend({'Location': location})
        return response

    @property
    def create_routename(self):
        return '{}-create'.format(self.singlename)


class RetrieveModelMixin(RetrieveMixin):
    @asyncio.coroutine
    def get(self, request):
        ident = request.match_info['ident']
        instance = yield from self.get_instance(ident)

        if not instance:
            raise HTTPNotFound(text=json.dumps({'id': ident}))
        instance = dict(instance)
        # instance = self.validate(self.trafaret_out, dict(instance))
        instance = self.serialize(dict(instance))
        data = json.dumps(instance).encode()
        return JSONResponse(
               data,
               status=http.HTTPStatus.OK.value)

    @property
    def get_routename(self):
        return '{}-get'.format(self.singlename)


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
                instance = self.list_serializer.serialize(dict(instance))
                instances.append(instance)
        data = {self.pluralname: instances}
        return JSONResponse(
               data,
               status=http.HTTPStatus.OK.value)

    @property
    def list_routename(self):
        return '{}-list'.format(self.singlename)


class ModelResource(CreateModelMixin,
                    RetrieveModelMixin,
                    ListModelMixin,
                    ModelBaseResource):
    pass
