#include <arpa/inet.h>
#include <errno.h>
#include <assert.h>

#include "stub_common.h"
#include "stub_logging.h"

/* Send data over TCP/IP. */
int usbip_sendmsg(SSL* ssl_conn, struct kvec *vec, size_t num)
{
	int i, result;
	struct kvec *iov;
	size_t total = 0;

	usbip_dbg_xmit("enter usbip_sendmsg %zd\n", num);

	for (i = 0; i < (int)num; i++) {
		iov = vec+i;

		if (iov->iov_len == 0)
			continue;

		if (usbip_dbg_flag_xmit) {
			pr_debug("sending, idx %d size %zd\n",
					i, iov->iov_len);
			usbip_dump_buffer((char *)(iov->iov_base),
					iov->iov_len);
		}

		result = SSL_write(ssl_conn, (char *)(iov->iov_base),
			iov->iov_len);

		if (result < 0) {
			pr_debug("send err sock 0x%p buf %p size %zu ",
				ssl_conn, iov->iov_base, iov->iov_len);
			pr_debug("ret %d total %zd\n", result, total);
			return total;
		}
		total += result;
	}
	return total;
}

/* Receive data over TCP/IP. */
int usbip_recv(SSL* ssl_conn, void *buf, int size)
{
	int result;
	int total = 0;

	/* for blocks of if (usbip_dbg_flag_xmit) */
	char *bp = (char *)buf;
	int osize = size;

	usbip_dbg_xmit("enter usbip_recv\n");

	if (!buf || !size) {
		pr_err("invalid arg, buff %p size %d\n",
			buf, size);
		errno = EINVAL;
		return -1;
	}

	do {
		usbip_dbg_xmit("receiving %d\n", size);
			result = SSL_read(ssl_conn, bp, size);

		if (result <= 0) {
			pr_debug("receive err buf %p size %u ",
				buf, size);
			pr_debug("ret %d total %d\n",
				result, total);
			goto err;
		}

		size -= result;
		bp += result;
		total += result;
	} while (size > 0);

	if (usbip_dbg_flag_xmit) {
		pr_debug("received, osize %d ret %d size %d total %d\n",
			 osize, result, size, total);
		usbip_dump_buffer((char *)buf, osize);
	}

	return total;

err:
	return result;
}

int trxstat2error(enum libusb_transfer_status trxstat)
{
	switch (trxstat) {
	case LIBUSB_TRANSFER_COMPLETED:
		return 0;
	case LIBUSB_TRANSFER_CANCELLED:
		return -ECONNRESET;
	case LIBUSB_TRANSFER_ERROR:
	case LIBUSB_TRANSFER_STALL:
	case LIBUSB_TRANSFER_TIMED_OUT:
	case LIBUSB_TRANSFER_OVERFLOW:
		return -EPIPE;
	case LIBUSB_TRANSFER_NO_DEVICE:
		return -ESHUTDOWN;
	}
	return -ENOENT;
}

enum libusb_transfer_status error2trxstat(int e)
{
	switch (e) {
	case 0:
		return LIBUSB_TRANSFER_COMPLETED;
	case -ENOENT:
		return LIBUSB_TRANSFER_ERROR;
	case -ECONNRESET:
		return LIBUSB_TRANSFER_CANCELLED;
	case -ETIMEDOUT:
		return LIBUSB_TRANSFER_TIMED_OUT;
	case -EPIPE:
		return LIBUSB_TRANSFER_STALL;
	case -ESHUTDOWN:
		return LIBUSB_TRANSFER_NO_DEVICE;
	case -EOVERFLOW:
		return LIBUSB_TRANSFER_OVERFLOW;
	}
	return LIBUSB_TRANSFER_ERROR;
}

static void correct_endian_basic(struct usbip_header_basic *base, int send)
{
	if (send) {
		base->command	= htonl(base->command);
		base->seqnum	= htonl(base->seqnum);
		base->devid	= htonl(base->devid);
		base->direction	= htonl(base->direction);
		base->ep	= htonl(base->ep);
	} else {
		base->command	= ntohl(base->command);
		base->seqnum	= ntohl(base->seqnum);
		base->devid	= ntohl(base->devid);
		base->direction	= ntohl(base->direction);
		base->ep	= ntohl(base->ep);
	}
}

static void correct_endian_cmd_submit(struct usbip_header_cmd_submit *pdu,
				      int send)
{
	if (send) {
		pdu->transfer_flags = htonl(pdu->transfer_flags);

		pdu->transfer_buffer_length =
			(int32_t)htonl(pdu->transfer_buffer_length);
		pdu->start_frame = (int32_t)htonl(pdu->start_frame);
		pdu->number_of_packets = (int32_t)htonl(pdu->number_of_packets);
		pdu->interval = (int32_t)htonl(pdu->interval);
	} else {
		pdu->transfer_flags = ntohl(pdu->transfer_flags);

		pdu->transfer_buffer_length =
			(int32_t)ntohl(pdu->transfer_buffer_length);
		pdu->start_frame = (int32_t)ntohl(pdu->start_frame);
		pdu->number_of_packets = (int32_t)ntohl(pdu->number_of_packets);
		pdu->interval = (int32_t)ntohl(pdu->interval);
	}
}

