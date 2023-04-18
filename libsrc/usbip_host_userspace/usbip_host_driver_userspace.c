#include <unistd.h>
#include <libudev.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <libusb-1.0/libusb.h>

#include "usbip_host_common.h"
#include "usbip_host_driver.h"
#include "stub.h"

#if USBIP_HOST_DRIVER_USERSPACE

#undef  PROGNAME
#define PROGNAME "libusbip"


#define BIND_DIR "/var/run/usbip/edevs/"
#define BIND_MAX_PATH (SYSFS_BUS_ID_SIZE + 256)

static libusb_context *libusb_ctx;


static void get_device_busid(libusb_device *dev, char *buf)
{
	snprintf(buf, SYSFS_BUS_ID_SIZE, "%d-%d",
		libusb_get_bus_number(dev),
		libusb_get_port_number(dev));
		// libusb_get_device_address(dev));
}

static uint32_t get_device_speed(libusb_device *dev)
{
	int speed = libusb_get_device_speed(dev);

	switch (speed) {
	case LIBUSB_SPEED_LOW:
		return USB_SPEED_LOW;
	case LIBUSB_SPEED_FULL:
		return USB_SPEED_FULL;
	case LIBUSB_SPEED_HIGH:
		return USB_SPEED_HIGH;
	case LIBUSB_SPEED_SUPER:
	default:
		dbg("unknown speed enum %d", speed);
	}
	return USB_SPEED_UNKNOWN;
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

static inline
struct stub_edev_data *edev_to_stub_edev_data(struct usbip_exported_device *edev)
{
	return (struct stub_edev_data *)(edev->uinf + edev->udev.bNumInterfaces);
}


static void exported_device_delete(struct usbip_exported_device *edev)
{
	struct stub_edev_data *edev_data = edev_to_stub_edev_data(edev);

	if (edev_data->sdev)
		stub_device_delete(edev_data->sdev);
	free(edev);
}

static void read_usb_device_userspace(struct usbip_usb_device *udev,
				libusb_device *dev,
				struct libusb_device_descriptor *desc,
				struct libusb_config_descriptor *config)
{
	char busid[SYSFS_BUS_ID_SIZE];
	get_device_busid(dev, busid);

	memset((char *)udev, 0, sizeof(struct usbip_usb_device));
	strncpy(udev->busid, busid, SYSFS_BUS_ID_SIZE);

	udev->busnum = libusb_get_bus_number(dev);
	// udev->devnum = libusb_get_device_address(dev);
	udev->devnum = libusb_get_port_number(dev);
	udev->speed = get_device_speed(dev);
	udev->idVendor = desc->idVendor;
	udev->idProduct = desc->idProduct;
	udev->bcdDevice = desc->bcdDevice;
	udev->bDeviceClass = desc->bDeviceClass;
	udev->bDeviceSubClass = desc->bDeviceSubClass;
	udev->bDeviceProtocol = desc->bDeviceProtocol;
	udev->bConfigurationValue = config->bConfigurationValue;
	udev->bNumConfigurations = desc->bNumConfigurations;
	udev->bNumInterfaces = config->bNumInterfaces;
}

static void read_usb_interfaces_userspace(struct usbip_usb_interface *uinf,
				struct libusb_config_descriptor *config)
{
	int i;
	const struct libusb_interface_descriptor *intf;

	for (i = 0; i < config->bNumInterfaces; i++) {
		intf = (config->interface + i)->altsetting;
		(uinf + i)->bInterfaceClass = intf->bInterfaceClass;
		(uinf + i)->bInterfaceSubClass = intf->bInterfaceSubClass;
		(uinf + i)->bInterfaceProtocol = intf->bInterfaceProtocol;
		(uinf + i)->bInterfaceNumber = intf->bInterfaceNumber;
	}
}

static void read_endpoint(struct stub_endpoint *ep,
			       const struct libusb_endpoint_descriptor *desc)
{
	ep->nr = desc->bEndpointAddress & LIBUSB_ENDPOINT_ADDRESS_MASK;
	ep->dir = desc->bEndpointAddress & LIBUSB_ENDPOINT_DIR_MASK;
	ep->type = desc->bmAttributes & LIBUSB_TRANSFER_TYPE_MASK;
}

static void read_endpoints(struct stub_endpoint *ep,
				struct libusb_config_descriptor *config)
{
	int i, j, k, num = 0;
	const struct libusb_interface *intf;
	const struct libusb_interface_descriptor *idesc;

	for (i = 0; i < config->bNumInterfaces; i++) {
		intf = config->interface + i;
		for (j = 0; j < intf->num_altsetting; j++) {
			idesc = intf->altsetting + j;
			for (k = 0; k < idesc->bNumEndpoints; k++) {
				read_endpoint(ep + num, idesc->endpoint + k);
			}
		}
	}
}

static int count_endpoints(struct libusb_config_descriptor *config)
{
	int i, j, num = 0;
	const struct libusb_interface *intf;
	const struct libusb_interface_descriptor *idesc;

	for (i = 0; i < config->bNumInterfaces; i++) {
		intf = config->interface + i;
		for (j = 0; j < intf->num_altsetting; j++) {
			idesc = intf->altsetting + j;
			num += idesc->bNumEndpoints;
		}
	}
	return num;
}

static struct usbip_exported_device *exported_device_new(
	libusb_device *dev, struct libusb_device_descriptor *desc)
{
	struct libusb_config_descriptor *config;
	struct usbip_exported_device *edev;
	struct stub_edev_data *edev_data;
	int num_eps;

	if (libusb_get_active_config_descriptor(dev, &config)) {
		err("libusb_get_active_config_descriptor error");
		goto err_out;
	}

	num_eps = count_endpoints(config);
	ndbg("num_eps: %d", num_eps);

	edev = (struct usbip_exported_device *)calloc(1,
		sizeof(struct usbip_exported_device) +
		(config->bNumInterfaces * sizeof(struct usbip_usb_interface)) +
		sizeof(struct stub_edev_data) +
		(num_eps * sizeof(struct stub_endpoint)));

	if (!edev) {
		err("alloc edev");
		goto err_free_config;
	}

	read_usb_device_userspace(&edev->udev, dev, desc, config);
	read_usb_interfaces_userspace(edev->uinf, config);

	edev_data = edev_to_stub_edev_data(edev);
	edev_data->dev = dev;
	edev_data->num_eps = num_eps;
	read_endpoints(edev_data->eps, config);

	libusb_free_config_descriptor(config);
	return edev;

err_free_config:
	libusb_free_config_descriptor(config);
err_out:
	return NULL;
}

static int get_device_list_userspace(__maybe_unused struct usbip_host_driver *hdriver,
	struct usbip_exported_devices *edevs)
{
	int num, i;
	libusb_device **devs, *dev;
	struct usbip_exported_device *edev;
	struct libusb_device_descriptor desc;
	char busid[SYSFS_BUS_ID_SIZE];

	edevs->ndevs = 0;
	INIT_LIST_HEAD(&edevs->edev_list);
	edevs->data = NULL;

	num = libusb_get_device_list(libusb_ctx, &devs);
	if (num < 0) {
		err("libusb_get_device_list error");
		goto err_out;
	}

	for (i = 0; i < num; i++) {
		dev = *(devs + i);
		get_device_busid(dev, busid);
		if (find_exported_device(busid)) {
			if (libusb_get_device_descriptor(dev, &desc)) {
				err("libusb_get_device_descriptor error (%s)", busid);
				goto err_free_list;
			}

			if (desc.bDeviceClass == USB_CLASS_HUB) {
				dbg("skip hub %s", busid);
				continue;
			}

			edev = exported_device_new(dev, &desc);
			if (!edev) {
				err("exported_device_new %s error", busid);
				goto err_out;
			}

			list_add(&edev->node, &edevs->edev_list);
			edevs->ndevs++;
		}
	}
	edevs->data = (void *)devs;
	return 0;

err_free_list:
	libusb_free_device_list(devs, 1);
err_out:
	return -1;
}

static void exported_devices_destroy(struct usbip_exported_devices *edevs)
{
	libusb_device **devs = (libusb_device **)edevs->data;
	struct list_head *i, *tmp;
	struct usbip_exported_device *edev;

	if (devs)
		libusb_free_device_list(devs, 1);

	list_for_each_safe(i, tmp, &edevs->edev_list) {
		edev = list_entry(i, struct usbip_exported_device, node);
		list_del(i);
		exported_device_delete(edev);
	}
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

	info("unbind device on busid %s: complete", busid);

	return 0;
err_close:
	usbip_host_driver_userspace_close(&host_driver);
err_out:
	return -1;
}

int export_device_userspace(__maybe_unused struct usbip_exported_device *edev,
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
	.udev_subsystem = "usb",
	.ops = {
		.open = usbip_host_driver_userspace_open,
		.close = usbip_host_driver_userspace_close,
		.get_device_list = get_device_list_userspace,
		.free_device_list = exported_devices_destroy,
		.get_device = usbip_generic_get_device,
		.read_device = NULL,
		.read_interface = NULL,
		.is_my_device = NULL,
		.bind_device = bind_device_userspace,
		.unbind_device = unbind_device_userspace,
		.export_device = export_device_userspace
	},
};

#endif /* USBIP_HOST_DRIVER_USERSPACE */
