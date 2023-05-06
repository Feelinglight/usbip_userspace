from typing import List, Iterable
from enum import IntEnum, auto
import logging
import asyncio
import os
import re

from usbip_autoexport import config
from common import utils
from common import usb


_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


async def get_usbip_devices() -> List[usb.UsbipDevice]:
    """
    Парсит вывод usbip list -l и возвращает список UsbipDevice
    Если filter_classes != None, пропускает USB устройства тех классов,
    которые перечислены в filter_classes
    """
    _, usbip_output, _ = await utils.async_check_output('usbip list -l')
    _, lsusb_output, _ = await utils.async_check_output('lsusb')

    usb_list = []
    for dev in usb.USBIP_RE.finditer(usbip_output):
        busid, vid, pid = dev.group('busid'), dev.group('vid'), dev.group('pid')
        assert all([busid, vid, pid]), 'Parse "usbip list -l" error!'

        usb_class = await usb.get_usb_class_by_id(vid, pid)
        # Имя лучше брать из lsusb, там алгоритм составления имени лучше, чем в usbip list -l
        usb_name_re = re.search(f'{vid}:{pid} (?P<name>.*)\\n', lsusb_output)
        usb_name = usb_name_re.group('name')

        usbip_device = usb.UsbipDevice(busid, vid, pid, usb_name, int(usb_class))
        usb_list.append(usbip_device)

    return usb_list


async def usbip_bind_single(device: usb.UsbipDevice, bind: bool) -> bool:
    """
    Биндит/анбиндит usb устройство к usbip, если usbip возвращает 0, либо
    ошибку "Устройство уже забиндено", возвращает True, иначе False
    """
    bind_cmd = 'bind' if bind else 'unbind'
    print("\x1b[33;23m", end=" ", flush=True)
    usbip_res, usbip_output, stderr = \
        await utils.async_check_output(f'sudo usbip {bind_cmd} -b {device.busid}')
    print("\x1b[0m", end=" ", flush=True)

    if usbip_res == 0:
        cmd_prefix = '' if bind else 'un'
        _LOGGER.info(f'{device.busid} ({device.name}) {cmd_prefix}bound successfully')

    return usbip_res == 0 or 'already bound' in stderr


async def usbip_bind_many(devices: Iterable[usb.UsbipDevice], bind: bool) -> List[usb.UsbipDevice]:
    """
    Биндит/анбиндит несколько usb устройств к usbip. Возвращает список устройств,
    которые не удалось забиндить
    """
    unbound_list = []
    cmd_prefix = '' if bind else 'un'
    for dev in devices:
        bound = await usbip_bind_single(dev, bind)
        if not bound:
            _LOGGER.error(f'Failed to {cmd_prefix}bind device {dev.name} ({dev.vid}:{dev.pid})')
            unbound_list.append(dev)
        # else:
        #     _LOGGER.info(f'Device {usb.name} ({usb.vid}:{usb.pid}) {cmd_prefix}bound successfully')

    return unbound_list


async def usbip_unbind_all():
    """
    Анбиндит все устройства от usbip
    """
    usb_devices = await get_usbip_devices()
    await usbip_bind_many(usb_devices, bind=False)


async def __usbip_auto_bind(filter_rules: List[usb.UsbFilterRule],
                            tick_period_s=0.2, bind_delay_s=2):
    """
    Проверяет вывод lsusb в цикле каждые tick_period_s.
    Если текущий вывод lsusb отличается от предыдущего - запускает таймер на bind_delay_s
    Если в течении bind_delay_s вывод lsusb не менялся, биндит все USB-устройства,
    классы которых не входят в filter_classes, к usbip.
    Иначе сбрасывает таймер обратно на bind_delay_s
    """
    prev_lsusb_output = ''
    # Нужен, чтобы детектировать новые устройства, потому что если вызывать usbip list -l сразу
    # после подключения устройства, usbip плохо работает
    bind_timer = utils.Timer(bind_delay_s)
    while True:
        # if not filter_rules:
        #     await asyncio.sleep(999)

        _, lsusb_output, _ = await utils.async_check_output('lsusb')
        if prev_lsusb_output != lsusb_output:
            prev_lsusb_output = lsusb_output

            # После обнаружения устройства нужно обязательно выждать время, перед вызовом usbip,
            # иначе usbip будет глючить
            bind_timer.start()

        if bind_timer.check():
            bind_timer.stop()

            usb_list = await get_usbip_devices()

            _LOGGER.info('Devices list changed --------------------------------')
            for dev in usb_list:
                _LOGGER.info(dev)
            _LOGGER.info('-----------------------------------------------------')

            usb_list = usb.filter_usb_list(usb_list, filter_rules)
            _LOGGER.debug("Filtered usb list:\n{}".format("\n".join(map(str, usb_list))))
            # await usbip_bind_many(usb_list, bind=True)

        await asyncio.sleep(tick_period_s)


async def usbip_watcher(filter_rules_path, tick_period_s=0.2, bind_delay_s=2):
    """
    Следит за подключением и отключением usb-устройств.
    Когда список usb-устройств меняется, пробует забиндить все устройства через
    USBIP, за исключением тех устройств, которые относятся к классам filter_classes.
    """
    if bind_delay_s < 2:
        _LOGGER.warning("Интервал между подключением устройства и вызова usbip bind должен "
                        "быть достаточно большим, чтобы проброс удался")

    if os.path.isfile(filter_rules_path):
        with open(filter_rules_path, 'r') as rules_file:
            filter_rules = usb.parse_filter_rules(rules_file.readlines())
    else:
        filter_rules = []
        _LOGGER.warning("Файл с правилами фильтрации не найден. Автоматический экспорт устройств"
                        "будет отключен.")
    try:
        await __usbip_auto_bind(filter_rules, tick_period_s, bind_delay_s)
    except asyncio.CancelledError:
        _LOGGER.info(f"{usbip_watcher.__name__} завершен")


if __name__ == '__main__':
    """
    CLI для управления usbip
    Функции:
        Мониторинг и автоматический бинд всех USB-устройств к usbip
        Анбинд всех USB-устройств от usbip
    """
    import argparse

    class Command(IntEnum):
        START = auto()
        UNBIND = auto()

    COMMAND_TO_STRING = {
        Command.START: "start",
        Command.UNBIND: "unbind",
    }
    STRING_TO_CMD = {cmd_str: cmd for cmd, cmd_str in COMMAND_TO_STRING.items()}

    parser = argparse.ArgumentParser(description="Usbip CLI")
    parser.add_argument('-d', action='store_true', dest='debug', help='Show debug messages')
    parser.add_argument('-r', default=config.RULES_LIST_PATH_DEFAULT, dest='filter_rules_path',
                        help='Filter rules file')
    parser.add_argument('command', choices=COMMAND_TO_STRING.values())
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

    cmd = STRING_TO_CMD[args.command]
    cmd_to_task = {
        Command.START: lambda: usbip_watcher(args.filter_rules_path),
        Command.UNBIND: lambda: usbip_unbind_all()
    }

    # () потому что cmd_to_task возвращает lambda, а не task
    # lambda нужны, чтобы не было warning-ов, что корутина не awaited
    task = cmd_to_task[cmd]()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
