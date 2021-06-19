import inspect
import logging
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from types import ModuleType
from typing import Type, Dict, Optional, List, Iterable, Any

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
from .exceptions import ConfigurationError, FieldIsNotSupported

from ._utils import dict_intersection

logger = logging.getLogger('orm_converter')


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
                convert_to_same_module: bool = True,
                app_name: Optional[str] = None,
                models_file: Optional[str] = None,
                module_name: Optional[str] = None,
                **redefined_fields: DjangoField
                ) -> Optional[Type[DjangoModel]]:
        """
        Convert TortoiseModel to DjangoModel.

        :param model:
            Tortoise model to convert.
        :param convert_to_same_module:
            If ``True`` models will be converted to the same module.
        :param app_name:
            App name for Django App.
            By default, this is the name of the folder from which the function is called.
        :param models_file:
            Filename in Django App to store models.
            By default, this is the name of the file from which the function is called.
        :param module_name:
            Module name to Django Model file.
            Default: {app_name}.{models_file}
        :param redefined_fields:
            Redefined DjangoModel fields.

        :return: DjangoModel or None.
        """
        if hasattr(model, 'Meta') and getattr(model.Meta, 'abstract', False):
            # Ignore abstract models
            return

        if hasattr(model, 'DjangoModel'):
            return getattr(model, 'DjangoModel')

        if hasattr(model, 'DjangoFields'):
            for name, value in model.DjangoFields.__dict__.items():
                if isinstance(value, DjangoField):
                    redefined_fields[name] = value

        if convert_to_same_module:
            if app_name is None:
                from django.apps import apps

                raw_app_name = model.__module__.split('.')
                for django_app_name in apps.app_configs.keys():
                    if django_app_name in raw_app_name:
                        app_name = django_app_name
                        break

            module_name = model.__module__

        if app_name is None:
            from_file = inspect.getfile(inspect.currentframe().f_back)
            app_name = from_file.split(os.sep)[-2]

        if module_name is None:
            if models_file is None:
                from_file = inspect.getfile(inspect.currentframe().f_back)
                models_file = from_file.split(os.sep)[-1]

            module_name = f'{app_name}.{models_file.rstrip("py")}'

        converted_fields: Dict[str, DjangoField] = {}
        tortoise_model_meta = getattr(model, '_meta')

        for field_name, field_type in tortoise_model_meta.fields_map.items():
            if field_name == 'id' and tortoise_model_meta.pk is field_type:
                continue
            if field_name not in redefined_fields.keys():
                converted_fields[field_name] = cls._get_django_field(field_type)
            else:
                converted_fields[field_name] = redefined_fields[field_name]

        django_meta = cls._generate_django_model_meta(
            app_name=app_name, tortoise_meta=model.Meta)

        try:
            converted_model = cls._generate_django_model(
                tortoise_model=model,
                model_name=model.__name__,
                module_name=module_name,
                model_meta=django_meta,
                fields=converted_fields)
            setattr(model, 'DjangoModel', converted_model)
            return converted_model
        except ImproperlyConfigured:
            return None

    @classmethod
    @lru_cache
    def convert_from_module(cls, module: Optional[ModuleType] = None,
                            from_current_module: bool = False,
                            exclude_models: Iterable[Type[TortoiseModel]] = tuple(),
                            convert_to_same_module: bool = True,
                            app_name: Optional[str] = None,
                            models_file: Optional[str] = None,
                            module_name: Optional[str] = None,
                            ) -> List[Optional[Type[DjangoModel]]]:
        """
        Converts all models from the module.

        :param module:
            The module from where the models will be converted.
        :param from_current_module:
            Sets the module equal to the module from which the function is called.
        :param exclude_models:
            Models that will not be converted.
        :param convert_to_same_module:
            Means that the conversion will take place in the same module(which is passed to the function)."
        :param app_name:
            App name for Django App.
            By default, this is the name of the folder from which the function is called.
        :param models_file:
            Filename in Django App to store models.
            By default, this is the name of the file from which the function is called.
        :param module_name:
            Module name to Django Model file.
            Default: {app_name}.{models_file}

        :return: List of DjangoModel or None
        """
        _converted_models: List[Type[DjangoModel]] = []

        if module is None:
            if from_current_module:
                module = inspect.getmodule(inspect.currentframe().f_back)
            else:
                raise ConfigurationError(
                    'You must specify either "module" or "from_current_module"'
                )

        for member in inspect.getmembers(module):
            if member[1] in exclude_models:
                continue
            if inspect.isclass(member[1]):
                if type(member[1]) is ModelMeta:
                    meta = getattr(member[1], '_meta', {})
                    fields_map = getattr(meta, 'fields_map', {})
                    if fields_map:
                        _converted_models.append(
                            cls.convert(
                                model=member[1],
                                convert_to_same_module=convert_to_same_module,
                                app_name=app_name,
                                models_file=models_file,
                                module_name=module_name))
        return _converted_models

    @classmethod
    def _generate_django_model(cls, tortoise_model: Type[TortoiseModel],
                               model_name: str,
                               fields: Dict[str, DjangoField],
                               model_meta: Type['DjangoModel.Meta'],
                               module_name: str) -> Type[DjangoModel]:
        django_model_attrs = {
            '__module__': module_name,
            '__str__': tortoise_model.__str__,
            'Meta': model_meta,
            **fields
        }

        return type(model_name, (DjangoModel,), django_model_attrs)  # type: ignore

    @classmethod
    def _generate_django_model_meta(cls, app_name: str,
                                    tortoise_meta: Type[TortoiseModel.Meta]
                                    ) -> Type['DjangoModel.Meta']:
        class Meta:
            app_label = app_name

        for name, value in tortoise_meta.__dict__.items():  # type: str, Any
            if name in ('__dict__',):
                continue

            if name == 'table':
                Meta.db_table = value
            else:
                setattr(Meta, name, value)

        return Meta

    @classmethod
    def _get_django_field_type(cls, tortoise_field: TortoiseField) -> Type[DjangoField]:
        field = cls.FIELDS_RATIO.get(type(tortoise_field))
        if field is None:
            raise FieldIsNotSupported(f'{tortoise_field} is not supported')

        return field

    @classmethod
    def _get_django_field(cls, tortoise_field: TortoiseField) -> DjangoField:
        django_field = cls._get_django_field_type(tortoise_field)
        django_field_kwargs = {**tortoise_field.__dict__}

        if isinstance(tortoise_field, RelationalTortoiseField):
            django_field_kwargs['to'] = getattr(tortoise_field, 'model_name')
            django_field_kwargs['on_delete'] = cls._get_on_delete_function(tortoise_field.on_delete)  # type: ignore

        django_field_kwargs['primary_key'] = getattr(tortoise_field, 'pk', False)
        django_field_kwargs['verbose_name'] = getattr(tortoise_field, 'description', None)

        if django_field_kwargs.get('default') is None:
            django_field_kwargs['default'] = NOT_PROVIDED

        if django_field_kwargs.get('null') is True:
            django_field_kwargs['blank'] = True

        if django_field_kwargs.get('validators'):
            django_field_kwargs.pop('validators')

        args = \
            set(inspect.getfullargspec(django_field).args) | \
            set(inspect.getfullargspec(DjangoField).args)

        django_field_kwargs = dict_intersection(django_field_kwargs, dict(zip(args, args)))

        logging.debug(f'Create Field\n'
                      f'Tortoise Field: {tortoise_field}\n'
                      f'New Field args: {django_field_kwargs}\n')

        return django_field(**django_field_kwargs)

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
