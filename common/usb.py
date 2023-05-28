from pydantic import BaseModel
from dataclasses import dataclass
from enum import IntEnum
from common import utils
from typing import List, Union, Set
from common import usb
import logging
import fnmatch
import re

_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())


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
    APP_SPEC = 0xFE,
    VENDOR_SPEC = 0xFF
    UNKNOWN = 0xFFFF


_CLASS_NAME_TO_ENUM = {usb_class.name: usb_class for usb_class in UsbClass}


class UsbipDevice(BaseModel):
    id_: int
    busid: str
    vid: str
    pid: str
    name: str
    classes: List[UsbClass]


class FilterRulePass(IntEnum):
    ALLOW = 1,
    FORBID = 2,


class FilterRuleType(IntEnum):
    CLASS = 1,
    VID_PID = 2,


class UsbFilterRule(BaseModel):
    pass_: FilterRulePass
    type_: FilterRuleType
    rule: Union[str, int]


def usb_class_to_name(usb_class: UsbClass) -> str:
    return usb_class.name.lower().replace("_", " ")


def usb_class_from_name(name: str) -> UsbClass:
    return _CLASS_NAME_TO_ENUM[name.replace(" ", "_").upper()]


def class_to_hex(usb_class: UsbClass) -> int:
    return usb_class.value()


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


def filter_rules_to_str(filter_rules: List[UsbFilterRule]) -> List[str]:
    filter_strs = []
    for rule in filter_rules:
        sign = '+' if rule.pass_ == FilterRulePass.ALLOW else '-'
        rule_str = rule.rule if rule.type_ == FilterRuleType.VID_PID else \
            usb_class_to_name(UsbClass(rule.rule))
        filter_strs.append(f"{sign} {rule_str}")
    return filter_strs


def match_filter_rule(usbip_dev: UsbipDevice, filter_rule: UsbFilterRule) -> bool:
    if filter_rule.type_ == FilterRuleType.CLASS:
        return UsbClass(filter_rule.rule) in usbip_dev.classes
    else:
        return fnmatch.fnmatch(f"{usbip_dev.vid}:{usbip_dev.pid}", filter_rule.rule)


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
