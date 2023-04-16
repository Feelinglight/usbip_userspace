// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Copyright (C) 2011 matt mooney <mfm@muteddisk.com>
 *               2005-2007 Takahiro Hirofuchi
 * Copyright (C) 2015-2016 Samsung Electronics
 *               Igor Kotrasinski <i.kotrasinsk@samsung.com>
 *               Krzysztof Opasiak <k.opasiak@samsung.com>
 */


#include <unistd.h>
#include <libudev.h>
#include <fcntl.h>

#include "usbip_host_common.h"
#include "usbip_host_driver.h"

#if !USBIP_HOST_DRIVER_USERSPACE

#undef  PROGNAME
#define PROGNAME "libusbip"

enum unbind_status {
	UNBIND_ST_OK,
	UNBIND_ST_USBIP_HOST,
	UNBIND_ST_FAILED
};

static int32_t read_device_status_kernel(struct usbip_usb_device *udev)
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

static int is_my_device(struct udev_device *dev)
{
	const char *driver;

	driver = udev_device_get_driver(dev);
	return driver != NULL && !strcmp(driver, USBIP_HOST_DRV_NAME);
}

static int usbip_host_driver_open(struct usbip_host_driver *hdriver)
{
	int ret;

	hdriver->ndevs = 0;
	INIT_LIST_HEAD(&hdriver->edev_list);

	ret = usbip_generic_driver_open(hdriver);
	if (ret)
		err("please load " USBIP_CORE_MOD_NAME ".ko and "
		    USBIP_HOST_DRV_NAME ".ko!");
	return ret;
}

/* call at unbound state */
static int bind_usbip(char *busid)
{
	char attr_name[] = "bind";
	char bind_attr_path[SYSFS_PATH_MAX];
	int rc = -1;

	snprintf(bind_attr_path, sizeof(bind_attr_path), "%s/%s/%s/%s/%s/%s",
		 SYSFS_MNT_PATH, SYSFS_BUS_NAME, SYSFS_BUS_TYPE,
		 SYSFS_DRIVERS_NAME, USBIP_HOST_DRV_NAME, attr_name);

	rc = write_sysfs_attribute(bind_attr_path, busid, strlen(busid));
	if (rc < 0) {
		err("error binding device %s to driver: %s", busid,
		    strerror(errno));
		return -1;
	}

	return 0;
}

/* buggy driver may cause dead lock */
static int unbind_other(char *busid)
{
	enum unbind_status status = UNBIND_ST_OK;

	char attr_name[] = "unbind";
	char unbind_attr_path[SYSFS_PATH_MAX];
	int rc = -1;

	struct udev *udev;
	struct udev_device *dev;
	const char *driver;
	const char *bDevClass;

	/* Create libudev context. */
	udev = udev_new();

	/* Get the device. */
	dev = udev_device_new_from_subsystem_sysname(udev, "usb", busid);
	if (!dev) {
		dbg("unable to find device with bus ID %s", busid);
		goto err_close_busid_dev;
	}

	/* Check what kind of device it is. */
	bDevClass  = udev_device_get_sysattr_value(dev, "bDeviceClass");
	if (!bDevClass) {
		dbg("unable to get bDevClass device attribute");
		goto err_close_busid_dev;
	}

	if (!strncmp(bDevClass, "09", strlen(bDevClass))) {
		dbg("skip unbinding of hub");
		goto err_close_busid_dev;
	}

	/* Get the device driver. */
	driver = udev_device_get_driver(dev);
	if (!driver) {
		/* No driver bound to this device. */
		goto out;
	}

	if (!strncmp(USBIP_HOST_DRV_NAME, driver,
				strlen(USBIP_HOST_DRV_NAME))) {
		/* Already bound to usbip-host. */
		status = UNBIND_ST_USBIP_HOST;
		goto out;
	}

	/* Unbind device from driver. */
	snprintf(unbind_attr_path, sizeof(unbind_attr_path), "%s/%s/%s/%s/%s/%s",
		 SYSFS_MNT_PATH, SYSFS_BUS_NAME, SYSFS_BUS_TYPE,
		 SYSFS_DRIVERS_NAME, driver, attr_name);

	rc = write_sysfs_attribute(unbind_attr_path, busid, strlen(busid));
	if (rc < 0) {
		err("error unbinding device %s from driver", busid);
		goto err_close_busid_dev;
	}

	goto out;

err_close_busid_dev:
	status = UNBIND_ST_FAILED;
out:
	udev_device_unref(dev);
	udev_unref(udev);

	return status;
}

