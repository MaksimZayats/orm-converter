from typing import Tuple, Type

import django
from django.conf import settings
from django.db import models as django_models
from django.db.models import Model as DjangoModel
from tortoise import Model as TortoiseModel
from tortoise import fields as tortoise_fields
from tortoise.fields import relational as tortoise_relational_fields

from orm_converter.tortoise_to_django import ConvertedModel

settings.configure()
django.setup()


def _create_models_to_test(
        fields: Tuple[Tuple, ...],
        models_names: Tuple[str, str]
) -> Tuple[Type[DjangoModel], Type[TortoiseModel]]:
    class Meta:
        app_label = 'test'

    tortoise_attributes = {'Meta': Meta}
    django_attributes = {'Meta': Meta, '__module__': '__test__'}

    current_field_index = 0

    for tortoise_field, django_field in fields:
        tortoise_attributes[f'field_{current_field_index}'] = tortoise_field
        django_attributes[f'field_{current_field_index}'] = django_field

        current_field_index += 1

    return (  # type: ignore
        type(
            models_names[1],
            (DjangoModel,),
            django_attributes
        ),
        type(
            models_names[0],
            (TortoiseModel, ConvertedModel),
            tortoise_attributes
        )
    )


class _FieldsToTest:
    without_kwargs = (
        (tortoise_fields.BigIntField(),
         django_models.BigIntegerField()),

        (tortoise_fields.BinaryField(),
         django_models.BinaryField()),

        (tortoise_fields.BooleanField(),
         django_models.BooleanField()),

        (tortoise_fields.DateField(),
         django_models.DateField()),

        (tortoise_fields.DatetimeField(),
         django_models.DateTimeField()),

        (tortoise_fields.FloatField(),
         django_models.FloatField()),

        (tortoise_fields.IntField(),
         django_models.IntegerField()),

        (tortoise_fields.JSONField(),
         django_models.JSONField()),

        (tortoise_fields.SmallIntField(),
         django_models.SmallIntegerField()),

        (tortoise_fields.TextField(),
         django_models.TextField()),

        (tortoise_fields.UUIDField(),
         django_models.UUIDField()),
    )

    with_kwargs = (
        (tortoise_fields.BigIntField(pk=True, description='Test description'),
         django_models.BigIntegerField(primary_key=True,
                                       verbose_name='Test description',
                                       unique=True, db_index=True)),

        (tortoise_fields.BigIntField(default=123),
         django_models.BigIntegerField(default=123)),

        (tortoise_fields.BigIntField(unique=True),
         django_models.BigIntegerField(unique=True)),

        (tortoise_fields.BigIntField(index=True),
         django_models.BigIntegerField(db_index=True)),

        (tortoise_fields.CharField(max_length=255),
         django_models.CharField(max_length=255)),

        (tortoise_fields.BinaryField(null=True),
         django_models.BinaryField(null=True, blank=True)),

        (tortoise_fields.BooleanField(default=False, null=True),
         django_models.BooleanField(default=False, null=True, blank=True)),

        (tortoise_fields.DateField(null=True),
         django_models.DateField(null=True, blank=True)),

        (tortoise_fields.DatetimeField(auto_now=False, auto_now_add=True),
         django_models.DateTimeField(auto_now=False, auto_now_add=True)),

        (tortoise_fields.DecimalField(max_digits=10, decimal_places=5),
         django_models.DecimalField(max_digits=10, decimal_places=5)),

        (tortoise_fields.FloatField(default=0.0, index=True),
         django_models.FloatField(default=0.0, db_index=True)),

        (tortoise_fields.IntField(unique=True),
         django_models.IntegerField(unique=True)),

        (tortoise_fields.JSONField(null=True),
         django_models.JSONField(null=True, blank=True)),

        (tortoise_fields.SmallIntField(default=0),
         django_models.SmallIntegerField(default=0)),

        (tortoise_fields.TextField(null=True),
         django_models.TextField(null=True, blank=True)),

        (tortoise_fields.UUIDField(null=True, description='Test description'),
         django_models.UUIDField(null=True, blank=True, verbose_name='Test description')),
    )

    relational = (
        (
            tortoise_relational_fields.ForeignKeyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
            ),
            django_models.ForeignKey(
                to='TortoiseModelWithoutKwargsFieldArguments',
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.ForeignKeyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
            ),
            django_models.ForeignKey(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.ForeignKeyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                index=True,
                null=True,
            ),
            django_models.ForeignKey(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                null=True, blank=True,
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.OneToOneField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
            ),
            django_models.OneToOneField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.OneToOneField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
            ),
            django_models.OneToOneField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.OneToOneField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
                null=True,
            ),
            django_models.OneToOneField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                null=True, blank=True,
                on_delete=django_models.CASCADE,
            )
        ),

        (
            tortoise_relational_fields.ManyToManyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
            ),
            django_models.ManyToManyField(
                to='TortoiseModelWithoutKwargsFieldArguments',
            )
        ),

        (
            tortoise_relational_fields.ManyToManyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
            ),
            django_models.ManyToManyField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
            )
        ),

        (
            tortoise_relational_fields.ManyToManyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
                null=True,
            ),
            django_models.ManyToManyField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                null=True, blank=True,
            )
        ),

        (
            tortoise_relational_fields.ManyToManyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
                backward_key='test_backward_key',
                null=True,
            ),
            django_models.ManyToManyField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                null=True, blank=True,
            )
        ),

        (
            tortoise_relational_fields.ManyToManyField(
                model_name='test.TortoiseModelWithoutKwargsFieldArguments',
                index=True,
                related_name='test_related_name',
                forward_key='test_forward_key',
                null=True,
            ),
            django_models.ManyToManyField(
                to='TortoiseModelWithoutKwargsFieldArguments',
                related_name='test_related_name',
                null=True, blank=True,
            )
        ),
    )


TEST_DATA = (
    _create_models_to_test(
        _FieldsToTest.without_kwargs,
        ('DjangoModelCase1', 'TortoiseModelCase1')
    ),
    _create_models_to_test(
        _FieldsToTest.with_kwargs,
        ('DjangoModelCase2', 'TortoiseModelCase2')
    ),
    _create_models_to_test(
        _FieldsToTest.relational,
        ('DjangoModelCase3', 'TortoiseModelCase3')
    ),
)
