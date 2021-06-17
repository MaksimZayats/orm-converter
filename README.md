# orm_converter

## Installation
`pip install git+https://github.com/MaxZayats/orm_converter`

## Possible conversions
1. `TortoiseORM` -> `DjangoORM`

## Usage Examples
### 1. Simple Usages
```python
# tortoise_models.py
from tortoise import fields
from tortoise.models import Model
   
class ExampleModel(Model):
    example_field = fields.IntField()
```

To convert only One model:
```python
# django_models.py
from orm_converter import TortoiseToDjango
from .tortoise_models import ExampleModel

ConvertedModel = TortoiseToDjango.convert(ExampleModel)
```

To convert all models from module:
```python
# django_models.py
from orm_converter import TortoiseToDjango
from . import tortoise_models

TortoiseToDjango.convert_from_module(tortoise_models)
# All models from "tortoise_models" will be converted
```

### 2. Redefining fields
```python
# tortoise_models.py
from .custom_tortoise_fields import CustomTortoiseField
from .custom_django_fields import CustomDjangoField
from tortoise.models import Model
   
class ExampleModel(Model):
    custom_field = CustomTortoiseField()
    
    class DjangoFields:
       """
       In class "DjangoFields", you can redefine your tortoise fields to django fields.
       You can use this if you have a custom fields
       Or if "orm_converter" converts fields incorrectly.
       """
       custom_field = CustomDjangoField()
```

```python
# django_models.py
from orm_converter import TortoiseToDjango
from . import tortoise_models

# Convert model with redefined fields just like default model
TortoiseToDjango.convert(tortoise_models.ExampleModel)
# or
TortoiseToDjango.convert_from_module(tortoise_models)
```

### 3. Redefining model
```python
# tortoise_models.py
from tortoise import fields
from tortoise.models import Model

from django.db import models as django_models
   
class ExampleModel(Model):
    example_field = fields.TextField()
    
    class DjangoModel(django_models.Model):
       """
       In class "DjangoModel", you can specify the converted model.
       """
       example_field = django_models.TextField()
```