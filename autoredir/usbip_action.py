from typing import List, Type, Dict
from enum import IntEnum, auto
import logging
import abc
import re

from common import usb, utils

_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


class UsbipAction(abc.ABC):
    class AutoAction(IntEnum):
        BIND = auto()
        ATTACH = auto()

    @staticmethod
    def make_action(action: AutoAction) -> Type['UsbipAction']:
        action_to_class = {
            UsbipAction.AutoAction.BIND: UsbipActionBind,
            UsbipAction.AutoAction.ATTACH: UsbipActionAttach,
        }
        return action_to_class[action]

    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def cmd(self, enable: bool) -> str:
        pass

    @abc.abstractmethod
    async def usb_list_changed(self) -> bool:
        pass

    @abc.abstractmethod
    async def get_usb_list(self) -> List[usb.UsbipDevice]:
        pass

    @abc.abstractmethod
    async def do_action(self, dev_id: int, enable) -> bool:
        pass


class UsbipActionBind(UsbipAction):
    # Ищет все busid в выводе usbip list -l
    USBIP_RE: re.Pattern = re.compile(
        r'- busid (?P<busid>[-.\d]*) \((?P<vid>[\da-zA-Z]*):(?P<pid>[\da-zA-Z]*)\)')

    # Ищет класс usb устройства в выводе lsusb -v
    LSUSB_CLASS_RE: re.Pattern = re.compile(r'bInterfaceClass[\s]*(?P<class_id>\d+)')

    def __init__(self):
        self.prev_lsusb_output = ''
        self.usb_list: List[usb.UsbipDevice] = []

    def name(self) -> str:
        return "Экспорт"

    def cmd(self, enable: bool) -> str:
        return "bind" if enable else "unbind"

    async def usb_list_changed(self) -> bool:
        _, lsusb_output, _ = await utils.async_check_output('lsusb')

        if self.prev_lsusb_output != lsusb_output:
            self.prev_lsusb_output = lsusb_output
            return True

        return False

    async def get_usb_list(self) -> List[usb.UsbipDevice]:
        _, usbip_output, _ = await utils.async_check_output('usbip list -l')
        _, lsusb_output, _ = await utils.async_check_output('lsusb')

        usb_list = []
        for idx, dev in enumerate(self.USBIP_RE.finditer(usbip_output)):
            busid, vid, pid = dev.group('busid'), dev.group('vid'), dev.group('pid')
            if not all([busid, vid, pid]):
                _LOGGER.error('Parse "usbip list -l" error!')

            usb_classes = await self.find_classes(vid, pid)
            usb_name_re = re.search(f'{vid}:{pid} (?P<name>.*)\\n', lsusb_output)
            usb_name = usb_name_re.group('name')

            usbip_device = usb.UsbipDevice(idx, busid, vid, pid, usb_name, usb_classes)
            usb_list.append(usbip_device)

        self.usb_list = list(usb_list)
        return usb_list

    async def do_action(self, dev_id: int, enable: bool) -> bool:
        cmd = self.cmd(enable)
        dev = list(filter(lambda d: d.id_ == dev_id, self.usb_list))[0]
        print("\x1b[33;23m", end=" ", flush=True)
        usbip_res, usbip_output, stderr = \
            await utils.async_check_output(f'sudo usbip {cmd} -b {dev.busid}')
        print("\x1b[0m", end=" ", flush=True)

        if usbip_res == 0:
            _LOGGER.info(f'{dev.busid} ({dev.name}) {cmd} successfully')

        return usbip_res == 0 or 'already bound' in stderr

    async def find_classes(self, vid: str, pid: str) -> List[usb.UsbClass]:
        _, lsusb_output, _ = await utils.async_check_output(f'lsusb -v -d {vid}:{pid}')

        dev_classes = set()
        for class_ in self.LSUSB_CLASS_RE.finditer(lsusb_output):
            class_id = class_.group('class_id')
            try:
                dev_classes.add(usb.UsbClass(int(class_id)))
            except ValueError:
                dev_classes.add(usb.UsbClass.UNKNOWN)

        return list(dev_classes)


class UsbipActionAttach(UsbipAction):

    def __init__(self, servers_file_path):
        self.servers_file_path = servers_file_path
        self.prev_usb_lists: Dict[str, str] = {}

    def name(self) -> str:
        return "Импорт"

    def cmd(self, enable: bool) -> str:
        return "attach" if enable else "detach"

    async def usb_list_changed(self) -> bool:
        _, usb_list_str, _ = await utils.async_check_output('lsusb')

        if self.prev_usb_list_str != usb_list_str:
            self.prev_usb_list_str = usb_list_str
            return True

        return False

    async def get_usb_list(self) -> List[usb.UsbipDevice]:
        _, usb_list_str, _ = await utils.async_check_output('lsusb')
        return []

    async def do_action(self, dev_id: int, enable) -> False:
        pass
