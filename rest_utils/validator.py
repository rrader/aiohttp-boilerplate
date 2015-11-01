import sqlalchemy.sql.sqltypes
import trafaret as t
from trafaret.contrib.rfc_3339 import DateTime


class BaseFieldBuilder:
    def __init__(self, column):
        self.column = column

    def build_key(self, kwargs):
        return kwargs

    def build_val(self, kwargs):
        return kwargs

    def build_trafaret(self, trafaret, kwargs):
        return trafaret


class GenericFieldValidatorBuilder(BaseFieldBuilder):
    """ Provides default implementation of trafaret generation
    for basic SQLAlchemy data types.
    """

    def build_key(self, kwargs):
        assert kwargs is None, "GenericFieldBuilder should be first in builders list"
        return {}

    def build_val(self, kwargs):
        assert kwargs is None, "GenericFieldBuilder should be first in builders list"
        return {}

    def build_trafaret(self, trafaret, kwargs):
        assert trafaret is None, "GenericFieldBuilder should be first in builders list"
        return self.default_cut(self.column, **kwargs)

    def _enum_col(self, column, **kwargs):
        return t.Enum(*column.type.enums, **kwargs)

    def _str_col(self, column, **kwargs):
        return t.String(max_length=column.type.length, **kwargs)

    def _int_col(self, column, **kwargs):
        return t.Int(**kwargs)

    def _datetime_col(self, column, **kwargs):
        return DateTime(**kwargs)  # RFC3339

    def _bool_col(self, column, **kwargs):
        return t.StrBool(**kwargs)

    def default_cut(self, column, **kwargs):
        if isinstance(column.type, sqlalchemy.sql.sqltypes.Enum):
            trafaret = self._enum_col(column, **kwargs)
        elif isinstance(column.type, sqlalchemy.sql.sqltypes.String):
            trafaret = self._str_col(column, **kwargs)
        elif isinstance(column.type, sqlalchemy.sql.sqltypes.Integer):
            trafaret = self._int_col(column, **kwargs)
        elif isinstance(column.type, sqlalchemy.sql.sqltypes.DateTime):
            trafaret = self._datetime_col(column, **kwargs)
        elif isinstance(column.type, sqlalchemy.sql.sqltypes.Boolean):
            trafaret = self._bool_col(column, **kwargs)
        else:
            raise NotImplementedError('{} has no implementation in validator'.format(str(column.type)))
        return trafaret


class NullableFieldBuilder(BaseFieldBuilder):
    """ Treats empty value as NULL
    """
    def build_key(self, kwargs):
        kwargs.update({'optional': self.column.nullable})
        return kwargs

    def build_val(self, kwargs):
        if isinstance(self.column.type, sqlalchemy.sql.sqltypes.String) and \
           not isinstance(self.column.type, sqlalchemy.sql.sqltypes.Enum):
            kwargs.update({'allow_blank': self.column.nullable})
        return kwargs

    def build_trafaret(self, trafaret, kwargs):
        if trafaret:
            if self.column.nullable:
                trafaret |= t.Null()
                # accept empty string as None value
                trafaret |= (t.String(max_length=0, allow_blank=True) >> (lambda x: None))
        return trafaret


class PrimaryKeySkipper(BaseFieldBuilder):
    """ Treats empty value as NULL
    """
    def build_trafaret(self, trafaret, kwargs):
        if self.column.primary_key and self.column.autoincrement:
            return None
        return trafaret


class GenericFieldSerializerBuilder(GenericFieldValidatorBuilder):
    def _datetime_col(self, column, **kwargs):
        return super()._datetime_col(column, **kwargs) >> (lambda dt: dt.isoformat())


class ModelValidator:
    """ Data Validator for SQLAlchemy model. Generates Trafaret by the model definition.

    If any specific configuration should be done for model field,
    method cut_<fieldname> could be overridden.

    For example, for model Event

    class EventValidator(ModelValidator):
        def __init__(self):
            super().__init__(Event)

        def cut_provider(self, column, **kwargs):
            pass  # skip field
    """
    SKIP_PRIMARY_KEY = True # assume we have clean data without id field
                            # if not, you can set this to False in the child
    GENERIC_FIELD_TRAFARET_BUILDER = GenericFieldValidatorBuilder

    def __init__(self, model):
        self._model = model

    def get_builders(self, column):
        builders =  [self.GENERIC_FIELD_TRAFARET_BUILDER(column), NullableFieldBuilder(column)]
        if self.SKIP_PRIMARY_KEY:
            builders += [PrimaryKeySkipper(column)]
        return builders

    @property
    def _validator(self):
        if self._model is None:
            raise t.DataError('ModelValidator is not associated with model')

        fields = {}
        for column in self._model.__table__.columns.values():
            key = t.Key(column.name, **self.key_kwargs(column))
            trafaret = self.cut(column, **self.val_kwargs(column))

            if trafaret is None:  # chain node can return None to skip field
                continue
            fields[key] = trafaret
        return t.Dict(fields)

    def check(self, instance):
        """
        Validates the instance. Raises DataError if validation fails
        :param instance: dict
        :return: validated and transformed dict
        """
        return self._validator.check(instance)

    def key_kwargs(self, column):
        """ Builds trafaret key arguments
        :param column: SQLAlchemy Column
        :return: dict
        """
        kwargs = None
        for builder in self.get_builders(column):
            kwargs = builder.build_key(kwargs)
        if hasattr(self, 'key_kwargs_{}'.format(column.name)):
            kwargs = getattr(self, 'key_kwargs_{}'.format(column.name))(column, kwargs)
        return kwargs

    def val_kwargs(self, column):
        """ Builds trafaret field arguments
        :param column: SQLAlchemy Column
        :return: dict
        """
        kwargs = None
        for builder in self.get_builders(column):
            kwargs = builder.build_val(kwargs)
        if hasattr(self, 'val_kwargs_{}'.format(column.name)):
            kwargs = getattr(self, 'val_kwargs_{}'.format(column.name))(column, kwargs)
        return kwargs

    def cut(self, column, **kwargs):
        """ Builds the trafaret field
        :param column: SQLAlchemy Column
        :return: dict
        """
        trafaret = None
        for builder in self.get_builders(column):
            trafaret = builder.build_trafaret(trafaret, kwargs)
        if hasattr(self, 'cut_{}'.format(column.name)):
            trafaret = getattr(self, 'cut_{}'.format(column.name))(trafaret, column)
        return trafaret


class ModelSerializer(ModelValidator):
    SKIP_PRIMARY_KEY = False
    GENERIC_FIELD_TRAFARET_BUILDER = GenericFieldSerializerBuilder

    def serialize(self, instance):
        return self.check(instance)
