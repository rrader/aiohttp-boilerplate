import logging
from aio_manager import Manager
from aio_manager.commands.ext import sqlalchemy
from test_service import settings
from test_service.app import build_application
from test_service.models import Base

logging.basicConfig(level=logging.WARNING)

app = build_application()
manager = Manager(app)

sqlalchemy.configure_manager(manager, app, Base,
                             settings.DATABASE_USERNAME,
                             settings.DATABASE_NAME,
                             settings.DATABASE_HOST,
                             settings.DATABASE_PASSWORD)

if __name__ == "__main__":
    manager.run()
