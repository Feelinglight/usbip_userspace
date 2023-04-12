mkdir -p build
cd build

autoreconf --install --force --verbose  "${PROJECT_DIR:-..}" 2>&1

# /bin/sh "${PROJECT_DIR:-..}/configure"

../configure --enable-stub_userspace=yes 'CFLAGS=-g -O0'
make
cp config.h ..

cd ..