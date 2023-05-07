from typing import List, Tuple
from pathlib import Path
import os

import PyInstaller.__main__ as pyinstaller


version_file_content = \
"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=(0, {version}, 0, 0),
prodvers=(0, 0, 0, 0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x0,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1,
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'{company_name}'),
    StringStruct(u'FileDescription', u'{file_description}'),
    StringStruct(u'FileVersion', u'{version}'),
    StringStruct(u'InternalName', u'{internal_name}'),
    StringStruct(u'LegalCopyright', u'{copyright}'),
    StringStruct(u'OriginalFilename', u'{original_filename}'),
    StringStruct(u'ProductName', u'{product_name}'),
    StringStruct(u'ProductVersion', u'{version}')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


class AppInfo:
    def __init__(self, a_app_name, a_company_name="", a_file_description="", a_version=0, a_internal_name="",
                 a_copyright="", a_original_filename="", a_product_name=""):
        self.app_name = a_app_name
        self.company_name = a_company_name
        self.file_description = a_file_description
        self.version = a_version
        self.internal_name = a_internal_name
        self.copyright = a_copyright
        self.original_filename = a_original_filename
        self.product_name = a_product_name


def build_app(a_main_filename: str, a_app_info: AppInfo, a_icon_filename: str = "", a_noconsole=True,
              a_one_file=True, a_admin = False, a_libs: List[Tuple[str, str]] = None):
    """
    Запускает сборку через pyinstaller с заданными параметрами.
    :param a_main_filename: Имя файла главного скрипта
    :param a_app_info: Информация о приложении
    :param a_icon_filename: Путь к иконке приложения
    :param a_noconsole: Параметр noconole в pyinstaller
    :param a_one_file: Параметр onefile в pyinstaller
    :param a_admin: Параметр --uac-admin в pyinstaller
    :param a_libs: Библиотеки (dll), которые нужно добавить в сборку
    """
    pyinstaller_args = [a_main_filename, "--name={}".format(a_app_info.app_name)]
    if a_one_file:
        pyinstaller_args.append("--onefile")
    if a_noconsole:
        pyinstaller_args.append("--noconsole")
    if a_icon_filename:
        pyinstaller_args.append("--icon={}".format(a_icon_filename))
    if a_admin:
        pyinstaller_args.append("--uac-admin")
    if a_libs:
        for src, dst in a_libs:
            pyinstaller_args.append("--add-data={}{}{}".format(src, os.pathsep, dst))

    version_filename = "version.txt"
    with open(version_filename, 'w', encoding="utf8") as version_file:
        version_file.write(version_file_content.format(
            company_name=a_app_info.company_name, file_description=a_app_info.file_description,
            version=a_app_info.version, internal_name=a_app_info.internal_name,
            copyright=a_app_info.copyright, original_filename=a_app_info.original_filename,
            product_name=a_app_info.product_name)
        )

    pyinstaller_args.append("--version-file={}".format(version_filename))

    try:
        pyinstaller.run(pyinstaller_args)
    finally:
        os.remove(version_filename)
