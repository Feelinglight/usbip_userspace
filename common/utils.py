from linecache import checkcache, getline
from typing import Tuple, Optional
from sys import exc_info
import traceback
import asyncio
import logging
import shutil
import time
import pwd
import os


_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


def exception_handler(a_exception):
    e_type, e_obj, e_tb = exc_info()
    frame = e_tb.tb_frame
    lineno = e_tb.tb_lineno
    filename = frame.f_code.co_filename
    checkcache(filename)
    line = getline(filename, lineno, frame.f_globals)
    return "Exception{0} in {1}\n"\
           "Line {2}: '{3}'\n"\
           "Message: {4}".format(type(a_exception), filename, lineno, line.strip(), a_exception)


def get_decorator(errors=(Exception, ), default_value=None, log_out_foo=print):
    def decorator(func):
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                log_out_foo(traceback.format_exc())
                return default_value
        return new_func
    return decorator


exception_decorator = get_decorator(log_out_foo=logging.critical)
exception_decorator_print = get_decorator(log_out_foo=print)
assertion_decorator = get_decorator(errors=(AssertionError, ), log_out_foo=logging.critical)


class Timer:
    """
    Класс таймера.
    Позволяет измерять время
    """
    def __init__(self, a_interval_s: float):
        """
        Инициализирует таймер
        :param a_interval_s: интервал таймера в секундах
        """
        self.interval_s = a_interval_s
        self.start_time = 0.
        self.stop_time = 0.
        self.__started = False

    def start(self, a_interval_s: float = None):
        """
        Запускает таймер
        Если a_interval_s != None, устанавливает время таймера перед запуском
        """
        self.__started = True
        self.start_time = time.perf_counter()
        if a_interval_s is not None:
            self.interval_s = a_interval_s
        self.stop_time = self.start_time + self.interval_s

    def stop(self):
        """
        Останавливает таймер
        """
        self.start_time = 0
        self.stop_time = 0
        self.__started = False

    def check(self) -> bool:
        """
        Возвращает True, если таймер сработал (Время self.interval_s прошло с момента вызова self.start()), иначе False
        Если таймер сработал, будет всегда возвращать True, пока не будут вызваны self.start() или self.stop()
        """
        if not self.__started:
            return False
        return time.perf_counter() > self.stop_time

    def started(self) -> bool:
        """
        Останавливает таймер (функция self.check() будет возвращать False)
        """
        return self.__started

    def time_passed(self) -> float:
        """
        Если таймер остановлен, возвращает 0
        Если таймер запущен, возвращает время, которое прошло с момента запуска таймера.
        Если таймер сработал, возвращает self.interval_s
        """
        if not self.__started:
            return 0
        elif time.perf_counter() > self.stop_time:
            return self.interval_s
        else:
            return time.perf_counter() - self.start_time


async def async_check_output(command: str, log_errors=True) -> Tuple[int, str, str]:
    """
    Асинхронно вызывает команду command и ждет ее завершения.
    Возвращает stdout, stderr и код возврата команды.
    """

    proc = await asyncio.subprocess.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE,
                                                            stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    stdout_formatted = stdout.decode().strip().replace('\r', '')
    stderr_formatted = stderr.decode().strip().replace('\r', '')

    if log_errors and (proc.returncode or stderr_formatted):
        err_msg = f'Команда "{command}" вернула код "{proc.returncode}"'
        if stderr_formatted:
            err_msg += f' (stderr: {stderr_formatted})'
        else:
            err_msg += ' (stderr пуст)'

        _LOGGER.warning(err_msg)

    return proc.returncode, stdout_formatted, stderr_formatted


def utility_call_cmd(utility_name: str) -> Optional[str]:
    """
    Ищет программу с помощью which. Если не находит, то ищет программу в пакетном менеджере flatpak.
    Если находит, то возвращает команду для запуска этой программы, иначе None
    """
    call_cmd = shutil.which(utility_name)
    return call_cmd


def get_home_dir() -> str:
    """
    Возвращает домашний каталог текущего пользователя
    Если при получении домашнего каталога возникла ошибка, возвращает пустую строку
    """
    home = os.environ.get('HOME')
    if home is not None:
        return home
    try:
        pw = pwd.getpwuid(os.getuid())
        return pw.pw_dir
    except Exception:
        return ""


def string_hex_to_16_bit_integer(s: str):
    integer = int(s, 16)
    if integer < 2 ** 16:
        return integer
    else:
        raise ValueError