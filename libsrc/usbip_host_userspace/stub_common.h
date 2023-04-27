#ifndef __STUB_COMMON_H
#define __STUB_COMMON_H

#include <stdio.h>
#include <stddef.h>
#include <libusb-1.0/libusb.h>

#include "usbip_common.h"

struct kvec {
	void *iov_base; /* and that should *never* hold a userland pointer */
	size_t iov_len;
};

#define USBIP_URB_SHORT_NOT_OK		0x0001
#define USBIP_URB_ISO_ASAP		0x0002
#define USBIP_URB_NO_TRANSFER_DMA_MAP	0x0004
#define USBIP_URB_ZERO_PACKET		0x0040
#define USBIP_URB_NO_INTERRUPT		0x0080
#define USBIP_URB_FREE_BUFFER		0x0100
#define USBIP_URB_DIR_IN		0x0200
#define USBIP_URB_DIR_OUT		0
#define USBIP_URB_DIR_MASK		USBIP_URB_DIR_IN

#define USBIP_URB_DMA_MAP_SINGLE	0x00010000
#define USBIP_URB_DMA_MAP_PAGE		0x00020000
#define USBIP_URB_DMA_MAP_SG		0x00040000
#define USBIP_URB_MAP_LOCAL		0x00080000
#define USBIP_URB_SETUP_MAP_SINGLE	0x00100000
#define USBIP_URB_SETUP_MAP_LOCAL	0x00200000
#define USBIP_URB_DMA_SG_COMBINED	0x00400000
#define USBIP_URB_ALIGNED_TEMP_BUFFER	0x00800000

/*
 * USB/IP request headers
 *
 * Each request is transferred across the network to its counterpart, which
 * facilitates the normal USB communication. The values contained in the headers
 * are basically the same as in a URB. Currently, four request types are
 * defined:
 *
 *  - USBIP_CMD_SUBMIT: a USB request block, corresponds to usb_submit_urb()
 *    (client to server)
 *
 *  - USBIP_RET_SUBMIT: the result of USBIP_CMD_SUBMIT
 *    (server to client)
 *
 *  - USBIP_CMD_UNLINK: an unlink request of a pending USBIP_CMD_SUBMIT,
 *    corresponds to usb_unlink_urb()
 *    (client to server)
 *
 *  - USBIP_RET_UNLINK: the result of USBIP_CMD_UNLINK
 *    (server to client)
 *
 */
#define USBIP_NOP		0x0000
#define USBIP_CMD_SUBMIT	0x0001
#define USBIP_CMD_UNLINK	0x0002
#define USBIP_RET_SUBMIT	0x0003
#define USBIP_RET_UNLINK	0x0004

#define USBIP_DIR_OUT	0x00
#define USBIP_DIR_IN	0x01


static inline uint8_t get_request_type(uint8_t rt)
{
	return (rt & USB_TYPE_MASK);
}

static inline uint8_t get_recipient(uint8_t rt)
{
	return (rt & USB_RECIP_MASK);
}

/**
 * struct usbip_header_basic - data pertinent to every request
 * @command: the usbip request type
 * @seqnum: sequential number that identifies requests; incremented per
 *	    connection
 * @devid: specifies a remote USB device uniquely instead of busnum and devnum;
 *	   in the stub driver, this value is ((busnum << 16) | devnum)
 * @direction: direction of the transfer
 * @ep: endpoint number
 */
struct usbip_header_basic {
	uint32_t command;
	uint32_t seqnum;
	uint32_t devid;
	uint32_t direction;
	uint32_t ep;
} __packed;

/**
 * struct usbip_header_cmd_submit - USBIP_CMD_SUBMIT packet header
 * @transfer_flags: URB flags
 * @transfer_buffer_length: the data size for (in) or (out) transfer
 * @start_frame: initial frame for isochronous or interrupt transfers
 * @number_of_packets: number of isochronous packets
 * @interval: maximum time for the request on the server-side host controller
 * @setup: setup data for a control request
 */
struct usbip_header_cmd_submit {
	uint32_t transfer_flags;
	int32_t transfer_buffer_length;

	/* it is difficult for usbip to sync frames (reserved only?) */
	int32_t start_frame;
	int32_t number_of_packets;
	int32_t interval;

	unsigned char setup[8];
} __packed;

/**
 * struct usbip_header_ret_submit - USBIP_RET_SUBMIT packet header
 * @status: return status of a non-iso request
 * @actual_length: number of bytes transferred
 * @start_frame: initial frame for isochronous or interrupt transfers
 * @number_of_packets: number of isochronous packets
 * @error_count: number of errors for isochronous transfers
 */
