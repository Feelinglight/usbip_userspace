#include "stub.h"


static void stub_shutdown(struct usbip_device *ud)
{
	struct stub_device *sdev = container_of(ud, struct stub_device, ud);

	sdev->should_stop = 1;
	usbip_stop_eh(&sdev->ud);
	pthread_mutex_unlock(&sdev->tx_waitq);
	/* rx will exit by disconnect */
}

static void stub_device_reset(struct usbip_device *ud)
{
	struct stub_device *sdev = container_of(ud, struct stub_device, ud);
	int ret;

	dev_dbg(sdev->dev, "device reset\n");

	/* try to reset the device */
	ret = libusb_reset_device(sdev->dev_handle);

	pthread_mutex_lock(&ud->lock);
	if (ret) {
		dev_err(sdev->dev, "device reset\n");
		ud->status = SDEV_ST_ERROR;
	} else {
		dev_info(sdev->dev, "device reset\n");
		ud->status = SDEV_ST_AVAILABLE;
	}
	pthread_mutex_unlock(&ud->lock);
}

static void stub_device_unusable(struct usbip_device *ud)
{
	pthread_mutex_lock(&ud->lock);
	ud->status = SDEV_ST_ERROR;
	pthread_mutex_unlock(&ud->lock);
}

static void init_usbip_device(struct usbip_device *ud)
{
	ud->status = SDEV_ST_AVAILABLE;
	pthread_mutex_init(&ud->lock, NULL);

	ud->eh_ops.shutdown = stub_shutdown;
	ud->eh_ops.reset    = stub_device_reset;
	ud->eh_ops.unusable = stub_device_unusable;
}

static void clear_usbip_device(struct usbip_device *ud)
{
	pthread_mutex_destroy(&ud->lock);
}

static inline uint32_t get_devid(libusb_device *dev)
{
	uint32_t bus_number = libusb_get_bus_number(dev);
	uint32_t dev_addr = libusb_get_device_address(dev);

	return (bus_number << 16) | dev_addr;
}

struct stub_device *stub_device_new(struct usbip_exported_device *edev)
{
	struct stub_device *sdev;
	struct stub_edev_data *edev_data = edev_to_stub_edev_data(edev);
	int num_ifs = edev->udev.bNumInterfaces;
	int num_eps = edev_data->num_eps;
	int i;

	sdev = (struct stub_device *)calloc(1,
			sizeof(struct stub_device) +
			(sizeof(struct stub_interface) * num_ifs) +
			(sizeof(struct stub_endpoint) * num_eps));
	if (!sdev) {
		err("alloc sdev");
		return NULL;
	}

	sdev->dev = edev_data->dev;
	memcpy(&sdev->udev, &edev->udev, sizeof(struct usbip_usb_device));
	init_usbip_device(&sdev->ud);
	sdev->devid = get_devid(edev_data->dev);
	for (i = 0; i < num_ifs; i++)
		memcpy(&((sdev->ifs + i)->uinf), edev->uinf + i,
			sizeof(struct usbip_usb_interface));
	sdev->num_eps = num_eps;
	sdev->eps = (struct stub_endpoint *)(sdev->ifs + num_ifs);
	for (i = 0; i < num_eps; i++)
		memcpy(sdev->eps + i, edev_data->eps + i,
			sizeof(struct stub_endpoint));

	pthread_mutex_init(&sdev->priv_lock, NULL);
	INIT_LIST_HEAD(&sdev->priv_init);
	INIT_LIST_HEAD(&sdev->priv_tx);
	INIT_LIST_HEAD(&sdev->priv_free);
	INIT_LIST_HEAD(&sdev->unlink_tx);
	INIT_LIST_HEAD(&sdev->unlink_free);
	pthread_mutex_init(&sdev->tx_waitq, NULL);
	pthread_mutex_lock(&sdev->tx_waitq);

	return sdev;
}

void stub_device_delete(struct stub_device *sdev)
{
	clear_usbip_device(&sdev->ud);
	pthread_mutex_destroy(&sdev->priv_lock);
	pthread_mutex_destroy(&sdev->tx_waitq);
	free(sdev);
}


void release_interface(__maybe_unused libusb_device_handle *dev_handle,
			      struct stub_interface *intf, int force)
{
	int nr = intf->uinf.bInterfaceNumber;
	int ret;

