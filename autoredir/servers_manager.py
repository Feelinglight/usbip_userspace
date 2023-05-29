from typing import List, Tuple, Optional
import configparser
import logging
import socket
import os
import json

from models import ServerCreate, ServerShow
from usbip_action import UsbipActionAttach
from common.usb import UsbFilterRule
from common.utils import Timer
from common import usb


class ServersManager:
    SERVERS_FILE = "./usbip_servers.ini"

    def __init__(self, usbip_attach_action: UsbipActionAttach):
        self.config = configparser.ConfigParser()
        self.check_servers_timer = Timer(5)
        self.check_servers_timer.start()

        self.usbip_attach_action = usbip_attach_action

        self.__init_servers_file()

    def __init_servers_file(self):
        if not os.path.isfile(ServersManager.SERVERS_FILE):
            self.config.add_section("main")
            self.config["main"]["servers"] = json.dumps([])
            self.config["main"]["common_filters"] = json.dumps([])
            with open(ServersManager.SERVERS_FILE, 'w') as f:
                self.config.write(f)

    def __save_server(self, server: ServerCreate):
        self.config.add_section(server.name)
        servers: list = json.loads(self.config["main"]["servers"])
        servers.append(server.name)
        self.config["main"]["servers"] = json.dumps(servers)
        self.config[server.name]['address'] = server.address
        self.config[server.name]['filters'] = json.dumps(usb.filter_rules_to_str([
            usb.UsbFilterRule(
                pass_=usb.FilterRulePass.FORBID,
                type_=usb.FilterRuleType.VID_PID,
                rule="- *"
            )
        ]))

        with open(ServersManager.SERVERS_FILE, 'w') as f:
            self.config.write(f)

    def add_server(self, server: ServerCreate) -> Tuple[bool, str]:
        if server.name in self.config.sections():
            return False, "Сервер с таким именем уже существует"

        if server.address in [self.config[srv]['address'] for srv in self.config.sections()]:
            return False, "Сервер с таким адресом уже существует"

        try:
            socket.getaddrinfo(server.address.encode('utf-8'), 777)
        except socket.gaierror:
            return False, "Адрес задан некорректно"

        self.__save_server(server)
        logging.debug(f"Server {server} added")
        return True, ""

    def get_server_filters(self, server_name: Optional[str]) -> List[UsbFilterRule]:
        server_name = 'main' if server_name is None else server_name
        filters_str = json.loads(self.config[server_name]['common_filters'])
        return usb.parse_filter_rules(filters_str)

    def set_server_filters(self, server_name: Optional[str], filters: List[UsbFilterRule]) \
            -> Tuple[bool, str]:
        logging.info(f"Set filter for {server_name}")

        server_name = "main" if server_name is None else server_name
        self.config[server_name]["common_filters"] = json.dumps(usb.filter_rules_to_str(filters))

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
            return False, f"Сервер {name} не найден"

        return True, ""

    def get_servers_list(self) -> List[ServerShow]:
        return []

    def attach_device(self, server_name: str, busid: str) -> Tuple[bool, str]:
        logging.info(f"attach device")
        return False, "Функция не реализована"

    def detach_device(self, server_name: str, busid: str) -> Tuple[bool, str]:
        logging.info(f"detach device")
        return False, "Функция не реализована"
