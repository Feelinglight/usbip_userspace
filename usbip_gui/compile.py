import helpers.pyinstaller_build as py_build

import app_info


if __name__ == "__main__":
    app_info = py_build.AppInfo(a_app_name=app_info.NAME,
                                a_version=app_info.VERSION,
                                a_company_name="Some company",
                                a_file_description="Any description",
                                a_internal_name="Internal name",
                                a_copyright="(c)",
                                a_original_filename="Original filename",
                                a_product_name="Product name")

    libs = [
        # 'C:\\Windows\\System32\\vcruntime140d.dll',
        # 'C:\\Windows\\System32\\ucrtbased.dll',
    ]

    py_build.build_qt_app(a_main_filename="main.py",
                          a_app_info=app_info,
                          a_icon_filename="resources/main_icon.ico",
                          a_noconsole=True,
                          a_one_file=True,
                          a_libs=libs)