	if (force || intf->claimed) {
		ret = libusb_release_interface(dev_handle, nr);
		if (ret == 0)
			intf->claimed = 0;
		else
			dbg("failed to release interface %d by %d", nr, ret);
	}
	if (force || intf->detached) {
		ret = libusb_attach_kernel_driver(dev_handle, nr);
		if (ret == 0)
			intf->detached = 0;
		else
			dbg("failed to attach interface %d by %d", nr, ret);
	}
}

void release_interfaces(libusb_device_handle *dev_handle, int num_ifs,
			       struct stub_interface *intfs, int force)
{
	int i;

	for (i = 0; i < num_ifs; i++)
		release_interface(dev_handle, intfs + i, force);
}

int claim_interface(libusb_device_handle *dev_handle,
			   struct stub_interface *intf)
{
	int nr = intf->uinf.bInterfaceNumber;
	int ret;

	ret = libusb_detach_kernel_driver(dev_handle, nr);
	if (ret)
		dbg("failed to detach interface %d by %d", nr, ret);
		/* ignore error, because some platform doesn't support */
	else
		intf->detached = 1;

	dbg("claiming interface %d", nr);
	ret = libusb_claim_interface(dev_handle, nr);
	if (ret) {
		dbg("failed to claim interface %d by %d", nr, ret);
		release_interface(dev_handle, intf, 0);
		return -1;
	}
	intf->claimed = 1;
	return 0;
}

int claim_interfaces(libusb_device_handle *dev_handle, int num_ifs,
			    struct stub_interface *intfs)
{
	int i;

	for (i = 0; i < num_ifs; i++) {
		if (claim_interface(dev_handle, intfs + i))
			return -1;
	}
	return 0;
}

int stub_start(struct stub_device *sdev)
{
	if (sdev == NULL)
		return 0;

	if (usbip_start_eh(&sdev->ud)) {
		err("start event handler");
		return -1;
	}
	// if (pthread_create(&sdev->rx, NULL, stub_rx_loop, sdev)) {
	// 	err("start recv thread");
	// 	return -1;
	// }
	// if (pthread_create(&sdev->tx, NULL, stub_tx_loop, sdev)) {
	// 	err("start send thread");
	// 	return -1;
	// }
	pthread_mutex_lock(&sdev->ud.lock);
	sdev->ud.status = SDEV_ST_USED;
	pthread_mutex_unlock(&sdev->ud.lock);
	dbg("successfully started libusb transmission");
	return 0;
}

void stub_device_cleanup_transfers(struct stub_device *sdev)
{
	// struct stub_priv *priv;
	// struct libusb_transfer *trx;

	dev_dbg(sdev->dev, "free sdev %p\n", sdev);

	// while (1) {
	// 	priv = stub_priv_pop(sdev);
	// 	if (!priv)
	// 		break;

	// 	trx = priv->trx;
	// 	libusb_cancel_transfer(trx);

	// 	dev_dbg(sdev->dev, "free trx %p\n", trx);
	// 	free(priv);
	// 	free(trx->buffer);
	// 	libusb_free_transfer(trx);
	// }
}

void stub_device_cleanup_unlinks(struct stub_device *sdev)
{
	/* derived from stub_shutdown_connection */
	// struct list_head *pos, *tmp;
	// struct stub_unlink *unlink;

	// pthread_mutex_lock(&sdev->priv_lock);
	// list_for_each_safe(pos, tmp, &sdev->unlink_tx) {
	// 	unlink = list_entry(pos, struct stub_unlink, list);
	// 	list_del(&unlink->list);
	// 	free(unlink);
	// }
	// list_for_each_safe(pos, tmp, &sdev->unlink_free) {
	// 	unlink = list_entry(pos, struct stub_unlink, list);
	// 	list_del(&unlink->list);
	// 	free(unlink);
	// }
	pthread_mutex_unlock(&sdev->priv_lock);
}

void stub_join(struct stub_device *sdev)
{
	if (sdev == NULL)
		return;
	dbg("waiting on libusb transmission threads");
	usbip_join_eh(&sdev->ud);
	// pthread_join(sdev->tx, NULL);
	// pthread_join(sdev->rx, NULL);
}

