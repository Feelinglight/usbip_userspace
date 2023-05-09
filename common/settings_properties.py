from collections.abc import Iterable
import configparser
import abc

from irspy.utils import base64_to_bytes, bytes_to_base64


class Property(abc.ABC):
    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str):
        self.name = None
        self.ini_path = a_ini_path
        self.ini_parser = a_ini_parser
        self.section = a_section

    def __get__(self, instance, owner):
        # print(f"list get {self.name}")
        assert self.name is not None, "Имя свойства не инициализировано"
        try:
            return instance.__dict__[self.name]
        except KeyError:
            instance.__dict__[self.name] = self.from_ini()
            return instance.__dict__[self.name]

    def __set__(self, instance, value):
        # print(f"list set {self.name} = {value}")
        instance.__dict__[self.name] = value
        value_to_ini = self.to_ini(value)
        self.ini_parser[self.section][self.name] = value_to_ini

        with open(self.ini_path, 'w') as config_file:
            self.ini_parser.write(config_file)

    @abc.abstractmethod
    def from_ini(self):
        pass

    @abc.abstractmethod
    def to_ini(self, a_value):
        pass


class ListOfFloatProperty(Property):
    DEFAULT = []

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = list(a_default) if a_default is not None else ListOfFloatProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return [float(val) for val in ini_string.split(',')]
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        assert isinstance(a_value, Iterable), "Значение ListProperty должно быть итерируемым"
        return ','.join(str(val) for val in a_value).strip(',')


class ListOfIntProperty(Property):
    DEFAULT = []

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = list(a_default) if a_default is not None else ListOfIntProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return [int(val) for val in ini_string.split(',')]
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        assert isinstance(a_value, Iterable), "Значение ListProperty должно быть итерируемым"
        return ','.join(str(val) for val in a_value).strip(',')


class FloatProperty(Property):
    DEFAULT = 0.

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = float(a_default) if a_default is not None else FloatProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return float(ini_string)
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        assert isinstance(a_value, float), "Значение FloatProperty должно быть типа float"
        return str(a_value)


class IntProperty(Property):
    DEFAULT = 0

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = int(a_default) if a_default is not None else IntProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return int(ini_string)
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        assert isinstance(a_value, int), "Значение IntProperty должно быть типа int"
        return str(a_value)


class StringProperty(Property):
    DEFAULT = ""

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = str(a_default) if a_default is not None else StringProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return str(ini_string)
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        assert isinstance(a_value, str), "Значение StringProperty должно быть типа str"
        return a_value


class BytesProperty(Property):
    DEFAULT = bytes()

    def __init__(self, a_ini_path, a_ini_parser: configparser.ConfigParser, a_section: str, a_default=None):
        super().__init__(a_ini_path, a_ini_parser, a_section)

        self.default = bytes(a_default) if a_default is not None else BytesProperty.DEFAULT

    def from_ini(self):
        try:
            ini_string = self.ini_parser[self.section][self.name]
            return base64_to_bytes(ini_string)
        except (ValueError, KeyError):
            self.ini_parser[self.section][self.name] = self.to_ini(self.default)
            return self.default

    def to_ini(self, a_value):
        try:
            value_to_ini = bytes_to_base64(bytes(a_value))
        except ValueError:
            print("bytes value_error")
            value_to_ini = bytes_to_base64(BytesProperty.DEFAULT)

        return value_to_ini
