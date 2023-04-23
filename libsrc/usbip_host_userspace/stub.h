#ifndef __STUB_H
#define __STUB_H


#include <libusb-1.0/libusb.h>
#include <pthread.h>

#include "usbip_host_common.h"
#include "stub_common.h"
#include "list.h"


struct stub_interface {
	struct usbip_usb_interface uinf;
	uint8_t detached;
	uint8_t claimed;
};


struct stub_endpoint {
	uint8_t nr;
    // LIBUSB_ENDPOINT_IN || LIBUSB_ENDPOINT_OUT
	uint8_t dir;
    // LIBUSB_TRANSFER_TYPE_
	uint8_t type;
};


struct stub_device {
	libusb_device *dev;
	libusb_device_handle *dev_handle;
	struct usbip_usb_device udev;
	struct usbip_device ud;
	uint32_t devid;
	int num_eps;
	struct stub_endpoint *eps;

	pthread_t tx, rx;

	/*
	 * stub_priv preserves private data of each urb.
	 * It is allocated as stub_priv_cache and assigned to urb->context.
	 *
	 * stub_priv is always linked to any one of 3 lists;
	 *	priv_init: linked to this until the comletion of a urb.
	 *	priv_tx  : linked to this after the completion of a urb.
	 *	priv_free: linked to this after the sending of the result.
	 *
	 * Any of these list operations should be locked by priv_lock.
	 */
	pthread_mutex_t priv_lock;
	struct list_head priv_init;
	struct list_head priv_tx;
	struct list_head priv_free;

	/* see comments for unlinking in stub_rx.c */
	struct list_head unlink_tx;
	struct list_head unlink_free;

	pthread_mutex_t tx_waitq;
	int should_stop;

	struct stub_interface ifs[];
};

struct stub_edev_data {
	libusb_device *dev;
	struct stub_device *sdev;
	int num_eps;
	struct stub_endpoint eps[];
};

/* private data into libusb_transfer->user_data */
struct stub_priv {
	unsigned long seqnum;
	struct list_head list;
	struct stub_device *sdev;
	struct libusb_transfer *trx;

	uint8_t dir;
	uint8_t unlinking;
};

struct stub_unlink {
	unsigned long seqnum;
	struct list_head list;
	enum libusb_transfer_status status;
};

static inline
struct stub_edev_data *edev_to_stub_edev_data(struct usbip_exported_device *edev)
{
	return (struct stub_edev_data *)(edev->uinf + edev->udev.bNumInterfaces);
}

struct stub_device *stub_device_new(struct usbip_exported_device *edev);
void stub_device_delete(struct stub_device *sdev);

void release_interface(libusb_device_handle *dev_handle,
	struct stub_interface *intf, int force);
void release_interfaces(libusb_device_handle *dev_handle, int num_ifs,
	struct stub_interface *intfs, int force);

int claim_interface(libusb_device_handle *dev_handle,
	struct stub_interface *intf);
int claim_interfaces(libusb_device_handle *dev_handle, int num_ifs,
	struct stub_interface *intfs);

int stub_start(struct stub_device *sdev);
void stub_join(struct stub_device *sdev);

void stub_device_cleanup_transfers(struct stub_device *sdev);
void stub_device_cleanup_unlinks(struct stub_device *sdev);

/* stub_rx.c */
void *stub_rx_loop(void *data);

/* stub_tx.c */
void stub_enqueue_ret_unlink(struct stub_device *sdev, uint32_t seqnum,
			     enum libusb_transfer_status status);
void LIBUSB_CALL stub_complete(struct libusb_transfer *trx);
void *stub_tx_loop(void *data);


/* for libusb */
extern libusb_context *stub_libusb_ctx;
uint8_t stub_get_transfer_type(struct stub_device *sdev, uint8_t ep);
uint8_t stub_endpoint_dir(struct stub_device *sdev, uint8_t ep);
int stub_endpoint_dir_out(struct stub_device *sdev, uint8_t ep);
uint8_t stub_get_transfer_flags(uint32_t in);


#endif // __STUB_H
