#include <unistd.h>
#include <libudev.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <libusb-1.0/libusb.h>

#include "usbip_host_common.h"
#include "usbip_host_driver.h"

#if USBIP_HOST_DRIVER_USERSPACE

#undef  PROGNAME
#define PROGNAME "libusbip"


#define BIND_DIR "/var/run/usbip/edevs/"
#define BIND_MAX_PATH (SYSFS_BUS_ID_SIZE + 256)

static libusb_context *libusb_ctx;

static int32_t read_device_status_userspace(__maybe_unused struct usbip_usb_device *udev)
{
	return 0;
}

static void get_device_busid(libusb_device *dev, char *buf)
{
	snprintf(buf, SYSFS_BUS_ID_SIZE, "%d-%d",
		libusb_get_bus_number(dev),
		libusb_get_device_address(dev));
}

static int mkdir_for_edev(const char *path)
{
	char *p;
	char buf[BIND_MAX_PATH];

	strncpy(buf, path, BIND_MAX_PATH);
	for (p = strchr(buf + 1, '/'); p; p = strchr(p + 1, '/')) {
		if (*(p + 1) == '/')
			continue;
		*p = 0;
		if (mkdir(buf, 0755)) {
			if (errno != EEXIST)
				return -1;
		}
		*p = '/';
	}
	return 0;
}

// path = BIND_DIR + busid
static void get_edev_path(char *path, const char *busid)
{
	strncat(path, BIND_DIR, BIND_MAX_PATH - SYSFS_BUS_ID_SIZE);
	strncat(path, busid, SYSFS_BUS_ID_SIZE);
}

static int find_exported_device(const char *busid)
{
	char path[BIND_MAX_PATH] = { 0 };
	struct stat st;

	get_edev_path(path, busid);

	if (stat(path, &st))
		return 0;

	return 1;
}

static int is_my_device(struct udev_device *dev)
{
	const char *name;
	char busid[SYSFS_BUS_ID_SIZE];

	name = udev_device_get_sysname(dev);
	strncpy(busid, name, SYSFS_BUS_ID_SIZE - 1);
	busid[SYSFS_BUS_ID_SIZE - 1] = '\0';

	return find_exported_device(busid);
}

static int usbip_host_driver_userspace_open(__maybe_unused struct usbip_host_driver *hdriver)
{
	return libusb_init(&libusb_ctx);
}

static void usbip_host_driver_userspace_close(__maybe_unused struct usbip_host_driver *hdriver)
{
	libusb_exit(libusb_ctx);
}

int find_device(const char *target_busid)
{
	int i, num, ret = 0;
	libusb_device **devs, *dev;
	char busid[SYSFS_BUS_ID_SIZE];

	num = libusb_get_device_list(libusb_ctx, &devs);
	if (num < 0) {
		err("get device list");
		return -1;
	}

	for (i = 0; i < num; i++) {
		dev = *(devs + i);
		get_device_busid(dev, busid);
		if (!strcmp(busid, target_busid)) {
			ret = 1;
			break;
		}
	}

	libusb_free_device_list(devs, 1);
	return ret;
}

static int bind_device_userspace(char *busid)
{
	int fd;
	char path[BIND_MAX_PATH];
	struct stat st;

	if (usbip_host_driver_userspace_open(&host_driver))
		goto err_out;

	if (!find_device(busid)) {
		err("device with the specified bus ID does not exist");
		goto err_close;
	}

	get_edev_path(path, busid);

	if (!stat(path, &st)) {
		err("device on busid %s is already bound", busid);
		goto err_close;
	}

	if (mkdir_for_edev(path)) {
		err("unable to create file \"%s\"", path);
		goto err_close;
	}

	fd = open(path, O_CREAT | O_EXCL | O_WRONLY, 0600);
	if (fd < 0) {
		err("unable to create file \"%s\"", path);
		goto err_close;
	}
	close(fd);
	usbip_host_driver_userspace_close(&host_driver);

	info("bind device on busid %s: complete", busid);

	return 0;
err_close:
	usbip_host_driver_userspace_close(&host_driver);
err_out:
	return -1;
}

static int unbind_device_userspace(char *busid)
{
	char path[BIND_MAX_PATH];
	struct stat st;

	if (usbip_host_driver_userspace_open(&host_driver))
		goto err_out;

	get_edev_path(path, busid);

	if (stat(path, &st)) {
		err("device is not bound");
		goto err_close;
	}

	if (unlink(path)) {
		err("del edev %s", path);
		goto err_close;
	}
	usbip_host_driver_userspace_close(&host_driver);
	return 0;
err_close:
	usbip_host_driver_userspace_close(&host_driver);
err_out:
	return -1;
}

int usbip_export_device_userspace(__maybe_unused struct usbip_exported_device *edev,
	__maybe_unused int sockfd)
{
	// char attr_name[] = "usbip_sockfd";
	// char sockfd_attr_path[SYSFS_PATH_MAX];
	// int size;
	// char sockfd_buff[30];
	// int ret;

	// if (edev->status != SDEV_ST_AVAILABLE) {
	// 	dbg("device not available: %s", edev->udev.busid);
	// 	switch (edev->status) {
	// 	case SDEV_ST_ERROR:
	// 		dbg("status SDEV_ST_ERROR");
	// 		ret = ST_DEV_ERR;
	// 		break;
	// 	case SDEV_ST_USED:
	// 		dbg("status SDEV_ST_USED");
	// 		ret = ST_DEV_BUSY;
	// 		break;
	// 	default:
	// 		dbg("status unknown: 0x%x", edev->status);
	// 		ret = -1;
	// 	}
	// 	return ret;
	// }

	// /* only the first interface is true */
	// size = snprintf(sockfd_attr_path, sizeof(sockfd_attr_path), "%s/%s",
	// 		edev->udev.path, attr_name);
	// if (size < 0 || (unsigned int)size >= sizeof(sockfd_attr_path)) {
	// 	err("exported device path length %i >= %lu or < 0", size,
	// 	    (long unsigned)sizeof(sockfd_attr_path));
	// 	return -1;
	// }

	// size = snprintf(sockfd_buff, sizeof(sockfd_buff), "%d\n", sockfd);
	// if (size < 0 || (unsigned int)size >= sizeof(sockfd_buff)) {
	// 	err("socket length %i >= %lu or < 0", size,
	// 	    (long unsigned)sizeof(sockfd_buff));
	// 	return -1;
	// }

	// ret = write_sysfs_attribute(sockfd_attr_path, sockfd_buff,
	// 			    strlen(sockfd_buff));
	// if (ret < 0) {
	// 	err("write_sysfs_attribute failed: sockfd %s to %s",
	// 	    sockfd_buff, sockfd_attr_path);
	// 	return ret;
	// }

	// info("connect: %s", edev->udev.busid);

	// return ret;
	return 0;
}

struct usbip_host_driver host_driver = {
	.edev_list = LIST_HEAD_INIT(host_driver.edev_list),
	.udev_subsystem = "usb",
	.ops = {
		.open = usbip_host_driver_userspace_open,
		.close = usbip_host_driver_userspace_close,
		.refresh_device_list = usbip_generic_refresh_device_list,
		.get_device = usbip_generic_get_device,
		.read_device = read_usb_device,
		.read_interface = read_usb_interface,
		.is_my_device = is_my_device,
		.read_device_status = read_device_status_userspace,
		.bind_device = bind_device_userspace,
		.unbind_device = unbind_device_userspace,
		.export_device = usbip_export_device_userspace
	},
};

#endif /* USBIP_HOST_DRIVER_USERSPACE */
