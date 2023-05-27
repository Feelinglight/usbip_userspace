from enum import IntEnum, auto
import logging
import asyncio

from autoredir.usbip_action import UsbipActionAttach, UsbipActionBind
from autoredir import usbip_autoredir
from autoredir import config


_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


if __name__ == '__main__':
    import argparse

    class Command(IntEnum):
        AUTOBIND = auto()
        UNBIND = auto()
        AUTOATTACH = auto()
        DETACH = auto()

    COMMAND_TO_STRING = {
        Command.AUTOBIND: "autobind",
        Command.UNBIND: "unbind",
        Command.AUTOATTACH: "autoattach",
        Command.DETACH: "detach",
    }
    STRING_TO_CMD = {cmd_str: cmd for cmd, cmd_str in COMMAND_TO_STRING.items()}

    parser = argparse.ArgumentParser(description="Usbip CLI")
    parser.add_argument('-d', action='store_true', dest='debug', help='Show debug messages')
    parser.add_argument('-r', default=config.RULES_LIST_PATH_DEFAULT, dest='filter_rules_path',
                        help='Filter rules file')
    parser.add_argument('-s', default=config.SERVER_LIST_PATH_DEFAULT, dest='servers_file_path',
                        help='Servers file')
    parser.add_argument('command', choices=COMMAND_TO_STRING.values())
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

    cmd = STRING_TO_CMD[args.command]
    cmd_to_task = {
        Command.AUTOBIND: lambda: usbip_autoredir.usbip_autoredir(
            UsbipActionBind(), args.filter_rules_path),
        Command.UNBIND: lambda: usbip_autoredir.usbip_cancel_all_actions(UsbipActionBind()),

        Command.AUTOATTACH: lambda: usbip_autoredir.run_autoredir_with_api(
            args.servers_file_path, args.filter_rules_path),
        # Command.DETACH: lambda: usbip_autoredir.usbip_cancel_all_actions(
        #     UsbipActionAttach(args.servers_file_path)),
    }

    # () потому что cmd_to_task возвращает lambda, а не task
    # lambda нужны, чтобы не было warning-ов, что корутина не awaited
    task = cmd_to_task[cmd]()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
