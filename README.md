# Orm-Converter

## Installation
```bash
pip install orm-converter
```

or

```bash
pip install git+https://github.com/MaxZayats/orm-converter`
```

***

## Available conversions
1. `TortoiseORM` -> `DjangoORM`

***

## Usage Examples
### 1. Simple Usage
```python
from orm_converter.tortoise_to_django import ConvertedModel
from tortoise import fields
from tortoise.models import Model as TortoiseModel


class ExampleModel(TortoiseModel, ConvertedModel):
    example_field = fields.IntField()


ExampleModel.DjangoModel  # <- Converted Django Model
```

### 2. Redefining fields/attributes
```python
from custom_django_fields import CustomDjangoField
from custom_tortoise_fields import CustomTortoiseField
from orm_converter.tortoise_to_django import (ConvertedModel,
                                              RedefinedDjangoAttributes)
from tortoise.models import Model as TortoiseModel


class ExampleModel(TortoiseModel, ConvertedModel):
    custom_field = CustomTortoiseField()

    class RedefinedAttributes(RedefinedDjangoAttributes):
        """
        In this class you can redefine your tortoise attributes to django attributes.
        You can use this if you have a custom fields
        Or if `orm_converter` converts fields incorrectly.
        """

        custom_field = CustomDjangoField()
```

### 3. Adding custom converters
```python
from custom_django_fields import CustomDjangoField
from custom_tortoise_fields import CustomTortoiseField
from orm_converter.tortoise_to_django import (BaseTortoiseFieldConverter,
                                              ConvertedModel, Converter)
from tortoise.models import Model as TortoiseModel


class MyCustomFieldConverter(BaseTortoiseFieldConverter):
    ORIGINAL_FIELD_TYPE = CustomTortoiseField
    CONVERTED_FIELD_TYPE = CustomDjangoField

    def _reformat_kwargs(self):
        super()._reformat_kwargs()
        # change field kwargs here

        self._original_field_kwargs["custom_kwarg"] = "Django"


Converter.add_converters(MyCustomFieldConverter)


class ExampleModel(TortoiseModel, ConvertedModel):
    custom_field = CustomTortoiseField(custom_kwarg="Tortoise")
```
