#!/bin/bash

# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev

# Download CMake source code
# https://github.com/Kitware/CMake
wget https://github.com/Kitware/CMake/releases/download/v3.26.3/cmake-3.26.3.tar.gz

# Extract the source code
tar -xzvf cmake-3.26.3.tar.gz

# Navigate to the source code directory
cd cmake-3.26.3

# Create a build directory and enter it
mkdir build
cd build

# Run CMake configuration
../bootstrap --prefix=/opt/cmake

# Compile and install
make -j$(nproc) || make
sudo make install

# Verify the installation
/opt/cmake/bin/cmake --version

# Add to env
echo 'export PATH="/opt/cmake/bin:$PATH"' | sudo tee -a /etc/profile
source /etc/profile
