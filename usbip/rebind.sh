#!/bin/bash
busid="$1"

sudo pkill -9 usbipd
echo "$busid" | sudo tee /sys/bus/usb/drivers/usb/unbind
echo "$busid" | sudo tee /sys/bus/usb/drivers/usb/bind