static void correct_endian_ret_submit(struct usbip_header_ret_submit *pdu,
				      int send)
{
	if (send) {
		pdu->status = (int32_t)htonl(pdu->status);
		pdu->actual_length = (int32_t)htonl(pdu->actual_length);
		pdu->start_frame = (int32_t)htonl(pdu->start_frame);
		pdu->number_of_packets = (int32_t)htonl(pdu->number_of_packets);
		pdu->error_count = (int32_t)htonl(pdu->error_count);
	} else {
		pdu->status = (int32_t)ntohl(pdu->status);
		pdu->actual_length = (int32_t)ntohl(pdu->actual_length);
		pdu->start_frame = (int32_t)ntohl(pdu->start_frame);
		pdu->number_of_packets = (int32_t)ntohl(pdu->number_of_packets);
		pdu->error_count = (int32_t)ntohl(pdu->error_count);
	}
}

static void correct_endian_cmd_unlink(struct usbip_header_cmd_unlink *pdu,
				      int send)
{
	if (send)
		pdu->seqnum = htonl(pdu->seqnum);
	else
		pdu->seqnum = ntohl(pdu->seqnum);
}

static void correct_endian_ret_unlink(struct usbip_header_ret_unlink *pdu,
				      int send)
{
	if (send)
		pdu->status = (int32_t)htonl(pdu->status);
	else
		pdu->status = ntohl(pdu->status);
}

void usbip_header_correct_endian(struct usbip_header *pdu, int send)
{
	uint32_t cmd = 0;

	if (send)
		cmd = pdu->base.command;

	correct_endian_basic(&pdu->base, send);

	if (!send)
		cmd = pdu->base.command;

	switch (cmd) {
	case USBIP_CMD_SUBMIT:
		correct_endian_cmd_submit(&pdu->u.cmd_submit, send);
		break;
	case USBIP_RET_SUBMIT:
		correct_endian_ret_submit(&pdu->u.ret_submit, send);
		break;
	case USBIP_CMD_UNLINK:
		correct_endian_cmd_unlink(&pdu->u.cmd_unlink, send);
		break;
	case USBIP_RET_UNLINK:
		correct_endian_ret_unlink(&pdu->u.ret_unlink, send);
		break;
	case USBIP_NOP:
		break;
	default:
		/* NOT REACHED */
		pr_err("unknown command\n");
		break;
	}
}

void usbip_iso_packet_correct_endian(
		struct usbip_iso_packet_descriptor *iso, int send)
{
	/* does not need all members. but copy all simply. */
	if (send) {
		iso->offset	= htonl(iso->offset);
		iso->length	= htonl(iso->length);
		iso->status	= htonl(iso->status);
		iso->actual_length = htonl(iso->actual_length);
	} else {
		iso->offset	= ntohl(iso->offset);
		iso->length	= ntohl(iso->length);
		iso->status	= ntohl(iso->status);
		iso->actual_length = ntohl(iso->actual_length);
	}
}

void usbip_pack_iso(struct usbip_iso_packet_descriptor *iso,
			   struct libusb_iso_packet_descriptor *uiso,
			   int offset, int pack)
{
	if (pack) {
		iso->offset		= offset;
		iso->length		= uiso->length;
		iso->status		= trxstat2error(uiso->status);
		iso->actual_length	= uiso->actual_length;
	} else {
		/* ignore iso->offset; */
		uiso->length		= iso->length;
		uiso->status		= error2trxstat(iso->status);
		uiso->actual_length	= iso->actual_length;
	}
}

/* some members of urb must be substituted before. */
int usbip_recv_xbuff(struct usbip_device *ud, struct libusb_transfer *trx,
		     int offset)
{
	int ret;
	int size;

	size = trx->length - offset;

	/* no need to recv xbuff */
	if (!(size > 0))
		return 0;

    /* should not happen, probably malicious packet */
    assert(size <= trx->length - offset);

    // TODO: sgs
	/*
	 * Take offset for CONTROL setup
	 */
	ret = usbip_recv(ud->ssl_conn, trx->buffer + offset, size);
	if (ret != size) {
		devh_err(trx->dev_handle, "recv xbuf, %d\n", ret);
		usbip_event_add(ud, SDEV_EVENT_ERROR_TCP);
	}

	return ret;
}

/* some members of urb must be substituted before. */
int usbip_recv_iso(struct usbip_device *ud, struct libusb_transfer *trx)
{
	void *buff;
	struct usbip_iso_packet_descriptor *iso;
	int np = trx->num_iso_packets;
	int size = np * sizeof(*iso);
	int i;
	int ret;
	int total_length = 0;

	/* my Bluetooth dongle gets ISO URBs which are np = 0 */
	if (np == 0)
		return 0;

	buff = malloc(size);
	if (!buff) {
		errno = ENOMEM;
		return -1;
	}

	ret = usbip_recv(ud->ssl_conn, buff, size);
	if (ret != size) {
		devh_err(trx->dev_handle,
			"recv iso_frame_descriptor, %d\n", ret);
		free(buff);
		usbip_event_add(ud, SDEV_EVENT_ERROR_TCP);
		errno = EPIPE;
		return -1;
	}

	iso = (struct usbip_iso_packet_descriptor *) buff;
	for (i = 0; i < np; i++) {
		usbip_iso_packet_correct_endian(&iso[i], 0);
		usbip_pack_iso(&iso[i], &trx->iso_packet_desc[i], 0, 0);
		total_length += trx->iso_packet_desc[i].actual_length;
	}

	free(buff);

	if (total_length != trx->actual_length) {
		devh_err(trx->dev_handle,
			"total length of iso packets %d not equal to actual ",
			total_length);
		devh_err(trx->dev_handle,
			"length of buffer %d\n",
			trx->actual_length);
		usbip_event_add(ud, SDEV_EVENT_ERROR_TCP);
		errno = EPIPE;
		return -1;
	}

	return ret;
}
