// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Copyright (C) 2011 matt mooney <mfm@muteddisk.com>
 *               2005-2007 Takahiro Hirofuchi
 */

#include <libudev.h>

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <getopt.h>

#include "usbip_common.h"
#include "usbip_host_driver.h"
#include "utils.h"
#include "usbip.h"
#include "sysfs_utils.h"

static const char usbip_unbind_usage_string[] =
	"usbip unbind <args>\n"
	"    -b, --busid=<busid>    Unbind " USBIP_HOST_DRV_NAME ".ko from "
	"device on <busid>\n";

void usbip_unbind_usage(void)
{
	printf("usage: %s", usbip_unbind_usage_string);
}



int usbip_unbind(int argc, char *argv[])
{
	static const struct option opts[] = {
		{ "busid", required_argument, NULL, 'b' },
		{ NULL,    0,                 NULL,  0  }
	};

	int opt;
	int ret = -1;

	for (;;) {
		opt = getopt_long(argc, argv, "b:", opts, NULL);

		if (opt == -1)
			break;

		switch (opt) {
		case 'b':
			ret = host_driver.ops.unbind_device(optarg);
			goto out;
		default:
			goto err_out;
		}
	}

err_out:
	usbip_unbind_usage();
out:
	return ret;
}
