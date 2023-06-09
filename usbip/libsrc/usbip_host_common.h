/* SPDX-License-Identifier: GPL-2.0-or-later */
/*
 * Copyright (C) 2015-2016 Samsung Electronics
 *               Igor Kotrasinski <i.kotrasinsk@samsung.com>
 *               Krzysztof Opasiak <k.opasiak@samsung.com>
 *
 * Refactored from usbip_host_driver.c, which is:
 * Copyright (C) 2011 matt mooney <mfm@muteddisk.com>
 *               2005-2007 Takahiro Hirofuchi
 */

#ifndef __USBIP_HOST_COMMON_H
#define __USBIP_HOST_COMMON_H

#include <stdint.h>
#include <libudev.h>
#include <errno.h>
#include <openssl/ssl.h>

#include "list.h"
#include "usbip_common.h"
#include "sysfs_utils.h"

struct usbip_host_driver;
struct usbip_exported_devices;

struct usbip_host_driver_ops {
	int (*open)(struct usbip_host_driver *hdriver);
	void (*close)(struct usbip_host_driver *hdriver);
	int (*get_device_list)(struct usbip_host_driver *hdriver,
		struct usbip_exported_devices *edevs);
	void (*free_device_list)(struct usbip_exported_devices *edevs);
	struct usbip_exported_device * (*get_device)(
		struct usbip_exported_devices *edevs, const char *busid);
	int (*read_device)(struct udev_device *sdev,
			   struct usbip_usb_device *dev);
	int (*read_interface)(struct usbip_usb_device *udev, int i,
			      struct usbip_usb_interface *uinf);
	int (*is_my_device)(struct udev_device *udev);
	int (*bind_device)(char *busid);
	int (*unbind_device)(char *busid);
	int (*export_device)(struct usbip_exported_device *edev, SSL* ssl_conn);
	int (*run_redirect)(struct usbip_exported_device *edev);
};

struct usbip_exported_devices {
	int ndevs;
	/* list of exported device */
	struct list_head edev_list;
	void *data;
};

struct usbip_host_driver {
	const char *udev_subsystem;
	struct usbip_host_driver_ops ops;
};

struct usbip_exported_device {
	struct udev_device *sudev;
	int32_t status;
	struct usbip_usb_device udev;
	struct list_head node;
	struct usbip_usb_interface uinf[];
};

/* External API to access the driver */
static inline int usbip_driver_open(struct usbip_host_driver *hdriver)
{
	if (!hdriver->ops.open)
		return -EOPNOTSUPP;
	return hdriver->ops.open(hdriver);
}

static inline void usbip_driver_close(struct usbip_host_driver *hdriver)
{
	if (!hdriver->ops.close)
		return;
	hdriver->ops.close(hdriver);
}

static inline int usbip_refresh_device_list(struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs)
{
	if (!hdriver->ops.get_device_list)
		return -EOPNOTSUPP;
	return hdriver->ops.get_device_list(hdriver, edevs);
}

static inline int usbip_free_device_list(struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs)
{
	if (!hdriver->ops.free_device_list)
		return -EOPNOTSUPP;
	hdriver->ops.free_device_list(edevs);
	return 0;
}

static inline int usbip_export_device(struct usbip_host_driver *hdriver,
	struct usbip_exported_device *edev, SSL* ssl_conn)
{
	if (!hdriver->ops.export_device)
		return -EOPNOTSUPP;
	return hdriver->ops.export_device(edev, ssl_conn);
}

static inline struct usbip_exported_device *usbip_get_device(
	struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs, const char *busid)
{
	if (!hdriver->ops.get_device)
		return NULL;
	return hdriver->ops.get_device(edevs, busid);
}

static inline int usbip_run_redirect(struct usbip_host_driver *hdriver,
	struct usbip_exported_device *edev)
{
	if (!hdriver->ops.run_redirect)
		return -EOPNOTSUPP;
	return hdriver->ops.run_redirect(edev);
}

/* Helper functions for implementing driver backend */
int usbip_generic_driver_open(struct usbip_host_driver *hdriver);
void usbip_generic_driver_close(struct usbip_host_driver *hdriver);
int usbip_generic_refresh_device_list(struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs);
struct usbip_exported_device *usbip_generic_get_device(
		struct usbip_exported_devices *edevs, const char *busid);

#endif /* __USBIP_HOST_COMMON_H */
