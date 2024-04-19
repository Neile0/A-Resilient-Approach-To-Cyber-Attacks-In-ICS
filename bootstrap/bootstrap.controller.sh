#!/bin/bash

echo "Provisioning Controller"

sudo apt-get update

sudo apt install net-tools

sudo apt install python3-pip -y

sudo pip install flask

git clone https://github.com/faucetsdn/ryu.git
cd ryu
sudo pip install .

cd ~/

git clone https://github.com/scy-phy/minicps.git
cd minicps
sudo pip install .
