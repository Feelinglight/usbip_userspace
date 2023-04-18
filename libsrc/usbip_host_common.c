// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Copyright (C) 2015-2016 Samsung Electronics
 *               Igor Kotrasinski <i.kotrasinsk@samsung.com>
 *               Krzysztof Opasiak <k.opasiak@samsung.com>
 *
 * Refactored from usbip_host_driver.c, which is:
 * Copyright (C) 2011 matt mooney <mfm@muteddisk.com>
 *               2005-2007 Takahiro Hirofuchi
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <errno.h>
#include <unistd.h>

#include <libudev.h>
#include <assert.h>

#include "usbip_common.h"
#include "usbip_host_common.h"
#include "list.h"
#include "sysfs_utils.h"

extern struct udev *udev_context;


static int32_t read_device_status(struct usbip_usb_device *udev)
{
	char status_attr_path[SYSFS_PATH_MAX];
	int size;
	int fd;
	int length;
	char status[2] = { 0 };
	int value = 0;

	size = snprintf(status_attr_path, sizeof(status_attr_path),
			"%s/usbip_status", udev->path);
	if (size < 0 || (unsigned int)size >= sizeof(status_attr_path)) {
		err("usbip_status path length %i >= %lu or < 0", size,
		    (long unsigned)sizeof(status_attr_path));
		return -1;
	}


	fd = open(status_attr_path, O_RDONLY);
	if (fd < 0) {
		err("error opening attribute %s", status_attr_path);
		return -1;
	}

	length = read(fd, status, 1);
	if (length < 0) {
		err("error reading attribute %s", status_attr_path);
		close(fd);
		return -1;
	}

	value = atoi(status);
	close(fd);
	return value;
}

static
struct usbip_exported_device *usbip_exported_device_new(
		struct usbip_host_driver *hdriver, const char *sdevpath)
{
	struct usbip_exported_device *edev = NULL;
	struct usbip_exported_device *edev_old;
	size_t size;
	int i;

	edev = calloc(1, sizeof(struct usbip_exported_device));

	edev->sudev =
		udev_device_new_from_syspath(udev_context, sdevpath);
	if (!edev->sudev) {
		err("udev_device_new_from_syspath: %s", sdevpath);
		goto err;
	}

	if (hdriver->ops.read_device(edev->sudev, &edev->udev) < 0)
		goto err;

	edev->status = read_device_status(&edev->udev);
	if (edev->status < 0)
		goto err;

	/* reallocate buffer to include usb interface data */
	size = sizeof(struct usbip_exported_device) +
		edev->udev.bNumInterfaces * sizeof(struct usbip_usb_interface);

	edev_old = edev;
	edev = realloc(edev, size);
	if (!edev) {
		edev = edev_old;
		dbg("realloc failed");
		goto err;
	}

	for (i = 0; i < edev->udev.bNumInterfaces; i++) {
		/* vudc does not support reading interfaces */
		if (!hdriver->ops.read_interface)
			break;
		hdriver->ops.read_interface(&edev->udev, i, &edev->uinf[i]);
	}

	return edev;
err:
	if (edev->sudev)
		udev_device_unref(edev->sudev);
	if (edev)
		free(edev);

	return NULL;
}

static int refresh_exported_devices(struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs)
{
	struct usbip_exported_device *edev;
	struct udev_enumerate *enumerate;
	struct udev_list_entry *devices, *dev_list_entry;
	struct udev_device *dev;
	const char *path;

	enumerate = udev_enumerate_new(udev_context);
	udev_enumerate_add_match_subsystem(enumerate, hdriver->udev_subsystem);
	udev_enumerate_scan_devices(enumerate);

	devices = udev_enumerate_get_list_entry(enumerate);

	udev_list_entry_foreach(dev_list_entry, devices) {
		path = udev_list_entry_get_name(dev_list_entry);
		dev = udev_device_new_from_syspath(udev_context,
						   path);
		if (dev == NULL)
			continue;

		/* Check whether device uses usbip driver. */
		if (hdriver->ops.is_my_device(dev)) {
			edev = usbip_exported_device_new(hdriver, path);
			if (!edev) {
				dbg("usbip_exported_device_new failed");
				continue;
			}

			list_add(&edev->node, &edevs->edev_list);
			edevs->ndevs++;
		}
	}

	return 0;
}

int usbip_generic_driver_open(__maybe_unused struct usbip_host_driver *hdriver)
{
	udev_context = udev_new();
	if (!udev_context) {
		err("udev_new failed");
		return -1;
	}

	return 0;
}

void usbip_generic_driver_close(struct usbip_host_driver *hdriver)
{
	if (!hdriver)
		return;

	udev_unref(udev_context);
}

int usbip_generic_refresh_device_list(struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs)
{
	int rc;

	edevs->ndevs = 0;
	INIT_LIST_HEAD(&edevs->edev_list);

	rc = refresh_exported_devices(hdriver, edevs);

	if (rc < 0)
		return -1;

	return 0;
}

struct usbip_exported_device *usbip_generic_get_device(
		struct usbip_exported_devices *edevs, const char *busid)
{
	struct list_head *i;
	struct usbip_exported_device *edev;

	list_for_each(i, &edevs->edev_list) {
		edev = list_entry(i, struct usbip_exported_device, node);
		if (!strncmp(busid, edev->udev.busid, SYSFS_BUS_ID_SIZE))
			return edev;
	}

	return NULL;
}
