import queue
from typing import List, Type, Dict, Optional, Set
from dataclasses import dataclass
from enum import IntEnum, auto
from queue import Queue
import configparser
import logging
import json
import abc
import os
import re

from common import usb, utils

_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


class UsbipAction(abc.ABC):

    USBIP_CMD = 'usbip'

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
        _, usbip_output, _ = await utils.async_check_output(f'{self.USBIP_CMD} list -l')
        _, lsusb_output, _ = await utils.async_check_output('lsusb')

        usb_list = []
        for idx, dev in enumerate(self.USBIP_RE.finditer(usbip_output)):
            busid, vid, pid = dev.group('busid'), dev.group('vid'), dev.group('pid')
            if not all([busid, vid, pid]):
                _LOGGER.error(f'Parse "{self.USBIP_CMD} list -l" error!')

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
            await utils.async_check_output(f'{self.USBIP_CMD} {cmd} -b {dev.busid}')
        print("\x1b[0m", end=" ", flush=True)

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
    FIND_DEV_RE = re.compile(
        r'\s+(?P<busid>[-.\d]*): (?P<name>.*) \((?P<vid>[\da-zA-Z]*):(?P<pid>[\da-zA-Z]*)\)')

    FIND_DEV_CLASS_RE = re.compile(
        r'.* \((?P<class>[\dabcdef]{2})/([\dabcdef]{2})/([\dabcdef]{2})\)')

    FIND_PORT_RE = re.compile(
        r'Port (?P<port>[\d\d]):.*')

    FIND_BUSID_PORT_RE = re.compile(
        r'\s+(?P<busid>[-.\d]*) -> .*')

    @dataclass
    class _UsbipServerInfo:
        name: str
        available: bool
        address: str
        rules: List[usb.UsbFilterRule]
        prev_usbip_list: str
        changed: bool
        usb_devices: List[usb.UsbipDevice]

        def __repr__(self):
            return \
                f"address: {self.address}\n" \
                f"rules: {self.rules}\n" \
                f"prev_usbip_list:\n{self.prev_usbip_list}\n" \
                f"changed: {self.changed}\n" \
                f"usb_devices: {self.usb_devices}\n"

    def __init__(self, servers_file_path, commands_queue: queue.Queue):
        self.servers_file_path = servers_file_path
        self.prev_servers_file_mt: float = 0.
        self.config = configparser.ConfigParser()
        self.servers: Dict[str, UsbipActionAttach._UsbipServerInfo] = {}
        self.commands_queue = commands_queue

    def name(self) -> str:
        return "Импорт"

    def cmd(self, enable: bool) -> str:
        return "attach" if enable else "detach"

    def read_config(self) -> Dict[str, 'UsbipActionAttach._UsbipServerInfo']:
        servers = {}
        servers_file_changed = False
        try:
            servers_file_mt = os.stat(self.servers_file_path).st_mtime
            if self.prev_servers_file_mt != servers_file_mt:
                self.prev_servers_file_mt = servers_file_mt
                servers_file_changed = True
            else:
                servers = self.servers
        except (FileNotFoundError, PermissionError) as e:
            _LOGGER.error(f"Can't read {self.servers_file_path} file: {e}")

        if servers_file_changed:
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.servers_file_path)
                server_names = json.loads(self.config['main']['servers'])
            except (KeyError, configparser.ParsingError, json.JSONDecodeError) as e:
                _LOGGER.error(f"Config file {self.servers_file_path} format error: {e}")
            else:
                for srv in server_names:
                    try:
                        address = self.config[srv]['address']
                        rules = list(json.loads(self.config[srv]['rules']))

                        servers[srv] = self._UsbipServerInfo(
                            name=srv,
                            available=True,
                            address=address,
                            rules=usb.parse_filter_rules(rules),
                            prev_usbip_list='',
                            changed=True,
                            usb_devices=[]
                        )

                    except KeyError as e:
                        _LOGGER.error(f"Parse server {srv} config error: {e}")
                    except json.JSONDecodeError as e:
                        _LOGGER.error(f"Cant't parse filter rules for server {srv}: {e}")
        return servers

    async def usb_list_changed(self) -> bool:
        try:
            data = self.commands_queue.get_nowait()
            print(data)
        except queue.Empty:
            pass

        new_servers = self.read_config()

        old_absent = self.servers.keys() - new_servers.keys()
        _LOGGER.debug(f"Absent servres: {old_absent}")
        for srv in old_absent:
            del self.servers[srv]

        new = new_servers.keys() - self.servers.keys()
        _LOGGER.debug(f"New servres: {new}")
        self.servers.update({srv: new_servers[srv] for srv in new})

        old = new_servers.keys() & self.servers.keys()
        _LOGGER.debug(f"Old servers to update address and rules: {old}")
        for srv, srv_info in self.servers.items():
            srv_info.address = new_servers[srv].address
            srv_info.rules = new_servers[srv].rules

        any_server_changed = False
        for srv, srv_info in self.servers.items():
            usbip_cmd = f'{self.USBIP_CMD} list -r {srv_info.address}'
            ret, usb_list_str, _ = await utils.async_check_output(usbip_cmd, log_errors=False)

            if not ret:
                srv_info.available = False

            if srv_info.prev_usbip_list != usb_list_str:
                srv_info.prev_usbip_list = usb_list_str

                srv_info.changed = True
                any_server_changed = True

        _LOGGER.debug(f"New servers list:\n{self.servers}")
        return any_server_changed

    def find_dev(self, line: str) -> Optional[usb.UsbipDevice]:
        if len(line) < 12:
            return None

        res = self.FIND_DEV_RE.search(line)
        if res is not None:
            return usb.UsbipDevice(
                id_=0,
                busid=res.group('busid'),
                name=res.group('name'),
                vid=res.group('vid'),
                pid=res.group('pid'),
                classes=[]
            )

        return None

    def find_class(self, line: str) -> Optional[usb.UsbClass]:
        res = self.FIND_DEV_CLASS_RE.search(line)
        if res is not None:
            class_ = int(res.group('class'), 16)
            if class_:
                return usb.UsbClass(class_)
        return None

    def parse_usbip_list_output(self, usbip_list: str, start_id: int) -> List[usb.UsbipDevice]:
        devs: List[usb.UsbipDevice] = []
        current_id = start_id

        for line in usbip_list.split('\n'):
            dev = self.find_dev(line)
            if dev:
                dev.id_ = current_id
                current_id += 1
                devs.append(dev)
            elif len(devs):
                class_ = self.find_class(line)
                if class_:
                    if class_ not in devs[-1].classes:
                        devs[-1].classes.append(class_)

        return devs

    async def get_usb_list(self) -> List[usb.UsbipDevice]:
        last_usb_id = 0
        for srv, srv_info in self.servers.items():
            if srv_info.changed:
                usb_devices = \
                    self.parse_usbip_list_output(srv_info.prev_usbip_list, last_usb_id)

                srv_info.usb_devices = usb.filter_usb_list(usb_devices, srv_info.rules)

                last_usb_id += len(srv_info.usb_devices)

        return [dev for srv_info in self.servers.values() for dev in srv_info.usb_devices]

    async def do_action_enable(self, server: str, dev: usb.UsbipDevice):
        cmd = self.cmd(enable=True)
        usbip_res, _, _ = await utils.async_check_output(
            f'{self.USBIP_CMD} {cmd} -b {dev.busid} -r {server}')

        attached = usbip_res == 0

        if attached:
            _LOGGER.info(f"Device {dev.busid} from {server} attached")

        return attached

    async def find_dev_port(self, busid: str) -> Optional[int]:
        res, usbip_output, stderr = await utils.async_check_output(f'{self.USBIP_CMD} port')

        if res:
            _LOGGER.error(f"Can't get usbip ports, output:\n{usbip_output}\n{stderr}")
            return None

        current_port = None
        for line in usbip_output.split('\n'):
            port = self.FIND_PORT_RE.search(line)
            if port:
                current_port = int(port.group('port'))
            elif current_port is not None:
                cur_busid = self.FIND_BUSID_PORT_RE.search(line)
                if cur_busid:
                    if busid == cur_busid.group('busid'):
                        return current_port

        _LOGGER.error(f"Device {busid} is not found in {self.USBIP_CMD} port output")
        return None

    async def do_action_disable(self, dev: usb.UsbipDevice):
        cmd = self.cmd(enable=True)

        dev_port = await self.find_dev_port(dev.busid)
        if dev_port is None:
            return False

        usbip_res, usbip_output, stderr = await utils.async_check_output(
            f'{self.USBIP_CMD} {cmd} -p {dev_port}')

        return usbip_res == 0

    async def do_action(self, dev_id: int, enable) -> False:
        for srv, srv_info in self.servers.items():
            if srv_info.usb_devices and \
                    srv_info.usb_devices[0].id_ <= dev_id <= srv_info.usb_devices[-1].id_:
                dev_server = srv
                dev = list(filter(lambda d: d.id_ == dev_id, srv_info.usb_devices))[0]
                break
        else:
            assert False, f"device with id {dev_id} not found"

        if enable:
            return await self.do_action_enable(dev_server, dev)
        else:
            return await self.do_action_disable(dev)
