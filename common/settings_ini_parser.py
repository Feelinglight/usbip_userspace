from typing import List
from enum import IntEnum
import configparser
import os

import irspy.settings_properties as prop


class BadIniException(Exception):
    pass


class PropertyOwner(type):
    def __new__(mcs, name, bases, attrs):
        # Ищет члены, унаследованные от Property и устанавливает им поля name в соответствии с инменем переменной
        for n, v in attrs.items():
            if issubclass(type(v), prop.Property):
                v.name = n
        return super(PropertyOwner, mcs).__new__(mcs, name, bases, attrs)


def add_properties_to_class(instance, a_properties):
    """
    Создает новый класс со свойством prop_name типа propr, унаследованный от instance
    """
    class_name = instance.__class__.__name__ + 'WithProperties'
    child_class = type(class_name, (instance.__class__,), a_properties)
    instance.__class__ = child_class


class Settings(metaclass=PropertyOwner):

    class ValueType(IntEnum):
        INT = 0
        FLOAT = 1
        LIST_FLOAT = 2
        LIST_INT = 3
        STRING = 4
        BYTES = 5

    class VariableInfo:
        def __init__(self, a_name: str, a_section: str, a_type, a_default=None):
            self.name = a_name
            self.section = a_section
            self.type_ = a_type
            self.default = a_default

    def __init__(self, a_ini_path, a_variables: List[VariableInfo]):
        self.ini_path = a_ini_path
        self.settings = configparser.ConfigParser()

        self.__variables = {}
        self.__sections = set()

        for variable in a_variables:
            self.add_variable(variable)
        add_properties_to_class(self, self.__variables)

        self.restore()

    def add_variable(self, a_variable_info: VariableInfo):
        if a_variable_info.type_ == Settings.ValueType.LIST_FLOAT:
            self.__variables[a_variable_info.name] = prop.ListOfFloatProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        elif a_variable_info.type_ == Settings.ValueType.LIST_INT:
            self.__variables[a_variable_info.name] = prop.ListOfIntProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        elif a_variable_info.type_ == Settings.ValueType.FLOAT:
            self.__variables[a_variable_info.name] = prop.FloatProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        elif a_variable_info.type_ == Settings.ValueType.INT:
            self.__variables[a_variable_info.name] = prop.IntProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        elif a_variable_info.type_ == Settings.ValueType.STRING:
            self.__variables[a_variable_info.name] = prop.StringProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        elif a_variable_info.type_ == Settings.ValueType.BYTES:
            self.__variables[a_variable_info.name] = prop.BytesProperty(
                self.ini_path, self.settings, a_variable_info.section, a_variable_info.default)
        else:
            assert False, "Settings: Нереализованный тип"

        self.__sections.add(a_variable_info.section)

    def add_ini_section(self, a_name: str):
        if not self.settings.has_section(a_name):
            self.settings.add_section(a_name)

    def restore(self):
        try:
            if not os.path.exists(self.ini_path):
                self.save()

            for section in self.__sections:
                self.add_ini_section(section)

            self.settings.read(self.ini_path)

        except configparser.ParsingError:
            raise BadIniException

    def save(self):
        with open(self.ini_path, 'w') as config_file:
            self.settings.write(config_file)


if __name__ == "__main__":
    # Пример использования
    a = Settings("./test_settings.ini", [
        Settings.VariableInfo(a_name="list_float", a_section="PARAMETERS", a_type=Settings.ValueType.LIST_FLOAT),
        Settings.VariableInfo(a_name="list_int", a_section="PARAMETERS", a_type=Settings.ValueType.LIST_INT),
        Settings.VariableInfo(a_name="float1", a_section="PARAMETERS", a_type=Settings.ValueType.FLOAT, a_default=123.),
        Settings.VariableInfo(a_name="int1", a_section="PARAMETERS", a_type=Settings.ValueType.INT, a_default=222),
        Settings.VariableInfo(a_name="str1", a_section="PARAMETERS", a_type=Settings.ValueType.STRING, a_default="haha")
    ])

    print(a.list_float, a.list_int, a.float1, a.int1, a.str1)

    a.list_float = [31., 33., 333.]
    a.list_int = [11, 2, 3]
    a.float1 = 11.
    a.int1 = 331
    a.str1 = "he1he"

    print(a.list_float, a.list_int, a.float1, a.int1, a.str1)
