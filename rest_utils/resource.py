import asyncio
import json
import http.client
from abc import ABCMeta, abstractmethod
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound, HTTPForbidden
from trafaret import DataError
from rest_utils.response import JSONResponse
from rest_utils.validator import ModelValidator, ModelSerializer


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


class UpdateMixin(BaseResource, metaclass=ABCMeta):
    update_routename = None

    def register(self):
        super().register()
        path_ident = self.get_path() + r'/{ident}'
        self.app.router.add_route('PUT', path_ident,
                                  self.update, name=self.update_routename)

    @abstractmethod
    @asyncio.coroutine
    def update(self, request):
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


class DeleteMixin(BaseResource, metaclass=ABCMeta):
    delete_routename = None

    def register(self):
        super().register()
        path_ident = self.get_path() + r'/{ident}'
        self.app.router.add_route('DELETE', path_ident,
                                  self.delete, name=self.delete_routename)

    @abstractmethod
    @asyncio.coroutine
    def delete(self, request):
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
               UpdateMixin,
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
    permissions = []

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

    @asyncio.coroutine
    def get_instance(self, request, ident):
        with (yield from self.get_engine()) as conn:
            result = yield from conn.execute(
                self.base_query(request).where(self.lookup_key == ident)  # TODO: via metadata??
            )
            instance = yield from result.fetchone()
        return instance

    @property
    def singlename(self):
        return self.model.__name__.lower()

    @property
    def pluralname(self):
        return self.singlename + "s"

    @property
    def validator(self):
        return ModelValidator(self.model)

    @property
    def serializer(self):
        return ModelSerializer(self.model)

    list_serializer = serializer

    def base_query(self, request):
        return self.model.__table__.select()

    @property
    def lookup_key(self):
        return self.model.__table__.c.id  # TODO: go through columns and find primary key

    @asyncio.coroutine
    def check_permissions(self, request):
        if not all(p.check(request) for p in self.permissions):
            raise HTTPForbidden()


class CreateModelMixin(CreateMixin):
    @asyncio.coroutine
    def create(self, request):
        yield from self.check_permissions(request)
        data = yield from request.json()
        data = self.validate(data)

        created_id = yield from self.perform_create(request, data)
        if hasattr(self, 'get_routename'):
            response = web.Response(
               status=http.client.CREATED)
            created_path = self.app.router[self.get_routename].\
                url(parts={'ident': created_id})
            location = "{}://{}{}".format(request.scheme, request.host, created_path)
            response.headers.extend({'Location': location})
        else:
            instance = yield from self.get_instance(request, created_id)
            data = self.serialize(dict(instance))
            data.pop('id')  # anyway retrieve method is not allowed
            response = JSONResponse(
                data,
                status=http.client.CREATED)
        return response

    @asyncio.coroutine
    def perform_create(self, request, data):
        with (yield from self.get_engine()) as conn:
            results = yield from conn.execute(
                self.model.__table__.insert().values(**data)
            )
            created_id = yield from results.scalar()
        return created_id

    @property
    def create_routename(self):
        return '{}-create'.format(self.singlename)


class UpdateModelMixin(UpdateMixin):
    @asyncio.coroutine
    def update(self, request):
        yield from self.check_permissions(request)
        id_ = request.match_info['ident']
        data = yield from request.json()
        data = self.validate(data)

        yield from self.perform_update(request, id_, data)
        if hasattr(self, 'get_routename'):
            response = web.Response(
               status=http.client.OK)
            updated_path = self.app.router[self.get_routename].\
                url(parts={'ident': id_})
            location = "{}://{}{}".format(request.scheme, request.host, updated_path)
            response.headers.extend({'Location': location})
        else:
            instance = yield from self.get_instance(request, id_)
            data = self.serialize(dict(instance))
            data.pop('id')  # anyway retrieve method is not allowed
            response = JSONResponse(
                data,
                status=http.client.OK)
        return response

    @asyncio.coroutine
    def perform_update(self, request, id_, data):
        with (yield from self.get_engine()) as conn:
            yield from conn.execute(
                self.model.__table__.update().where(self.lookup_key == id_).values(**data)
            )

    @property
    def update_routename(self):
        return '{}-update'.format(self.singlename)


class RetrieveModelMixin(RetrieveMixin):
    @asyncio.coroutine
    def get(self, request):
        yield from self.check_permissions(request)
        ident = request.match_info['ident']
        instance = yield from self.get_instance(request, ident)

        if not instance:
            raise HTTPNotFound(text=json.dumps({'id': ident}))

        instance = dict(instance)
        instance = self.serialize(dict(instance))
        data = json.dumps(instance).encode()
        return JSONResponse(
               data,
               status=http.client.OK)

    @property
    def get_routename(self):
        return '{}-get'.format(self.singlename)


class DeleteModelMixin(DeleteMixin):
    @asyncio.coroutine
    def delete(self, request):
        yield from self.check_permissions(request)
        ident = request.match_info['ident']
        instance = yield from self.get_instance(request, ident)

        if not instance:
            raise HTTPNotFound(text=json.dumps({'id': ident}))

        yield from self.perform_delete(request, ident)
        return JSONResponse(status=http.client.OK)

    @asyncio.coroutine
    def perform_delete(self, request, id_):
        with (yield from self.get_engine()) as conn:
            yield from conn.execute(
                self.model.__table__.delete().where(self.lookup_key == id_)
            )

    @property
    def delete_routename(self):
        return '{}-delete'.format(self.singlename)


class ListModelMixin(ListMixin):
    page_size = 10

    @asyncio.coroutine
    def list(self, request):
        yield from self.check_permissions(request)
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('count', self.page_size))

        order_by = request.GET.get('order_by', '')
        if order_by:
            order_column = self.model.__mapper__.columns[order_by.strip('-')]
            if order_by.startswith('-'):
                order_column = order_column.desc()

        query = self.base_query(request).offset(offset).limit(limit + 1)
        if order_by:
            query = query.order_by(order_column)
        with (yield from self.get_engine()) as conn:
            result = yield from conn.execute(query)
            instances = yield from result.fetchall()

        has_next = len(instances) > limit
        if has_next:
            del instances[-1]
        page = [self.list_serializer.serialize(dict(instance))
                for instance in instances]

        data = {self.pluralname: page,
                'has_next': has_next,
                'count': len(page),
                'offset': offset}
        if has_next:
            next_path = self.app.router[self.list_routename].\
                url(query={'count': limit, 'offset': offset + limit})
            next_url = "{}://{}{}".format(request.scheme, request.host, next_path)
            data.update({'next': next_url})
        return JSONResponse(
               data,
               status=http.client.OK)

    @property
    def list_routename(self):
        return '{}-list'.format(self.singlename)


class ModelResource(CreateModelMixin,
                    UpdateModelMixin,
                    RetrieveModelMixin,
                    DeleteModelMixin,
                    ListModelMixin,
                    ModelBaseResource):
    pass
