from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from common import utils
from typing import List, Union
import logging
import fnmatch
import re

_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())

# Ищет класс usb устройства в выводе lsusb -v
LSUSB_CLASS_RE: re.Pattern = re.compile(r'bInterfaceClass[\s]*(?P<class_id>\d+)')

# Ищет все busid в выводе usbip list
USBIP_RE: re.Pattern = re.compile(
    r'- busid (?P<busid>[-.\d]*) \((?P<vid>[\da-zA-Z]*):(?P<pid>[\da-zA-Z]*)\)')

UsbipDevice = namedtuple('UsbipDevice', 'busid vid, pid name class_')


class FilterRulePass(IntEnum):
    ALLOW = 1,
    FORBID = 2,


class FilterRuleType(IntEnum):
    CLASS = 1,
    VID_PID = 2,


@dataclass
class UsbFilterRule:
    pass_: FilterRulePass
    type_: FilterRuleType
    rule: Union[str, int]


class UsbClass(IntEnum):
    AUDIO = 0x01,
    CDC_CTL = 0x02,
    HID = 0x03,
    PHYSICAL = 0x05,
    IMAGE = 0x06,
    PRINTER = 0x07,
    MSC = 0x08,
    HUB = 0x09,
    CDC_DATA = 0x0A,
    SMART_CARD = 0x0B,
    SEC = 0x0D,
    VIDEO = 0x0E,
    HEALTH = 0x0F,
    AUDIO_VIDEO = 0x10,
    BILLBOARD = 0x11,
    BRIDGE = 0x12,
    DISPLAY = 0x13,
    I3C = 0x3C,
    DIAGNOSTIC = 0xDC,
    WIRELESS = 0xE0,
    MISC = 0xEF,
    VENDOR_SPEC = 0xFE,
    UNKNOWN = 0xFFFF


_CLASS_NAME_TO_ENUM = {usb_class.name: usb_class for usb_class in UsbClass}


def usb_class_to_name(usb_class: UsbClass) -> str:
    return usb_class.name.lower().replace("_", " ")


def usb_class_from_name(name: str) -> UsbClass:
    return _CLASS_NAME_TO_ENUM[name.replace(" ", "_").upper()]


def class_to_hex(usb_class: UsbClass) -> int:
    return usb_class.value()


async def get_usb_class_by_id(vid: str, pid: str) -> UsbClass:
    """
    Возвращает UsbClass для USB-устройства с заданным vid:pid
    Если не удалось получить класс для заданного устройства, возвращает None
    """
    _, lsusb_output, _ = await utils.async_check_output(f'lsusb -v -d {vid}:{pid}')

    res = LSUSB_CLASS_RE.search(lsusb_output)
    if res is not None:
        class_id = res.group('class_id')
        try:
            return UsbClass(int(class_id))
        except ValueError:
            return UsbClass.UNKNOWN
    else:
        _LOGGER.error(f'No class id in lsusb output for device {vid}:{pid}')
        _LOGGER.debug(f'lsusb output:\n{lsusb_output}')
        return UsbClass.UNKNOWN


def parse_filter_rules(filter_rules: List[str]) -> List[UsbFilterRule]:
    rules = []
    for rule in filter_rules:
        if len(rule) < 3:
            _LOGGER.warning(
                f"Filter rule '{rule}' has length less than 3 symbols and will be skipped")
            continue

        if rule.startswith("+ "):
            rule_pass = FilterRulePass.ALLOW
        elif rule.startswith("- "):
            rule_pass = FilterRulePass.FORBID
        else:
            _LOGGER.warning(
                f"Filter rule '{rule}' is not starting with '+ ' or '- ' and will be skipped")
            continue

        rule = rule[2:].strip()
        try:
            usb_class = usb_class_from_name(rule)
            rule_type = FilterRuleType.CLASS
            rule_val = usb_class.value
        except KeyError:
            rule_type = FilterRuleType.VID_PID
            rule_val = rule

        rules.append(UsbFilterRule(rule_pass, rule_type, rule_val))

    _LOGGER.debug("Filter rules:\n{}".format('\n'.join(map(str, rules))))

    return rules


def match_filter_rule(usbip_dev: UsbipDevice, filter_rule: UsbFilterRule) -> bool:
    return filter_rule.type_ == FilterRuleType.CLASS and usbip_dev.class_ == filter_rule.rule or \
        filter_rule.type_ == FilterRuleType.VID_PID and \
        fnmatch.fnmatch(f"{usbip_dev.vid}:{usbip_dev.pid}", filter_rule.rule)


def filter_usb_list(usbip_devices: List[UsbipDevice], filter_rules: List[UsbFilterRule]) -> \
        List[UsbipDevice]:
    allowed_devs = []
    for dev in usbip_devices:
        for rule in filter_rules:
            if match_filter_rule(dev, rule):
                if rule.pass_ == FilterRulePass.ALLOW:
                    allowed_devs.append(dev)
                else:
                    _LOGGER.info(f"Device {dev} filtered")
                break

    return allowed_devs
