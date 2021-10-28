from abc import ABC
from inspect import getfullargspec
from typing import Callable, Dict

from django.db import models as django_models
from django.db.models import NOT_PROVIDED
from django.db.models import fields as django_fields
from tortoise import fields as tortoise_fields
from tortoise.fields import relational

from orm_converter import bases
from orm_converter.shared.utils import dict_intersection


class BaseTortoiseFieldConverter(bases.BaseFieldConverter, ABC):
    @property
    def converted_field(self) -> django_fields.Field:
        return self.CONVERTED_FIELD_TYPE(**self._converted_field_kwargs)  # type: ignore

    @property
    def _converted_field_kwargs(self) -> dict:
        self._reformat_kwargs()

        spec = getfullargspec(self.CONVERTED_FIELD_TYPE)

        kwargs = dict(zip(spec.args[1:], spec.args[1:]))
        # the value of kwargs does not matter because it will be replaced with
        # values from `self._original_field_kwargs`

        if spec.varkw:
            base_field_spec = getfullargspec(django_fields.Field)
            kwargs.update(zip(base_field_spec.args[1:], base_field_spec.args[1:]))

        return dict_intersection(self._original_field_kwargs, kwargs)

    def _reformat_kwargs(self):
        self._original_field_kwargs["primary_key"] = self._original_field_kwargs.get("pk", False)
        self._original_field_kwargs["verbose_name"] = self._original_field_kwargs.get("description", None)
        self._original_field_kwargs["db_index"] = self._original_field_kwargs["index"]

        if self._original_field_kwargs.get("null", False) is True:
            self._original_field_kwargs["blank"] = True

        if self._original_field_kwargs.get("default") is None:
            self._original_field_kwargs["default"] = NOT_PROVIDED

        self._original_field_kwargs.pop("validators", None)
        # Can't process the custom validators


class BaseTortoiseRelationalFieldConverter(BaseTortoiseFieldConverter, ABC):
    _on_delete_functions_ratio: Dict[str, Callable] = {
        "CASCADE": django_models.CASCADE,
        "RESTRICT": django_models.RESTRICT,
        "SET NULL": django_models.SET_NULL,
        "SET DEFAULT": django_models.SET_DEFAULT,
    }

    def _reformat_kwargs(self):
        super()._reformat_kwargs()

        self._original_field_kwargs["to"] = self._original_field_kwargs.get("model_name")

        self._original_field_kwargs["on_delete"] = self._on_delete_functions_ratio.get(
            self._original_field_kwargs.get("on_delete")
        )

        self._original_field_kwargs["related_name"] = self._original_field_kwargs.get("related_name")


# Default Fields


class BigIntFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.BigIntField
    CONVERTED_FIELD_TYPE = django_fields.BigIntegerField


class BinaryFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.BinaryField
    CONVERTED_FIELD_TYPE = django_fields.BinaryField


class BooleanFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.BooleanField
    CONVERTED_FIELD_TYPE = django_fields.BooleanField


class CharFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.CharField
    CONVERTED_FIELD_TYPE = django_fields.CharField


class DateFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.DateField
    CONVERTED_FIELD_TYPE = django_fields.DateField


class DatetimeFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.DatetimeField
    CONVERTED_FIELD_TYPE = django_fields.DateTimeField


class DecimalFieldConverter(BaseTortoiseFieldConverter):  # NOQA
    ORIGINAL_FIELD_TYPE = tortoise_fields.DecimalField
    CONVERTED_FIELD_TYPE = django_fields.DecimalField


class FloatFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.FloatField
    CONVERTED_FIELD_TYPE = django_fields.FloatField


class IntFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.IntField
    CONVERTED_FIELD_TYPE = django_fields.IntegerField


class JSONFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.JSONField
    CONVERTED_FIELD_TYPE = django_models.JSONField


class SmallIntFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.SmallIntField
    CONVERTED_FIELD_TYPE = django_fields.SmallIntegerField


class TextFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.TextField
    CONVERTED_FIELD_TYPE = django_fields.TextField


class UUIDFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = tortoise_fields.UUIDField
    CONVERTED_FIELD_TYPE = django_fields.UUIDField


# Relational Fields


class ForeignKeyFieldConverter(BaseTortoiseRelationalFieldConverter):
    ORIGINAL_FIELD_TYPE = relational.ForeignKeyFieldInstance
    CONVERTED_FIELD_TYPE = django_models.ForeignKey


class OneToOneFieldConverter(BaseTortoiseRelationalFieldConverter):
    ORIGINAL_FIELD_TYPE = relational.OneToOneFieldInstance
    CONVERTED_FIELD_TYPE = django_models.OneToOneField


class ManyToManyFieldConverter(BaseTortoiseRelationalFieldConverter):
    ORIGINAL_FIELD_TYPE = relational.ManyToManyFieldInstance
    CONVERTED_FIELD_TYPE = django_models.ManyToManyField
