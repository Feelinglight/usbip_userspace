mkdir -p build_kernel
cd build_kernel

autoreconf --install --force --verbose  "${PROJECT_DIR:-..}" 2>&1

# /bin/sh "${PROJECT_DIR:-..}/configure"

../configure --enable-stub_userspace=no 'CFLAGS=-g -O0'
make
cp config.h ..

cd ..