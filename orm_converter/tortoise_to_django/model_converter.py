from inspect import isclass
from typing import Dict, Optional, Type

from django.db.models import Model as DjangoModel
from django.db.models.fields import Field as DjangoField
from tortoise import fields as tortoise_fields
from tortoise.fields import Field as TortoiseField
from tortoise.fields import relational as tortoise_relational_fields
from tortoise.models import MetaInfo
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta

from orm_converter.bases import BaseConvertedModelMeta, BaseConverter
from orm_converter.shared.exceptions import FieldIsNotSupported
from orm_converter.tortoise_to_django import field_converter


class RedefinedDjangoAttributes:
    """
    In this class you can redefine your tortoise attributes to django attributes.
    You can use this if you have a custom fields
    Or if `orm_converter` converts fields incorrectly.
    """


class Converter(BaseConverter):
    _FIELDS_RATIO: Dict[Type[TortoiseField],
                        Type[field_converter.BaseTortoiseFieldConverter]] = {  # type: ignore
        tortoise_fields.BigIntField: field_converter.BigIntFieldConverter,
        tortoise_fields.BinaryField: field_converter.BinaryFieldConverter,
        tortoise_fields.BooleanField: field_converter.BooleanFieldConverter,
        tortoise_fields.CharField: field_converter.CharFieldConverter,
        tortoise_fields.DateField: field_converter.DateFieldConverter,
        tortoise_fields.DatetimeField: field_converter.DatetimeFieldConverter,
        tortoise_fields.DecimalField: field_converter.DecimalFieldConverter,
        tortoise_fields.FloatField: field_converter.FloatFieldConverter,
        tortoise_fields.IntField: field_converter.IntFieldConverter,
        tortoise_fields.JSONField: field_converter.JSONFieldConverter,
        tortoise_fields.SmallIntField: field_converter.SmallIntFieldConverter,
        tortoise_fields.TextField: field_converter.TextFieldConverter,
        tortoise_fields.UUIDField: field_converter.UUIDFieldConverter,

        tortoise_relational_fields.ForeignKeyFieldInstance: field_converter.ForeignKeyFieldConverter,
        tortoise_relational_fields.OneToOneFieldInstance: field_converter.OneToOneFieldConverter,
        tortoise_relational_fields.ManyToManyFieldInstance: field_converter.ManyToManyFieldConverter,
    }

    def __init__(self, original_model_type: Type[TortoiseModel]):
        super().__init__(original_model_type)

        self._redefined_attributes = dict()

        for attribute in self._original_model_type_attributes.values():
            if isclass(attribute) and issubclass(attribute, RedefinedDjangoAttributes):
                self._redefined_attributes |= dict(attribute.__dict__)

    @property
    def converted_model(self) -> Optional[Type[DjangoModel]]:
        meta: Optional[MetaInfo] = getattr(self._original_model_type, "_meta", None)

        if meta is None:
            raise RuntimeError("Can't convert this model")

        converted_fields = self._get_converted_fields(model_meta=meta)
        converted_attributes = self._get_converted_attributes(model_meta=meta) | converted_fields

        return type(self._original_model_type.__name__, (DjangoModel,), converted_attributes)  # type: ignore

    def _get_converted_fields(self, model_meta: MetaInfo) -> Dict[str, DjangoField]:
        converted_fields: Dict[str, DjangoField] = {}

        for field_name, field in model_meta.fields_map.items():
            if field_name in self._redefined_attributes:
                converted_fields[field_name] = self._redefined_attributes.get(field_name)
                continue

            converter = self._FIELDS_RATIO.get(type(field))

            if converter is None:
                raise FieldIsNotSupported(
                    f"{type(field)} is not supported field."
                )

            converted_fields[field_name] = converter(field).converted_field

        return converted_fields

    def _get_converted_attributes(self, model_meta: MetaInfo) -> dict:
        attributes = self._original_model_type_attributes | self._redefined_attributes

        attributes.pop("_meta", None)
        attributes["Meta"] = self._get_converted_meta_class(model_meta=model_meta)

        return attributes

    def _get_converted_meta_class(self, model_meta: MetaInfo) -> Type[object]:
        if self._redefined_attributes.get("Meta", None):
            return self._redefined_attributes.get("Meta")  # type: ignore

        model_meta_class: Type[object] = getattr(self._original_model_type, "Meta", type)
        meta_attributes = dict(model_meta_class.__dict__)

        meta_attributes["db_table"] = meta_attributes.get("table", model_meta.db_table)

        meta_attributes.pop("__dict__", None)
        meta_attributes.pop("table", None)

        return type("Meta", tuple(), meta_attributes)  # type: ignore


class _ConvertedModelMeta(BaseConvertedModelMeta, TortoiseModelMeta):
    default_converter = Converter
    model_type_to_convert = TortoiseModel

    @property
    def DjangoModel(cls) -> Optional[Type[DjangoModel]]:
        return cls._converted_model  # type: ignore


class ConvertedModel(metaclass=_ConvertedModelMeta):
    DjangoModel: Optional[Type[DjangoModel]]

    class Meta:
        abstract = True
