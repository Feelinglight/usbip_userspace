#include "usbip_common.h"
#include "stub_logging.h"


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
