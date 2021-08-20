from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, Type


class BaseFieldConverter(ABC):
    def __init__(self, original_field: object):
        if not isinstance(original_field, self.ORIGINAL_FIELD_TYPE):
            raise TypeError("Invalid field type\n"
                            f'Expected: "{self.ORIGINAL_FIELD_TYPE}"\n'
                            f'Got: "{type(original_field)}"')

        self._original_field = original_field
        self._original_field_kwargs = original_field.__dict__.copy()

    @property
    @abstractmethod
    def ORIGINAL_FIELD_TYPE(self) -> Type[object]:
        pass

    @property
    @abstractmethod
    def CONVERTED_FIELD_TYPE(self) -> Type[object]:
        pass

    @property
    @abstractmethod
    def converted_field(self) -> object:
        pass


class BaseConverter(ABC):
    def __init__(self, original_model_type: Type[object]):
        self._original_model_type = original_model_type
        self._original_model_type_attributes = original_model_type.__dict__.copy()

    @property
    @abstractmethod
    def _FIELDS_RATIO(self) -> Dict[Type[object], Type[BaseFieldConverter]]:
        pass

    @property
    @abstractmethod
    def converted_model(self):
        pass

    @classmethod
    def add_converters(cls, *converters: Type[BaseFieldConverter]):
        for converter in converters:
            cls._FIELDS_RATIO[converter.ORIGINAL_FIELD_TYPE] = converter  # type: ignore


class BaseConvertedModelMeta(ABCMeta):
    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)  # type: ignore

        if issubclass(cls, mcs.model_type_to_convert):  # NOQA
            converted_model = mcs.default_converter(cls).converted_model  # NOQA type: ignore
            cls._converted_model = converted_model
        else:
            cls._converted_model = None

        return cls

    @property
    @abstractmethod
    def default_converter(cls) -> Type[object]:
        pass

    @property
    @abstractmethod
    def model_type_to_convert(cls) -> Type[object]:
        pass
