#!/bin/bash

echo "Provisioning Mininet VM"

#echo "Bootstrapping VM"
sudo apt-get update
#echo "apt-get update"
#
sudo apt install python3-pip -y

sudo apt-get install -y net-tools
git clone https://github.com/mininet/mininet
sudo mininet/util/install.sh -a

git clone https://github.com/scy-phy/minicps.git
cd minicps
sudo pip install .



#sudo apt-get install -y python2 python-is-python2 unzip net-tools
#
#
#
#echo "Cloning Mininet (latest)"
#git clone https://github.com/mininet/mininet
#
#
#
#echo "mininet/util/install.sh -a"
#echo "Installing"
#sudo PYTHON=python3 mininet/util/install.sh -a
