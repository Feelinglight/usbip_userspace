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
#include "stub_logging.h"

#ifdef CONFIG_USBIP_DEBUG
unsigned long usbip_debug_flag = 0xffffffff;
#else
// unsigned long usbip_debug_flag = 0xffffffff;
unsigned long usbip_debug_flag = 0;
#endif

int usbip_dev_printf(FILE *s, const char *level, struct libusb_device *dev)
{
	uint8_t bus = libusb_get_bus_number(dev);

	uint8_t adr = libusb_get_port_number(dev);
	// uint8_t adr = libusb_get_device_address(dev);

	return fprintf(s, "%s:%d-%d ", level, bus, adr);
}

int usbip_devh_printf(FILE *s, const char *level,
		      libusb_device_handle *dev_handle)
{
	struct libusb_device *dev = libusb_get_device(dev_handle);

	return usbip_dev_printf(s, level, dev);
}

void usbip_dump_buffer(char *buff, int bufflen)
{
	unsigned char *p = (unsigned char *)buff;
	int rem = bufflen;
	int i;
	struct b {
		char b[3];
	};
	struct b a[16];

	while (rem > 0) {
		for (i = 0; i < 16; i++) {
			if (i < rem)
				sprintf(a[i].b, "%02x", *(p+i));
			else
				a[i].b[0] = 0;
		}
		fprintf(stdout,
			"%s %s %s %s %s %s %s %s  %s %s %s %s %s %s %s %s\n",
			a[0].b, a[1].b, a[2].b, a[3].b,
			a[4].b, a[5].b, a[6].b, a[7].b,
			a[8].b, a[9].b, a[10].b, a[11].b,
			a[12].b, a[13].b, a[14].b, a[15].b);
		if (rem > 16) {
			rem -= 16;
			p += 16;
		} else {
			rem = 0;
		}
	}
}

static const char *s_trx_type_cont = "cont";
static const char *s_trx_type_isoc = "isoc";
static const char *s_trx_type_bulk = "bulk";
static const char *s_trx_type_intr = "intr";
static const char *s_trx_type_blks = "blks";
static const char *s_trx_type_unknown = "????";

static const char *get_trx_type_str(uint8_t type)
{
	switch (type) {
	case LIBUSB_TRANSFER_TYPE_CONTROL:
		return s_trx_type_cont;
	case LIBUSB_TRANSFER_TYPE_ISOCHRONOUS:
		return s_trx_type_isoc;
	case LIBUSB_TRANSFER_TYPE_BULK:
		return s_trx_type_bulk;
	case LIBUSB_TRANSFER_TYPE_INTERRUPT:
		return s_trx_type_intr;
	case LIBUSB_TRANSFER_TYPE_BULK_STREAM:
		return s_trx_type_blks;
	}
	return s_trx_type_unknown;
}

static void get_endpoint_descs(struct libusb_config_descriptor *config,
	const struct libusb_endpoint_descriptor *in[],
	const struct libusb_endpoint_descriptor *out[], int max)
{
	int i, j, k;
	const struct libusb_interface *intf;
	const struct libusb_interface_descriptor *desc;
	const struct libusb_endpoint_descriptor *ep;
	uint8_t dir;
	int num_in = 0;
	int num_out = 0;

	for (k = 0; k < max; k++) {
		in[k] = NULL;
		out[k] = NULL;
	}
	for (i = 0; i < config->bNumInterfaces; i++) {
		intf = config->interface + i;
		for (j = 0; j < intf->num_altsetting; j++) {
			desc = intf->altsetting + j;
			for (k = 0; k < desc->bNumEndpoints; k++) {
				ep = desc->endpoint + k;
				dir = ep->bEndpointAddress & 0x80;
				if (dir == LIBUSB_ENDPOINT_IN
					&& num_in < max) {
					in[num_in++] = ep;
				} else if (dir == LIBUSB_ENDPOINT_OUT
					&& num_out < max) {
					out[num_out++] = ep;
				}
			}
		}
	}
}

static void usbip_dump_ep_max(const struct libusb_endpoint_descriptor *ep[],
			      char *buf)
{
	int i;

	for (i = 0; i < 16; i++) {
		sprintf(buf+(3*i), " %2u", (ep[i]) ?
			libusb_le16_to_cpu(ep[i]->wMaxPacketSize) : 0);
	}
}

