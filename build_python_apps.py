import common.pyinstaller_build as py_build
from usbip_gui import app_info as gui_app


def build_prog(prog_name, main_file, version: str, gui: bool = False):
    app_info = py_build.AppInfo(a_app_name=prog_name,
                                a_version=version,
                                a_company_name='',
                                a_file_description=prog_name,
                                a_internal_name=prog_name,
                                a_copyright='feelinglight',
                                a_original_filename=prog_name,
                                a_product_name=prog_name)

    py_build.build_app(a_main_filename=main_file,
                       a_app_info=app_info,
                       a_noconsole=True,
                       a_one_file=True)


if __name__ == "__main__":
    build_prog("autoredir", "./autoredir/__main__.py", "0.1")
    build_prog(gui_app.NAME, "./usbip_gui/__main__.py", gui_app.VERSION, True)
