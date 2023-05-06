from typing import List, Iterable
from enum import IntEnum, auto
import logging
import asyncio
import os
import re

from usbip_autoexport import config
from usbip_autoimport.usbip_action import UsbipAction, UsbipActionAttach, UsbipActionBind
from common import utils
from common import usb


_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())



async def __do_action_many(action: UsbipAction, usb_list: List[usb.UsbipDevice], enable):
    for dev in usb_list:
        success = await action.do_action(dev.id_, enable=enable)
        if success:
            _LOGGER.debug(f'Device {dev.name} ({dev.vid}:{dev.pid}) '
                          f'{action.cmd(enable=True)} successfully')
        else:
            _LOGGER.error(f'Failed to {action.cmd(enable=enable)} '
                          f'device {dev.name} ({dev.vid}:{dev.pid})')


async def __usbip_auto_action(action: UsbipAction, filter_rules: List[usb.UsbFilterRule],
                              tick_period_s=0.2):
    bind_timer = utils.Timer(2)
    while True:
        # if not filter_rules:
        #     await asyncio.sleep(999)
        if await action.usb_list_changed():
            # После обнаружения устройства нужно обязательно выждать время, перед вызовом usbip,
            # иначе usbip будет глючить
            bind_timer.start()

        if bind_timer.check():
            bind_timer.stop()

            usb_list = await action.get_usb_list()

            _LOGGER.info('Devices list changed --------------------------------')
            _LOGGER.info('\n'.join(map(str, usb_list)))
            _LOGGER.info('-----------------------------------------------------')

            usb_list = usb.filter_usb_list(usb_list, filter_rules)
            _LOGGER.debug("Filtered usb list:\n{}".format("\n".join(map(str, usb_list))))

            await __do_action_many(action, usb_list, enable=True)

        await asyncio.sleep(tick_period_s)


async def usbip_cancel_all_actions(action: UsbipAction):
    usb_devices = await action.get_usb_list()
    await __do_action_many(action, usb_devices, enable=False)


async def usbip_autoredir(action: UsbipAction, filter_rules_path: str, tick_period_s=0.2):
    """
    Следит за подключением и отключением usb-устройств.
    Когда список usb-устройств меняется, пробует испортировать/экспортировать все устройства через
    USBIP, с учетом фильтров
    """
    if os.path.isfile(filter_rules_path):
        with open(filter_rules_path, 'r') as rules_file:
            filter_rules = usb.parse_filter_rules(rules_file.readlines())
    else:
        filter_rules = []
        _LOGGER.warning(f"Файл с правилами фильтрации не найден. Автоматический"
                        f"{action.name().lower()} устройств будет отключен.")
    try:
        await __usbip_auto_action(action, filter_rules, tick_period_s)
    except asyncio.CancelledError:
        _LOGGER.info(f"{usbip_autoredir.__name__} завершен")


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
        Command.AUTOBIND: lambda: usbip_autoredir(UsbipActionBind(), args.filter_rules_path),
        Command.UNBIND: lambda: usbip_cancel_all_actions(UsbipActionBind()),

        Command.AUTOATTACH: lambda: usbip_autoredir(
            UsbipActionAttach(args.servers_file_path), args.filter_rules_path),
        Command.DETACH: lambda: usbip_cancel_all_actions(
            UsbipActionAttach(args.servers_file_path)),
    }

    # () потому что cmd_to_task возвращает lambda, а не task
    # lambda нужны, чтобы не было warning-ов, что корутина не awaited
    task = cmd_to_task[cmd]()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
