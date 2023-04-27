#ifndef __STUB_LOGGING_H
#define __STUB_LOGGING_H

#include <stdio.h>
#include <stddef.h>
#include <libusb-1.0/libusb.h>

#include "stub_common.h"

extern unsigned long usbip_debug_flag;
extern struct device_attribute dev_attr_usbip_debug;


#define pr_debug(...) \
	fprintf(stdout, __VA_ARGS__)
#define pr_err(...) \
	fprintf(stderr, __VA_ARGS__)
#define pr_warn(...) \
	fprintf(stderr, __VA_ARGS__)

#define dev_dbg(dev, ...) \
	(usbip_dev_printf(stdout, "DEBUG", dev), \
	fprintf(stdout, __VA_ARGS__))
#define dev_info(dev, ...) \
	(usbip_dev_printf(stdout, "INFO", dev), \
	fprintf(stdout, __VA_ARGS__))
#define dev_err(dev, ...) \
	(usbip_dev_printf(stderr, "ERROR", dev), \
	fprintf(stderr, __VA_ARGS__))

#define devh_dbg(devh, ...) \
	(usbip_devh_printf(stdout, "DEBUG", devh), \
	fprintf(stdout, __VA_ARGS__))
#define devh_info(devh, ...) \
	(usbip_devh_printf(stdout, "INFO", devh), \
	fprintf(stdout, __VA_ARGS__))
#define devh_err(devh, ...) \
	(usbip_devh_printf(stderr, "ERROR", devh), \
	fprintf(stderr, __VA_ARGS__))

enum {
	usbip_debug_xmit	= (1 << 0),
	usbip_debug_sysfs	= (1 << 1),
	usbip_debug_urb		= (1 << 2),
	usbip_debug_eh		= (1 << 3),

	usbip_debug_stub_cmp	= (1 << 8),
	usbip_debug_stub_dev	= (1 << 9),
	usbip_debug_stub_rx	= (1 << 10),
	usbip_debug_stub_tx	= (1 << 11),
};

#define usbip_dbg_flag_xmit	(usbip_debug_flag & usbip_debug_xmit)
#define usbip_dbg_flag_stub_rx	(usbip_debug_flag & usbip_debug_stub_rx)
#define usbip_dbg_flag_stub_tx	(usbip_debug_flag & usbip_debug_stub_tx)
#define usbip_dbg_flag_vhci_sysfs  (usbip_debug_flag & usbip_debug_vhci_sysfs)


#define usbip_dbg_with_flag(flag, fmt, args...)		\
	do {						\
		if (flag & usbip_debug_flag)		\
			pr_debug(fmt, ##args);		\
	} while (0)

#define usbip_dbg_sysfs(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_sysfs, fmt, ##args)
#define usbip_dbg_xmit(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_xmit, fmt, ##args)
#define usbip_dbg_urb(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_urb, fmt, ##args)
#define usbip_dbg_eh(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_eh, fmt, ##args)

#define usbip_dbg_stub_cmp(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_stub_cmp, fmt, ##args)
#define usbip_dbg_stub_rx(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_stub_rx, fmt, ##args)
#define usbip_dbg_stub_tx(fmt, args...) \
	usbip_dbg_with_flag(usbip_debug_stub_tx, fmt, ##args)


int usbip_dev_printf(FILE *s, const char *level,
			struct libusb_device *dev);
int usbip_devh_printf(FILE *s, const char *level,
			libusb_device_handle *dev_handle);

void usbip_dump_buffer(char *buff, int bufflen);
void usbip_dump_trx(struct libusb_transfer *trx);
void usbip_dump_header(struct usbip_header *pdu);

#endif // __STUB_LOGGING_H