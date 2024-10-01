---
title:  "install gcc 7.3.0 from souce"
date:   2024-08-18 20:53:00 +0800
last_modified_at: 2024-08-31 20:47:00 +0800
categories: gcc
tags: gcc7.3.0
---

# install gcc 7.3.0 from souce  

## 1. Some notes on compiling  
1> Some [dependencies](https://gcc.gnu.org/install/prerequisites.html) are necessary for compiling.  
They are **gmp-6.1.0, mpfr-3.1.4, mpc-1.0.3**, isl-0.16.1 for gcc 7.3.0.  
You can download them by run shell **`download_prerequisites`** when there is Internet.  
Or you can install the packages libgmp-dev, libmpfr-dev and libmpc-dev for debian(or ubuntu).  
Or you can download them manually.  

(1) GNU Multiple Precision Library (GMP). It can be [downloaded](https://gmplib.org/).  
(2) MPFR Library. It can be [downloaded](https://www.mpfr.org).  
(3) MPC Library. It can be [downloaded](https://www.multiprecision.org/mpc/).  
(4) isl Library. It can be [downloaded](https://gcc.gnu.org/pub/gcc/infrastructure/).  

2>**Do not run ./configure from within the source directory, this is not supported.**  
You need to run configure from outside the source directory, in a separate directory created for the build.  


## 2. Install From source  
[releases web page](https://gcc.gnu.org/releases.html) or [github releases](https://github.com/gcc-mirror/gcc/tags) for gcc src code.  

```
# Prepare building toolchain  
apt install gcc     # version >= 4.8.3  
apt install make    # version >= 3.8  
apt install g++     # version >= 4.8.3 if c++ is enable  

gcc_version=7.3.0
wget https://ftp.gnu.org/gnu/gcc/gcc-${gcc_version}/gcc-${gcc_version}.tar.gz
wget https://ftp.gnu.org/gnu/gcc/gcc-${gcc_version}/gcc-${gcc_version}.tar.gz.sig
wget https://ftp.gnu.org/gnu/gnu-keyring.gpg

signature_invalid=`gpg --verify --no-default-keyring --keyring ./gnu-keyring.gpg gcc-${gcc_version}.tar.gz.sig`
if [ $signature_invalid ]; then echo "Invalid signature" ; exit 1 ; fi

tar -zxvf gcc-${gcc_version}.tar.gz
cd gcc-${gcc_version}
./contrib/download_prerequisites
cd ..

mkdir gcc-${gcc_version}-build
cd gcc-${gcc_version}-build
$PWD/../gcc-${gcc_version}/configure --prefix=/opt/softwares --enable-languages=c,c++ --disable-multilib

make
make install
```
**NOTE 1**:  
The shell script `download_prerequisites` do things like:  
(wget --no-verbose -O ./gmp-6.1.0.tar.bz2 ftp://gcc.gnu.org/pub/gcc/infrastructure/gmp-6.1.0.tar.bz2)  
(wget --no-verbose -O ./mpfr-3.1.4.tar.bz2 ftp://gcc.gnu.org/pub/gcc/infrastructure/mpfr-3.1.4.tar.bz2)  
(wget --no-verbose -O ./mpc-1.0.3.tar.gz ftp://gcc.gnu.org/pub/gcc/infrastructure/mpc-1.0.3.tar.gz)  
(wget --no-verbose -O ./isl-0.16.1.tar.bz2 ftp://gcc.gnu.org/pub/gcc/infrastructure/isl-0.16.1.tar.bz2)  
**NOTE 2**:  
configure: error: I suspect your system does not have 32-bit development libraries (libc and headers).  
If you have them, rerun configure with --enable-multilib.  
If you do not have them, and want to build a 64-bit-only compiler, rerun configure with --disable-multilib.  

## 3. Reference  
[Install docu](https://gcc.gnu.org/wiki/InstallingGCC)  
[Install guide](https://gcc.gnu.org/install/index.html)  
[Install prerequisites](https://gcc.gnu.org/install/prerequisites.html)  
[Install configure](https://gcc.gnu.org/install/configure.html)  
[wiki FAQ configure](https://gcc.gnu.org/wiki/FAQ#configure)  
