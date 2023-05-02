from pathlib import Path
from typing import Tuple
import os

from PyQt5 import uic
from PyQt5 import pyrcc


def __is_file_newer(fst_filename, snd_filename):
    return os.path.getmtime(str(fst_filename)) > os.path.getmtime(str(snd_filename))


def convert_ui(path_in: str = ".", path_out: str = ".", resources_path: str = ""):
    """
    Конвертирует .ui формы из path_in в .py файлы (в path_out)
    :param path_in: Каталог, содержащий .ui формы
    :param path_out: Каталог, в коротом будут создаваться .py файлы
    :param resources_path: если не пустая строка, то код в py файлах сгенерируется со строкой
    from resource_path import py_filename, иначе import py_filename
    """
    for ui_filename, py_filename in __old_files_with_extension(path_in, ".ui", path_out, ".py"):
        print(ui_filename, "updated")
        py_filename.parent.mkdir(exist_ok=True, parents=True)
        with open(str(py_filename), 'w', encoding='utf8') as py_file:
            uic.compileUi(ui_filename, py_file, resource_suffix="",
                          from_imports=True if resources_path else False,
                          import_from=resources_path)


def convert_resources(path_in: str = ".", path_out: str = "."):
    """
    Конвертирует .qrc ресурсы из path_in в .py файлы (в path_out)
    :param path_in: Каталог, содержащий .qrc формы
    :param path_out: Каталог, в коротом будут создаваться .py файлы
    """
    for qrc_filename, py_filename in __old_files_with_extension(path_in, ".qrc", path_out, ".py"):
        print(qrc_filename, "updated")
        py_filename.parent.mkdir(exist_ok=True, parents=True)
        __qrc_to_py([str(qrc_filename)], str(py_filename))


def __old_files_with_extension(path_in, ext_in: str, path_out, ext_out: str) -> Tuple[Path, Path]:
    path_in = Path(path_in)
    path_out = Path(path_out)

    for file in os.listdir(str(path_in)):
        if file.endswith(ext_in):
            file = Path(file)
            ui_filename = path_in/file
            py_filename = path_out/file.with_suffix(ext_out)

            if not os.path.isfile(str(py_filename)) or __is_file_newer(ui_filename, py_filename):
                yield ui_filename, py_filename


def __qrc_to_py(qrc_filename, py_filename):
    library = pyrcc.RCCResourceLibrary()
    library.setInputFiles(qrc_filename)
    library.setVerbose(False)
    library.setCompressLevel(pyrcc.CONSTANT_COMPRESSLEVEL_DEFAULT)
    library.setCompressThreshold(pyrcc.CONSTANT_COMPRESSTHRESHOLD_DEFAULT)
    library.setResourceRoot('')

    if not library.readFiles():
        return False

    return library.output(py_filename)


def create_translate(a_py_files_folder: str, a_ts_file_path: str):
    """
    Создает ts-файлы с помощью pylupdate5 из py-файлов qt-форм. Полученные файлы можно открыть в QtLinguist, чтобы
    сгенерировать qm-файл для QTranslator
    :param a_py_files_folder: Каталог с py-файлами
    :param a_ts_files_folder: Каталог, в который будут помещены ts-файлы
    """

    raise NotImplemented("Переписать с использованием функции __old_files_with_extension, без хэшей")
    # py_files_list = []
    # py_files_changed = False
    # for file in os.listdir(a_py_files_folder):
    #     if file.endswith(".py"):
    #         py_filename = "{0}/{1}".format(a_py_files_folder, file)
    #         py_files_list.append(py_filename)
    #
    #         py_current_hash = __get_file_hash(py_filename)
    #         py_prev_hash = "" if py_filename not in hashes.keys() else hashes[py_filename]
    #
    #         if py_prev_hash != py_current_hash or not os.path.isfile(a_ts_file_path):
    #             hashes[py_filename] = py_current_hash
    #             py_files_changed = True
    #
    # if py_files_changed:
    #     os.system("pylupdate5 {} -ts {}".format(" ".join(py_files_list), a_ts_file_path))
    #
    #     with open(hashes_path, 'w') as hashes_file:
    #         json.dump(hashes, hashes_file)


if __name__ == "__main__":
    convert_ui("../../ui", "../../ui/py")
    convert_resources("../../resources", "../../")
    # create_translate("../../upms_1v_pc/ui/py", "../../upms_1v_pc/ui/translates")
