from typing import Any, Dict, Type

import pytest
from django.db.models import Model as DjangoModel
from tortoise.models import Model as TortoiseModel

from .data import TEST_DATA


@pytest.mark.parametrize(
    'django_model_type, tortoise_model_type',
    TEST_DATA,
)
def test_conversions(django_model_type: Type[DjangoModel],
                     tortoise_model_type: Type[TortoiseModel]):
    original_fields = django_model_type._meta.fields  # type: ignore
    converted_fields = tortoise_model_type.DjangoModel._meta.fields  # type: ignore

    for original_field, converted_field in zip(original_fields, converted_fields):
        original_field_attributes: Dict[str, Any] = original_field.__dict__.copy()
        converted_field_attributes: Dict[str, Any] = converted_field.__dict__.copy()

        original_field_attributes.pop('model', None)
        converted_field_attributes.pop('model', None)

        original_field_attributes.pop('creation_counter', None)
        converted_field_attributes.pop('creation_counter', None)

        original_field_attributes.pop('decoder', None)
        original_field_attributes.pop('encoder', None)

        converted_field_attributes.pop('decoder', None)
        converted_field_attributes.pop('encoder', None)

        original_field_attributes.pop('remote_field', None)
        converted_field_attributes.pop('remote_field', None)

        original_field_attributes.pop('opts', None)
        converted_field_attributes.pop('opts', None)

        print(converted_field, type(converted_field))

        assert original_field_attributes == converted_field_attributes, \
            converted_field_attributes['name']
