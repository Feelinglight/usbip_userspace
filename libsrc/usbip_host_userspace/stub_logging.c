#ifdef HAVE_CONFIG_H
#include "../config.h"
#endif

#include <sys/types.h>
#ifndef USBIP_OS_NO_SYS_SOCKET
#include <sys/socket.h>
#include <arpa/inet.h>
#endif
#include <errno.h>

#include "stub.h"

#ifdef CONFIG_USBIP_DEBUG
unsigned long usbip_debug_flag = 0xffffffff;
#else
unsigned long usbip_debug_flag;
#endif

int usbip_dev_printf(FILE *s, const char *level, struct libusb_device *dev)
{
	uint8_t bus = libusb_get_bus_number(dev);
	uint8_t adr = libusb_get_device_address(dev);

	return fprintf(s, "%s:%d-%d ", level, bus, adr);
}

int usbip_devh_printf(FILE *s, const char *level,
		      libusb_device_handle *dev_handle)
{
	struct libusb_device *dev = libusb_get_device(dev_handle);

	return usbip_dev_printf(s, level, dev);
}