static void usbip_dump_usb_device(struct libusb_device *dev)
{
	struct libusb_device_descriptor desc;
	struct libusb_config_descriptor *config;
	int config_acquired = 0;
	const struct libusb_endpoint_descriptor *in[16], *out[16];
	char buf[3*16+1];

	if (libusb_get_device_descriptor(dev, &desc))
		dev_err(dev, "fail to get desc\n");

	if (libusb_get_active_config_descriptor(dev, &config) == 0)
		config_acquired = 1;

	dev_dbg(dev, "addr(%d)\n",
		// libusb_get_device_address(dev));
		libusb_get_port_number(dev));
	/* TODO: device number, device path */
	/* TODO: Transaction Translator info, tt */

	/* TODO: Toggle */

	if (config_acquired) {
		get_endpoint_descs(config, in, out, 16);
		usbip_dump_ep_max(in, buf);
		dev_dbg(dev, "epmaxp_in   :%s\n", buf);
		usbip_dump_ep_max(out, buf);
		dev_dbg(dev, "epmaxp_out  :%s\n", buf);
	}

	/* TODO: bus pointer */
	dev_dbg(dev, "parent %p\n",
		libusb_get_parent(dev));

	/* TODO: all configs pointer, raw descs */
	dev_dbg(dev, "vendor:0x%x product:0x%x actconfig:%p\n",
		desc.idVendor, desc.idProduct, config);

	/* TODO: have_lang, have_langid */

	/* TODO: maxchild */

	if (config_acquired)
		libusb_free_config_descriptor(config);
}

static const char *s_recipient_device    = "DEVC";
static const char *s_recipient_interface = "INTF";
static const char *s_recipient_endpoint  = "ENDP";
static const char *s_recipient_other = "OTHR";
static const char *s_recipient_unknown   = "????";

static const char *get_request_recipient_str(uint8_t rt)
{
	uint8_t recip = get_recipient(rt);

	switch (recip) {
	case LIBUSB_RECIPIENT_DEVICE:
		return s_recipient_device;
	case LIBUSB_RECIPIENT_INTERFACE:
		return s_recipient_interface;
	case LIBUSB_RECIPIENT_ENDPOINT:
		return s_recipient_endpoint;
	case LIBUSB_RECIPIENT_OTHER:
		return s_recipient_other;
	}
	return s_recipient_unknown;
}

static const char *s_request_get_status     = "GET_STATUS";
static const char *s_request_clear_feature  = "CLEAR_FEAT";
static const char *s_request_set_feature    = "SET_FEAT  ";
static const char *s_request_set_address    = "SET_ADDRRS";
static const char *s_request_get_descriptor = "GET_DESCRI";
static const char *s_request_set_descriptor = "SET_DESCRI";
static const char *s_request_get_config     = "GET_CONFIG";
static const char *s_request_set_config     = "SET_CONFIG";
static const char *s_request_get_interface  = "GET_INTERF";
static const char *s_request_set_interface  = "SET_INTERF";
static const char *s_request_sync_frame     = "SYNC_FRAME";
static const char *s_request_unknown        = "????      ";

static const char *get_request_str(uint8_t req)
{
	switch (req) {
	case LIBUSB_REQUEST_GET_STATUS:
		return s_request_get_status;
	case LIBUSB_REQUEST_CLEAR_FEATURE:
		return s_request_clear_feature;
	case LIBUSB_REQUEST_SET_FEATURE:
		return s_request_set_feature;
	case LIBUSB_REQUEST_SET_ADDRESS:
		return s_request_set_address;
	case LIBUSB_REQUEST_GET_DESCRIPTOR:
		return s_request_get_descriptor;
	case LIBUSB_REQUEST_SET_DESCRIPTOR:
		return s_request_set_descriptor;
	case LIBUSB_REQUEST_GET_CONFIGURATION:
		return s_request_get_config;
	case LIBUSB_REQUEST_SET_CONFIGURATION:
		return s_request_set_config;
	case LIBUSB_REQUEST_GET_INTERFACE:
		return s_request_get_interface;
	case LIBUSB_REQUEST_SET_INTERFACE:
		return s_request_set_interface;
	case LIBUSB_REQUEST_SYNCH_FRAME:
		return s_request_sync_frame;
	}
	return s_request_unknown;
}

static void usbip_dump_usb_ctrlrequest(struct libusb_device *dev,
		struct libusb_transfer *trx)
{
	struct libusb_control_setup *cmd =
		libusb_control_transfer_get_setup(trx);

