#include "stub.h"
#include "stub_logging.h"

static unsigned long event_get(struct usbip_device *ud)
{
	unsigned long event;

	pthread_mutex_lock(&ud->lock);
	event = ud->event;
	ud->event = 0;
	pthread_mutex_unlock(&ud->lock);

	return event;
}

static int event_handler(struct usbip_device *ud)
{
	unsigned long event = event_get(ud);

	usbip_dbg_eh("enter event_handler\n");

	/*
	 * Events are handled by only this thread.
	 */
	usbip_dbg_eh("pending event %lx\n", event);

	/*
	 * NOTE: shutdown must come first.
	 * Shutdown the device.
	 */
	if (event & USBIP_EH_SHUTDOWN)
		ud->eh_ops.shutdown(ud);

	/* Reset the device. */
	if (event & USBIP_EH_RESET)
		ud->eh_ops.reset(ud);

	/* Mark the device as unusable. */
	if (event & USBIP_EH_UNUSABLE)
		ud->eh_ops.unusable(ud);

	/* Stop the error handler. */
	if (event & USBIP_EH_BYE)
		return -1;

	return 0;
}

static void *event_handler_loop(void *data)
{
	struct usbip_device *ud = (struct usbip_device *)data;

	while (!ud->eh_should_stop) {
		pthread_mutex_lock(&ud->eh_waitq);
		usbip_dbg_eh("wakeup\n");

		if (event_handler(ud) < 0)
			break;
	}

	return 0;
}

int usbip_start_eh(struct usbip_device *ud)
{
	pthread_mutex_init(&ud->eh_waitq, NULL);
	ud->eh_should_stop = 0;
	ud->event = 0;

	if (pthread_create(&ud->eh, NULL, event_handler_loop, ud)) {
		pr_warn("Unable to start control thread\n");
		return -1;
	}
	return 0;
}

void usbip_stop_eh(struct usbip_device *ud)
{
	usbip_dbg_eh("finishing usbip_eh\n");
	ud->eh_should_stop = 1;
	pthread_mutex_unlock(&ud->eh_waitq);
}

void usbip_join_eh(struct usbip_device *ud)
{
	pthread_join(ud->eh, NULL);
	pthread_mutex_destroy(&ud->eh_waitq);
}

void usbip_event_add(struct usbip_device *ud, unsigned long event)
{
	pthread_mutex_lock(&ud->lock);
	ud->event |= event;
	pthread_mutex_unlock(&ud->lock);
	pthread_mutex_unlock(&ud->eh_waitq);
}

int usbip_event_happened(struct usbip_device *ud)
{
	int happened = 0;

	pthread_mutex_lock(&ud->lock);
	if (ud->event != 0)
		happened = 1;
	pthread_mutex_unlock(&ud->lock);

	return happened;
}
