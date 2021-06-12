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

from ._utils import dict_intersection


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
                model_file: Optional[str] = None,
                **fields: DjangoField
                ) -> Optional[Type[DjangoModel]]:
        from_file = inspect.getfile(inspect.currentframe().f_back)
        app_label = app_name or from_file.split(os.sep)[-2]
        model_file_name = model_file or from_file.split(os.sep)[-1]

        tortoise_model_meta = model._meta

        for field_name, field_type in tortoise_model_meta.fields_map.items():
            if field_name == 'id' and tortoise_model_meta.pk is field_type:
                continue
            if field_name not in fields:
                fields[field_name] = cls._get_django_field(field_type)

        django_meta = cls._generate_django_model_meta(
            app_label=app_label, tortoise_meta=model.Meta)

        try:
            return cls._generate_django_model(
                model_name=model.__name__,
                model_file=model_file_name,
                model_meta=django_meta,
                fields=fields)
        except ImproperlyConfigured:
            return None

    @classmethod
    @lru_cache
    def convert_from_module(cls, module: Optional[ModuleType] = None,
                            from_current_file: bool = False,
                            exclude_models: List[Type[TortoiseModel]] = None,
                            app_name: Optional[str] = None,
                            models_file: Optional[str] = None
                            ) -> List[Optional[Type[DjangoModel]]]:
        _converter_models: List[Type[DjangoModel]] = []

        from_file = inspect.getfile(inspect.currentframe().f_back)
        app_label = app_name or from_file.split(os.sep)[-2]
        models_file_name = models_file or from_file.split(os.sep)[-1]

        if module is not None:
            module_members = inspect.getmembers(module)
        elif from_current_file:
            module = inspect.getmodule(inspect.currentframe().f_back)
            module_members = inspect.getmembers(module)
        else:
            raise ValueError('')

        for member in module_members:
            if exclude_models and member[1] in exclude_models:
                continue
            if inspect.isclass(member[1]):
                if type(member[1]) is ModelMeta:
                    if getattr(member[1], '_meta', {}) and \
                            getattr(member[1]._meta, 'fields_map', {}):
                        _converter_models.append(
                            cls.convert(
                                model=member[1],
                                app_name=app_label,
                                model_file=models_file_name))
        return _converter_models

    @classmethod
    def _generate_django_model(cls, model_name: str,
                               fields: Dict[str, DjangoField],
                               model_meta: Type['DjangoModel.Meta'],
                               model_file: str = 'models') -> Type[DjangoModel]:
        model_file = model_file.rstrip('.py')

        django_model_attrs = {
            '__module__': f'{model_meta.app_label}.{model_file}',
            'Meta': model_meta,
            **fields
        }

        return type(model_name, (DjangoModel,), django_model_attrs)  # type: ignore

    @classmethod
    def _generate_django_model_meta(cls, app_label: str,
                                    tortoise_meta: Type[TortoiseModel.Meta]
                                    ) -> Type['DjangoModel.Meta']:
        class Meta:
            db_table = getattr(tortoise_meta, 'table')

        Meta.app_label = app_label

        if getattr(tortoise_meta, 'verbose_name', None):
            Meta.verbose_name = getattr(tortoise_meta, 'verbose_name')

        if getattr(tortoise_meta, 'verbose_name_plural', None):
            Meta.verbose_name_plural = getattr(tortoise_meta, 'verbose_name_plural')

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

        kwargs = dict_intersection(tortoise_field.__dict__, dict(zip(args, args)))

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