int modify_match_busid(char *busid, int add)
{
	char attr_name[] = "match_busid";
	char command[SYSFS_BUS_ID_SIZE + 4];
	char match_busid_attr_path[SYSFS_PATH_MAX];
	int rc;
	int cmd_size;

	snprintf(match_busid_attr_path, sizeof(match_busid_attr_path),
		 "%s/%s/%s/%s/%s/%s", SYSFS_MNT_PATH, SYSFS_BUS_NAME,
		 SYSFS_BUS_TYPE, SYSFS_DRIVERS_NAME, USBIP_HOST_DRV_NAME,
		 attr_name);

	if (add)
		cmd_size = snprintf(command, SYSFS_BUS_ID_SIZE + 4, "add %s",
				    busid);
	else
		cmd_size = snprintf(command, SYSFS_BUS_ID_SIZE + 4, "del %s",
				    busid);

	rc = write_sysfs_attribute(match_busid_attr_path, command,
				   cmd_size);
	if (rc < 0) {
		dbg("failed to write match_busid: %s", strerror(errno));
		return -1;
	}

	return 0;
}

static int bind_device_kernel(char *busid)
{
	int rc;
	struct udev *udev;
	struct udev_device *dev;
	const char *devpath;

	/* Check whether the device with this bus ID exists. */
	udev = udev_new();
	dev = udev_device_new_from_subsystem_sysname(udev, "usb", busid);
	if (!dev) {
		err("device with the specified bus ID does not exist");
		return -1;
	}
	devpath = udev_device_get_devpath(dev);
	udev_unref(udev);

	/* If the device is already attached to vhci_hcd - bail out */
	if (strstr(devpath, USBIP_VHCI_DRV_NAME)) {
		err("bind loop detected: device: %s is attached to %s\n",
		    devpath, USBIP_VHCI_DRV_NAME);
		return -1;
	}

	rc = unbind_other(busid);
	if (rc == UNBIND_ST_FAILED) {
		err("could not unbind driver from device on busid %s", busid);
		return -1;
	} else if (rc == UNBIND_ST_USBIP_HOST) {
		err("device on busid %s is already bound to %s", busid,
		    USBIP_HOST_DRV_NAME);
		return -1;
	}

	rc = modify_match_busid(busid, 1);
	if (rc < 0) {
		err("unable to bind device on %s", busid);
		return -1;
	}

	rc = bind_usbip(busid);
	if (rc < 0) {
		err("could not bind device to %s", USBIP_HOST_DRV_NAME);
		modify_match_busid(busid, 0);
		return -1;
	}

	info("bind device on busid %s: complete", busid);

	return 0;
}

