#!/bin/sh -x

#aclocal
#autoheader
#libtoolize --copy --force
#automake-1.9 -acf
#autoconf

mkdir -p build
cd build
autoreconf --install --force --verbose "${PROJECT_DIR:-..}" 2>&1; /bin/sh "${PROJECT_DIR:-..}/configure" 'CFLAGS=-g -O0'
cd ..
# autoreconf -i -f -v
