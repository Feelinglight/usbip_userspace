import configparser
import subprocess
import logging
import socket
import os
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from common.usb import UsbFilterRule, UsbipDevice, UsbClass
from common import usb
from common.utils import Timer
import logging
import json


@dataclass
class UsbipServer:
    name: str
    address: str
    available: bool
    devices: List[UsbipDevice]
    filters: List[UsbFilterRule]


def run_cmd(cmd, log_errors=True, timeout=0.3) -> Tuple[bool, str]:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        stdout = res.stdout.decode().strip().replace('\r', '')
    except subprocess.TimeoutExpired:
        if log_errors:
            logging.warning(f"Команда '{cmd}' завершена по таймауту")
        return False, ""

    if res.returncode != 0:
        if log_errors:
            logging.warning(
                f"Команда {cmd} вернула {res.returncode}.\n"
                f"Stdout:\n{res.stdout}\nStderr:\n{res.stderr}")
        return False, stdout

    return True, stdout


class ServersManager:
    SERVERS_FILE = "./usbip_servers.ini"

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.servers: Dict[str, UsbipServer] = {}
        self.check_servers_timer = Timer(5)
        self.check_servers_timer.start()

        self.__init_servers_file()
        self.__update_servers()

    def __init_servers_file(self):
        if not os.path.isfile(ServersManager.SERVERS_FILE):
            self.config.add_section("main")
            self.config["main"]["servers"] = json.dumps([])
            self.config["main"]["common_filters"] = json.dumps([])
            with open(ServersManager.SERVERS_FILE, 'w') as f:
                self.config.write(f)

    def __save_server(self, server: UsbipServer):
        try:
            self.config.add_section(server.name)
            servers: list = json.loads(self.config["main"]["servers"])
            servers.append(server.name)
            self.config["main"]["servers"] = json.dumps(servers)
        except configparser.DuplicateSectionError:
            pass
        self.config[server.name]['address'] = server.address
        self.config[server.name]['filters'] = json.dumps(usb.filter_rules_to_str(server.filters))

        with open(ServersManager.SERVERS_FILE, 'w') as f:
            self.config.write(f)

        self.__update_servers()

    def __find_dev(self, line: str) -> Optional[UsbipDevice]:
        if len(line) < 12:
            return None

        FIND_DEV_RE = re.compile(
            r'\s+(?P<busid>[-.\d]*): (?P<name>.*) \((?P<vid>[\da-zA-Z]*):(?P<pid>[\da-zA-Z]*)\)')

        res = FIND_DEV_RE.search(line)
        if res is not None:
            return UsbipDevice(
                id_=0,
                busid=res.group('busid'),
                name=res.group('name'),
                vid=res.group('vid'),
                pid=res.group('pid'),
                classes=[]
            )

        return None

    def __find_class(self, line: str) -> Optional[UsbClass]:
        FIND_DEV_CLASS_RE = re.compile(
            r'.* \((?P<class>[\dabcdef]{2})/([\dabcdef]{2})/([\dabcdef]{2})\)')

        res = FIND_DEV_CLASS_RE.search(line)
        if res is not None:
            class_ = int(res.group('class'), 16)
            if class_:
                return UsbClass(class_)
        return None

    def __parse_usbip_list_output(self, usbip_list: str, start_id: int) -> List[UsbipDevice]:
        devs: List[UsbipDevice] = []
        current_id = start_id

        for line in usbip_list.split('\n'):
            dev = self.__find_dev(line)
            if dev:
                dev.id_ = current_id
                current_id += 1
                devs.append(dev)
            elif len(devs):
                class_ = self.__find_class(line)
                if class_:
                    if class_ not in devs[-1].classes:
                        devs[-1].classes.append(class_)

        return devs

    def __update_servers(self):
        self.config.read(ServersManager.SERVERS_FILE)
        server_names = json.loads(self.config["main"]["servers"])

        self.servers.clear()
        for srv_name in server_names:
            server_address = self.config[srv_name]['address']
            res, stdout = run_cmd(f"usbip list -r {server_address}")

            if not res:
                logging.warning(f"Не удалось получить список устройств с сервера {server_address}")

            filter_rules = json.loads(self.config[srv_name]['filters'])

            self.servers[srv_name] = UsbipServer(
                name=srv_name,
                address=server_address,
                available=res,
                devices=self.__parse_usbip_list_output(stdout, 0) if res else [],
                filters=usb.parse_filter_rules(filter_rules),
            )

    def add_server(self, server: UsbipServer) -> Tuple[bool, str]:
        if server.name in self.config.sections():
            return False, "Сервер с таким именем уже существует"

        if server.address in [srv.address for srv in self.servers.values()]:
            return False, "Сервер с таким адресом уже существует"

        try:
            socket.getaddrinfo(server.address.encode('utf-8'), 777)
        except socket.gaierror:
            return False, "Адрес задан некорректно"

        self.__save_server(server)
        logging.debug(f"Server {server} added")
        return True, ""

    def set_server_filters(self, server_name: Optional[str], filters: List[UsbFilterRule]) \
            -> Tuple[bool, str]:
        logging.info(f"Set filter for {server_name}")
        if server_name is not None:
            self.servers[server_name].filters = filters
            self.__save_server(self.servers[server_name])
        else:
            self.config["main"]["common_filters"] = json.dumps(usb.filter_rules_to_str(filters))

            with open(ServersManager.SERVERS_FILE, 'w') as f:
                self.config.write(f)

        return True, ""

    def remove_server(self, name: str) -> Tuple[bool, str]:
        logging.debug(f"Remove server {name}")
        servers_list = json.loads(self.config["main"]["servers"])
        if name in servers_list:
            new_servers = servers_list.remove(name)
            self.config["main"]["servers"] = json.dumps(new_servers)
            self.config.remove_section(name)

            with open(ServersManager.SERVERS_FILE, 'w') as f:
                self.config.write(f)
        else:
            logging.warning(f"Сервер {name} не найден")

        return True, ""

    def get_servers_list(self) -> List[UsbipServer]:
        if self.check_servers_timer.check():
            self.check_servers_timer.start()

            self.__update_servers()

        return list(self.servers.values())

    def attach_device(self, server_name: str, busid: str) -> Tuple[bool, str]:
        logging.info(f"attach device")
        return False, "Функция не реализована"

    def detach_device(self, server_name: str, busid: str) -> Tuple[bool, str]:
        logging.info(f"detach device")
        return False, "Функция не реализована"