static int unbind_device_kernel(char *busid)
{
	char bus_type[] = "usb";
	int rc, ret = -1;

	char unbind_attr_name[] = "unbind";
	char unbind_attr_path[SYSFS_PATH_MAX];
	char rebind_attr_name[] = "rebind";
	char rebind_attr_path[SYSFS_PATH_MAX];

	struct udev *udev;
	struct udev_device *dev;
	const char *driver;

	/* Create libudev context. */
	udev = udev_new();

	/* Check whether the device with this bus ID exists. */
	dev = udev_device_new_from_subsystem_sysname(udev, "usb", busid);
	if (!dev) {
		err("device with the specified bus ID does not exist");
		goto err_close_udev;
	}

	/* Check whether the device is using usbip-host driver. */
	driver = udev_device_get_driver(dev);
	if (!driver || strcmp(driver, "usbip-host")) {
		err("device is not bound to usbip-host driver");
		goto err_close_udev;
	}

	/* Unbind device from driver. */
	snprintf(unbind_attr_path, sizeof(unbind_attr_path), "%s/%s/%s/%s/%s/%s",
		 SYSFS_MNT_PATH, SYSFS_BUS_NAME, bus_type, SYSFS_DRIVERS_NAME,
		 USBIP_HOST_DRV_NAME, unbind_attr_name);

	rc = write_sysfs_attribute(unbind_attr_path, busid, strlen(busid));
	if (rc < 0) {
		err("error unbinding device %s from driver", busid);
		goto err_close_udev;
	}

	/* Notify driver of unbind. */
	rc = modify_match_busid(busid, 0);
	if (rc < 0) {
		err("unable to unbind device on %s", busid);
		goto err_close_udev;
	}

	/* Trigger new probing. */
	snprintf(rebind_attr_path, sizeof(unbind_attr_path), "%s/%s/%s/%s/%s/%s",
			SYSFS_MNT_PATH, SYSFS_BUS_NAME, bus_type, SYSFS_DRIVERS_NAME,
			USBIP_HOST_DRV_NAME, rebind_attr_name);

	rc = write_sysfs_attribute(rebind_attr_path, busid, strlen(busid));
	if (rc < 0) {
		err("error rebinding");
		goto err_close_udev;
	}

	ret = 0;
	info("unbind device on busid %s: complete", busid);

err_close_udev:
	udev_device_unref(dev);
	udev_unref(udev);

	return ret;
}

int usbip_export_device_kernel(struct usbip_exported_device *edev, int sockfd)
{
	char attr_name[] = "usbip_sockfd";
	char sockfd_attr_path[SYSFS_PATH_MAX];
	int size;
	char sockfd_buff[30];
	int ret;

	if (edev->status != SDEV_ST_AVAILABLE) {
		dbg("device not available: %s", edev->udev.busid);
		switch (edev->status) {
		case SDEV_ST_ERROR:
			dbg("status SDEV_ST_ERROR");
			ret = ST_DEV_ERR;
			break;
		case SDEV_ST_USED:
			dbg("status SDEV_ST_USED");
			ret = ST_DEV_BUSY;
			break;
		default:
			dbg("status unknown: 0x%x", edev->status);
			ret = -1;
		}
		return ret;
	}

	/* only the first interface is true */
	size = snprintf(sockfd_attr_path, sizeof(sockfd_attr_path), "%s/%s",
			edev->udev.path, attr_name);
	if (size < 0 || (unsigned int)size >= sizeof(sockfd_attr_path)) {
		err("exported device path length %i >= %lu or < 0", size,
		    (long unsigned)sizeof(sockfd_attr_path));
		return -1;
	}

	size = snprintf(sockfd_buff, sizeof(sockfd_buff), "%d\n", sockfd);
	if (size < 0 || (unsigned int)size >= sizeof(sockfd_buff)) {
		err("socket length %i >= %lu or < 0", size,
		    (long unsigned)sizeof(sockfd_buff));
		return -1;
	}

	ret = write_sysfs_attribute(sockfd_attr_path, sockfd_buff,
				    strlen(sockfd_buff));
	if (ret < 0) {
		err("write_sysfs_attribute failed: sockfd %s to %s",
		    sockfd_buff, sockfd_attr_path);
		return ret;
	}

	info("connect: %s", edev->udev.busid);

	return ret;
}


struct usbip_host_driver host_driver = {
	.edev_list = LIST_HEAD_INIT(host_driver.edev_list),
	.udev_subsystem = "usb",
	.ops = {
		.open = usbip_host_driver_open,
		.close = usbip_generic_driver_close,
		.refresh_device_list = usbip_generic_refresh_device_list,
		.get_device = usbip_generic_get_device,
		.read_device = read_usb_device,
		.read_interface = read_usb_interface,
		.is_my_device = is_my_device,
		.read_device_status = read_device_status_kernel,
		.bind_device = bind_device_kernel,
		.unbind_device = unbind_device_kernel,
		.export_device = usbip_export_device_kernel,
	},
};

#endif /* USBIP_HOST_DRIVER_USERSPACE */
