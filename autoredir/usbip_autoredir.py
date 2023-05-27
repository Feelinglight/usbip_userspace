from typing import List
import logging
import asyncio
import os

from autoredir import api
import uvicorn

from autoredir.usbip_action import UsbipAction
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


async def __usbip_auto_action(action: UsbipAction, filter_rules: List[usb.UsbFilterRule]):
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

        await asyncio.sleep(1)


async def usbip_cancel_all_actions(action: UsbipAction):
    usb_devices = await action.get_usb_list()
    await __do_action_many(action, usb_devices, enable=False)


async def usbip_autoredir(action: UsbipAction, filter_rules_path: str):
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
        _LOGGER.warning(f"Файл с правилами фильтрации не найден. Автоматический "
                        f"{action.name().lower()} устройств будет отключен.")
    try:
        await __usbip_auto_action(action, filter_rules)
    except asyncio.CancelledError:
        _LOGGER.info(f"{usbip_autoredir.__name__} завершен")


def run_autoredir_with_api(servers_file_path, filter_rules_path):
    os.environ['SERVERS_FILE_PATH'] = servers_file_path
    os.environ['FILTER_RULES_PATH'] = filter_rules_path

    # redir_app_config = uvicorn.Config()
    uvicorn.run(api.app, host="127.0.0.1", port=13987, log_level="info")
