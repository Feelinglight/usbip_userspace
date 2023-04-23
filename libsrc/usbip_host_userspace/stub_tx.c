#include "stub.h"
#include "stub_logging.h"

// TODO: sgs
static void stub_free_priv_and_trx(struct stub_priv *priv)
{
	struct libusb_transfer *trx = priv->trx;

	free(trx->buffer);
	list_del(&priv->list);
	free(priv);
	usbip_dbg_stub_tx("freeing trx %p\n", trx);
	libusb_free_transfer(trx);
}


/* be in spin_lock_irqsave(&sdev->priv_lock, flags) */
void stub_enqueue_ret_unlink(struct stub_device *sdev, uint32_t seqnum,
			     enum libusb_transfer_status status)
{
	struct stub_unlink *unlink;

	unlink = (struct stub_unlink *)calloc(1, sizeof(struct stub_unlink));
	if (!unlink) {
		usbip_event_add(&sdev->ud, VDEV_EVENT_ERROR_MALLOC);
		return;
	}

	unlink->seqnum = seqnum;
	unlink->status = status;

	list_add(&unlink->list, sdev->unlink_tx.prev);
}

/**
 * stub_complete - completion handler of a usbip urb
 * @urb: pointer to the urb completed
 *
 * When a urb has completed, the USB core driver calls this function mostly in
 * the interrupt context. To return the result of a urb, the completed urb is
 * linked to the pending list of returning.
 *
 */
// TODO: sgs
void LIBUSB_CALL stub_complete(struct libusb_transfer *trx)
{
	struct stub_priv *priv = (struct stub_priv *) trx->user_data;
	struct stub_device *sdev = priv->sdev;

	usbip_dbg_stub_tx("complete %p! status %d\n", trx, trx->status);

	switch (trx->status) {
	case LIBUSB_TRANSFER_COMPLETED:
		/* OK */
		break;
	case LIBUSB_TRANSFER_ERROR:
		devh_info(trx->dev_handle,
			"error on endpoint %d\n", trx->endpoint);
		break;
	case LIBUSB_TRANSFER_CANCELLED:
		devh_info(trx->dev_handle,
			"unlinked by a call to usb_unlink_urb()\n");
		break;
	case LIBUSB_TRANSFER_STALL:
		devh_info(trx->dev_handle,
			"endpoint %d is stalled\n", trx->endpoint);
		break;
	case LIBUSB_TRANSFER_NO_DEVICE:
		devh_info(trx->dev_handle, "device removed?\n");
		break;
	default:
		devh_info(trx->dev_handle,
			"urb completion with non-zero status %d\n",
			trx->status);
		break;
	}

	/* link a urb to the queue of tx. */
	pthread_mutex_lock(&sdev->priv_lock);
	if (priv->unlinking) {
		stub_enqueue_ret_unlink(sdev, priv->seqnum, trx->status);
		stub_free_priv_and_trx(priv);
	} else {
		list_del(&priv->list);
		list_add(&priv->list, sdev->priv_tx.prev);
	}
	pthread_mutex_unlock(&sdev->priv_lock);

	/* wake up tx_thread */
	pthread_mutex_unlock(&sdev->tx_waitq);
}
