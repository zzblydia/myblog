#!/bin/bash
# v0.0.1 openssl 3.0.12 install on debian 11.8

# Install necessary build tools and dependencies
sudo apt-get update
sudo apt-get install -y build-essential zlib1g-dev

# Download and extract OpenSSL source code
wget https://www.openssl.org/source/openssl-3.0.12.tar.gz
tar -xf openssl-3.0.12.tar.gz
cd openssl-3.0.12

# Configure and compile OpenSSL
sudo mkdir /opt/openssl
./config --prefix=/opt/openssl --openssldir=/opt/openssl
make -j$(nproc) || make

# (Optional) Install OpenSSL
sudo make install

# env
echo 'export PATH="/opt/openssl/bin:$PATH"' >> /etc/profile

# ./openssl version
# ./openssl: error while loading shared libraries: libssl.so.3: cannot open shared object file: No such file or directory
sudo vi /etc/ld.so.conf.d/openssl.conf
/opt/openssl/lib64
sudo ldconfig
sudo ldconfig -p | grep ssl
