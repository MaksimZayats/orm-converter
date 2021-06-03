import inspect
import logging
import os

from abc import ABC, abstractmethod
from functools import lru_cache
from types import ModuleType
from typing import Type, Dict, Optional, List

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ImproperlyConfigured
from django.db import models as django_models
from django.db.models import Model as DjangoModel, Field as DjangoField, NOT_PROVIDED
from django.db.models import fields as django_fields

from tortoise import Model as TortoiseModel
from tortoise import fields as tortoise_fields
from tortoise.fields import Field as TortoiseField
from tortoise.fields import relational
from tortoise.fields.relational import RelationalField as RelationalTortoiseField
from tortoise.models import ModelMeta

from .utils import _dict_intersection


class IConverter(ABC):
    @classmethod
    @abstractmethod
    def convert(cls, model: type,
                **kwargs) -> Optional[type]:
        pass

    @classmethod
    @abstractmethod
    def convert_from_module(cls, module: ModuleType,
                            **kwargs) -> Optional[List[type]]:
        pass


class TortoiseToDjango(IConverter):
    FIELDS_RATIO: Dict[Type[TortoiseField], Type[DjangoField]] = {
        relational.ForeignKeyFieldInstance: django_models.ForeignKey,
        relational.OneToOneFieldInstance: django_models.OneToOneField,
        relational.ManyToManyFieldInstance: django_models.ManyToManyField,
        tortoise_fields.BigIntField: django_fields.BigIntegerField,
        tortoise_fields.BinaryField: django_fields.BinaryField,
        tortoise_fields.BooleanField: django_fields.BooleanField,
        tortoise_fields.CharField: django_fields.CharField,
        tortoise_fields.DateField: django_fields.DateField,
        tortoise_fields.DatetimeField: django_fields.DateTimeField,
        tortoise_fields.DecimalField: django_fields.DecimalField,
        tortoise_fields.FloatField: django_fields.FloatField,
        tortoise_fields.IntField: django_fields.IntegerField,
        tortoise_fields.JSONField: JSONField,
        tortoise_fields.SmallIntField: django_fields.SmallIntegerField,
        tortoise_fields.TextField: django_fields.TextField,
        tortoise_fields.UUIDField: django_fields.UUIDField,
    }

    @classmethod
    @lru_cache
    def convert(cls, model: Type[TortoiseModel],
                app_name: Optional[str] = None,
                models_file: Optional[str] = None,
                **fields: DjangoField) -> Optional[Type[DjangoModel]]:
        from_file = inspect.getfile(inspect.currentframe().f_back)
        _app_name = app_name or from_file.split(os.sep)[-2]
        _models_file_name = models_file or from_file.split(os.sep)[-1]

        _fields: Dict[str, DjangoField] = {}

        for field_name, field_type in model._meta.fields_map.items():
            if field_name == 'id' and model._meta.pk is field_type:
                continue
            if field_name not in fields:
                _fields[field_name] = cls._get_django_field(field_type)

        _fields |= fields

        try:
            return cls._generate_django_model(
                model_name=model.__name__,
                app_name=_app_name,
                models_file=_models_file_name,
                db_table=model._meta.db_table,
                fields=_fields)
        except ImproperlyConfigured:
            return None

    @classmethod
    @lru_cache
    def convert_from_module(cls, module: ModuleType,
                            exclude_models: List[Type[TortoiseModel]] = None,
                            app_name: Optional[str] = None,
                            models_file: Optional[str] = None):
        from_file = inspect.getfile(inspect.currentframe().f_back)
        _app_name = app_name or from_file.split(os.sep)[-2]
        _models_file_name = models_file or from_file.split(os.sep)[-1]

        module_members = inspect.getmembers(module)
        for member in module_members:
            if exclude_models and member[1] in exclude_models:
                continue
            if inspect.isclass(member[1]):
                if type(member[1]) is ModelMeta:
                    if getattr(member[1], '_meta', {}) and \
                            getattr(member[1]._meta, 'fields_map', {}):
                        cls.convert(
                            model=member[1],
                            app_name=_app_name,
                            models_file=_models_file_name)

    @classmethod
    def _generate_django_model(cls, model_name: str,
                               app_name: str,
                               db_table: str,
                               fields: Dict[str, DjangoField],
                               models_file: str = 'models') -> Type[DjangoModel]:
        models_file = models_file.rstrip('.py')
        meta = cls._generate_django_model_meta(
            db_table=db_table, app_label=app_name)

        django_model_attrs = {
            '__module__': f'{app_name}.{models_file}',
            'Meta': meta,
            **fields
        }

        return type(model_name, (DjangoModel,), django_model_attrs)  # type: ignore

    @classmethod
    def _generate_django_model_meta(cls, db_table: str,
                                    app_label: str) -> 'DjangoModel.Meta':
        _db_table = db_table
        _app_label = app_label

        class Meta:
            db_table = _db_table
            app_label = _app_label

        return Meta

    @classmethod
    def _get_django_field_type(cls, tortoise_field: TortoiseField) -> Type[DjangoField]:
        field = cls.FIELDS_RATIO.get(type(tortoise_field))
        if field is None:
            raise ValueError(f'{tortoise_field} is not supported')

        return field

    @classmethod
    def _get_django_field(cls, tortoise_field: TortoiseField) -> DjangoField:
        django_field = cls._get_django_field_type(tortoise_field)

        if isinstance(tortoise_field, RelationalTortoiseField):
            tortoise_field.to = getattr(tortoise_field, 'model_name').split('.')[1]
            tortoise_field.on_delete = cls._get_on_delete_function(tortoise_field.on_delete)  # type: ignore

        tortoise_field.primary_key = getattr(tortoise_field, 'pk', False)
        tortoise_field.verbose_name = getattr(tortoise_field, 'description', None)

        if getattr(tortoise_field, 'default') is None:
            tortoise_field.default = NOT_PROVIDED

        '''
        if tortoise_field.validators:
            # tortoise_field.validators = []
            tortoise_field.validators = \
                [validator.__call__ for validator in tortoise_field.validators]
        '''
        delattr(tortoise_field, 'validators')

        args =\
            set(inspect.getfullargspec(django_field).args) |\
            set(inspect.getfullargspec(DjangoField).args)

        kwargs = _dict_intersection(tortoise_field.__dict__, dict(zip(args, args)))

        logging.debug(f'Create Field\n'
                      f'Tortoise Field: {tortoise_field}\n'
                      f'New Field args: {kwargs}\n')

        return django_field(**kwargs)

    @classmethod
    def _get_on_delete_function(cls, function_name: str) -> callable:
        function_name = function_name.upper().strip()
        if function_name == 'CASCADE':
            return django_models.CASCADE
        elif function_name == 'RESTRICT':
            return django_models.RESTRICT
        elif function_name == 'SET NULL':
            return django_models.SET_NULL
        elif function_name == 'SET DEFAULT':
            return django_models.SET_DEFAULT
