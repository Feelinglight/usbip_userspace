# SPDX-License-Identifier: GPL-2.0
libusbip_la_CPPFLAGS = -DUSBIDS_FILE='"@USBIDS_DIR@/usb.ids"'
libusbip_la_CFLAGS   = @EXTRA_CFLAGS@
libusbip_la_LDFLAGS  = -version-info @LIBUSBIP_VERSION@

lib_LIBRARIES = libusbip.la
libusbip_la_SOURCES = names.c names.h usbip_host_driver.c \
			   usbip_host_userspace/usbip_host_driver_userspace.c \
			   usbip_host_userspace/stub_logging.c usbip_host_userspace/stub_event.c \
			   usbip_host_userspace/stub_rx.c usbip_host_userspace/stub_common.c\
			   usbip_host_userspace/stub_tx.c \
			   usbip_host_userspace/stub.h usbip_host_userspace/stub.c \
			   usbip_host_driver.h usbip_device_driver.c usbip_device_driver.h \
		       usbip_common.c usbip_common.h usbip_host_common.h \
		       usbip_host_common.c vhci_driver.c vhci_driver.h \
		       ssl_utils.c ssl_utils.h \
		       sysfs_utils.c sysfs_utils.h