struct usbip_header_ret_submit {
	int32_t status;
	int32_t actual_length;
	int32_t start_frame;
	int32_t number_of_packets;
	int32_t error_count;
} __packed;

/**
 * struct usbip_header_cmd_unlink - USBIP_CMD_UNLINK packet header
 * @seqnum: the URB seqnum to unlink
 */
struct usbip_header_cmd_unlink {
	uint32_t seqnum;
} __packed;

/**
 * struct usbip_header_ret_unlink - USBIP_RET_UNLINK packet header
 * @status: return status of the request
 */
struct usbip_header_ret_unlink {
	int32_t status;
} __packed;

/**
 * struct usbip_header - common header for all usbip packets
 * @base: the basic header
 * @u: packet type dependent header
 */
struct usbip_header {
	struct usbip_header_basic base;

	union {
		struct usbip_header_cmd_submit	cmd_submit;
		struct usbip_header_ret_submit	ret_submit;
		struct usbip_header_cmd_unlink	cmd_unlink;
		struct usbip_header_ret_unlink	ret_unlink;
	} u;
} __packed;

/*
 * This is the same as usb_iso_packet_descriptor but packed for pdu.
 */
struct usbip_iso_packet_descriptor {
	uint32_t offset;
	uint32_t length;			/* expected length */
	uint32_t actual_length;
	uint32_t status;
} __packed;


#define USBIP_EH_SHUTDOWN	(1 << 0)
#define USBIP_EH_BYE		(1 << 1)
#define USBIP_EH_RESET		(1 << 2)
#define USBIP_EH_UNUSABLE	(1 << 3)

#define SDEV_EVENT_REMOVED   (USBIP_EH_SHUTDOWN | USBIP_EH_RESET | USBIP_EH_BYE)
#define	SDEV_EVENT_DOWN		(USBIP_EH_SHUTDOWN | USBIP_EH_RESET)
#define	SDEV_EVENT_ERROR_TCP	(USBIP_EH_SHUTDOWN | USBIP_EH_RESET)
#define	SDEV_EVENT_ERROR_SUBMIT	(USBIP_EH_SHUTDOWN | USBIP_EH_RESET)
#define	SDEV_EVENT_ERROR_MALLOC	(USBIP_EH_SHUTDOWN | USBIP_EH_UNUSABLE)

#define	VDEV_EVENT_REMOVED	(USBIP_EH_SHUTDOWN | USBIP_EH_BYE)
#define	VDEV_EVENT_DOWN		(USBIP_EH_SHUTDOWN | USBIP_EH_RESET)
#define	VDEV_EVENT_ERROR_TCP	(USBIP_EH_SHUTDOWN | USBIP_EH_RESET)
#define	VDEV_EVENT_ERROR_MALLOC	(USBIP_EH_SHUTDOWN | USBIP_EH_UNUSABLE)


/* a common structure for stub_device and vhci_device */
struct usbip_device {
	enum usbip_device_status status;

	/* lock for status */
	pthread_mutex_t lock;

	int sockfd;

	unsigned long event;
	pthread_t eh;
	pthread_mutex_t eh_waitq;
	int eh_should_stop;

	struct eh_ops {
		void (*shutdown)(struct usbip_device *);
		void (*reset)(struct usbip_device *);
		void (*unusable)(struct usbip_device *);
	} eh_ops;
};

int usbip_sendmsg(int sockfd, struct kvec *vec, size_t num);
int usbip_recv(int sockfd, void *buf, int size);

struct stub_unlink;

int trxstat2error(enum libusb_transfer_status trxstat);
enum libusb_transfer_status error2trxstat(int e);
void usbip_header_correct_endian(struct usbip_header *pdu, int send);


void usbip_iso_packet_correct_endian(
		struct usbip_iso_packet_descriptor *iso, int send);
void usbip_pack_iso(struct usbip_iso_packet_descriptor *iso,
			   struct libusb_iso_packet_descriptor *uiso,
			   int offset, int pack);

struct usbip_iso_packet_descriptor*
usbip_alloc_iso_desc_pdu(struct libusb_transfer *trx, ssize_t *bufflen);

/* some members of urb must be substituted before. */
int usbip_recv_iso(struct usbip_device *ud, struct libusb_transfer *trx);
int usbip_recv_xbuff(struct usbip_device *ud, struct libusb_transfer *trx,
			int offset);

/* usbip_event.c */
int usbip_start_eh(struct usbip_device *ud);
void usbip_stop_eh(struct usbip_device *ud);
void usbip_join_eh(struct usbip_device *ud);
void usbip_event_add(struct usbip_device *ud, unsigned long event);
int usbip_event_happened(struct usbip_device *ud);

#endif // __STUB_COMMON_H
