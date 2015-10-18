import asyncio
from abc import ABCMeta, abstractmethod


class BaseResource:
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
    def get(self, request, ident):
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
    def __init__(self, app):
        self.app = app

    def register(self):
        super().register()

    @abstractmethod
    def get_path(self):
        pass