	if (!cmd) {
		dev_dbg(dev, "null control\n");
		return;
	}

	dev_dbg(dev, "bRequestType(%02X) bRequest(%02X) ",
		cmd->bmRequestType, cmd->bRequest);
	dev_dbg(dev, "wValue(%04X) wIndex(%04X) wLength(%04X)\n",
		cmd->wValue, cmd->wIndex, cmd->wLength);

	switch (cmd->bmRequestType & USB_TYPE_MASK) {
	case LIBUSB_REQUEST_TYPE_STANDARD:
		dev_dbg(dev, "STANDARD %s %s\n",
			get_request_str(cmd->bRequest),
			get_request_recipient_str(cmd->bmRequestType));
		break;
	case LIBUSB_REQUEST_TYPE_CLASS:
		dev_dbg(dev, "CLASS\n");
		break;
	case LIBUSB_REQUEST_TYPE_VENDOR:
		dev_dbg(dev, "VENDOR\n");
		break;
	case LIBUSB_REQUEST_TYPE_RESERVED:
		dev_dbg(dev, "RESERVED\n");
		break;
	}
}

void usbip_dump_trx(struct libusb_transfer *trx)
{
	struct libusb_device *dev;

	if (!trx) {
		pr_debug("trx: null pointer!!\n");
		return;
	}

	if (!trx->dev_handle) {
		pr_debug("trx->dev_handle: null pointer!!\n");
		return;
	}

	dev = libusb_get_device(trx->dev_handle);

	dev_dbg(dev, "   trx          :%p\n", trx);
	dev_dbg(dev, "   dev_handle   :%p\n", trx->dev_handle);
	dev_dbg(dev, "   trx_type     :%s\n", get_trx_type_str(trx->type));
	dev_dbg(dev, "   endpoint     :%08x\n", trx->endpoint);
	dev_dbg(dev, "   status       :%d\n", trx->status);
	dev_dbg(dev, "   trx_flags    :%08X\n", trx->flags);
	dev_dbg(dev, "   buffer       :%p\n", trx->buffer);
	dev_dbg(dev, "   buffer_length:%d\n", trx->length);
	dev_dbg(dev, "   actual_length:%d\n", trx->actual_length);
	dev_dbg(dev, "   num_packets  :%d\n", trx->num_iso_packets);
	dev_dbg(dev, "   context      :%p\n", trx->user_data);
	dev_dbg(dev, "   complete     :%p\n", trx->callback);

	if (trx->type == LIBUSB_TRANSFER_TYPE_CONTROL)
		usbip_dump_usb_ctrlrequest(dev, trx);

	usbip_dump_usb_device(dev);
}

void usbip_dump_header(struct usbip_header *pdu)
{
	pr_debug("BASE: cmd %u seq %u devid %u dir %u ep %u\n",
		 pdu->base.command,
		 pdu->base.seqnum,
		 pdu->base.devid,
		 pdu->base.direction,
		 pdu->base.ep);

	switch (pdu->base.command) {
	case USBIP_CMD_SUBMIT:
		pr_debug("USBIP_CMD_SUBMIT: xflg %x xln %u sf %x #p %d iv %d\n",
			 pdu->u.cmd_submit.transfer_flags,
			 pdu->u.cmd_submit.transfer_buffer_length,
			 pdu->u.cmd_submit.start_frame,
			 pdu->u.cmd_submit.number_of_packets,
			 pdu->u.cmd_submit.interval);
		break;
	case USBIP_CMD_UNLINK:
		pr_debug("USBIP_CMD_UNLINK: seq %u\n",
			 pdu->u.cmd_unlink.seqnum);
		break;
	case USBIP_RET_SUBMIT:
		pr_debug("USBIP_RET_SUBMIT: st %d al %u sf %x #p %d ec %d\n",
			 pdu->u.ret_submit.status,
			 pdu->u.ret_submit.actual_length,
			 pdu->u.ret_submit.start_frame,
			 pdu->u.ret_submit.number_of_packets,
			 pdu->u.ret_submit.error_count);
		break;
	case USBIP_RET_UNLINK:
		pr_debug("USBIP_RET_UNLINK: status %d\n",
			 pdu->u.ret_unlink.status);
		break;
	case USBIP_NOP:
		pr_debug("USBIP_NOP\n");
		break;
	default:
		/* NOT REACHED */
		pr_err("unknown command\n");
		break;
	}
}
