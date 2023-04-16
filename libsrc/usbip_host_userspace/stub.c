#include "stub.h"


static void clear_usbip_device(struct usbip_device *ud)
{
	pthread_mutex_destroy(&ud->lock);
}

void stub_device_delete(struct stub_device *sdev)
{
	clear_usbip_device(&sdev->ud);
	pthread_mutex_destroy(&sdev->priv_lock);
	pthread_mutex_destroy(&sdev->tx_waitq);
	free(sdev);
}
