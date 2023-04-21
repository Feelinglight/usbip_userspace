#ifndef __STUB_COMMON_H
#define __STUB_COMMON_H

#include "usbip_common.h"
#include "stub_logging.h"


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

/* usbip_event.c */
int usbip_start_eh(struct usbip_device *ud);
void usbip_stop_eh(struct usbip_device *ud);
void usbip_join_eh(struct usbip_device *ud);
void usbip_event_add(struct usbip_device *ud, unsigned long event);
int usbip_event_happened(struct usbip_device *ud);

#endif // __STUB_COMMON_H
