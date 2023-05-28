from pydantic import BaseModel
from common.usb import UsbFilterRule
from common.usb import UsbipDevice


class ServerCreate(BaseModel):
    name: str
    address: str


class ServerShow(BaseModel):
    name: str
    address: str
    available: bool
    rules: list[UsbFilterRule]
    devs: list[UsbipDevice]
