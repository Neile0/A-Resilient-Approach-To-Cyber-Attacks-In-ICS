#!/bin/bash

echo "Provisioning Controller"

sudo apt-get update

sudo apt install net-tools
sudo apt install build-essential python-dev -y
sudo apt install openjdk-8-jdk maven ant git -y

sudo update-java-alternatives --set /usr/lib/jvm/java-1.8.0-openjdk-amd64

sudo git clone https://github.com/floodlight/floodlight.git

cd floodlight
cd lib

sudo wget https://repo1.maven.org/maven2/org/apache/thrift/libthrift/0.14.1/libthrift-0.14.1.jar

sudo wget https://repo1.maven.org/maven2/io/netty/netty-all/4.1.66.Final/netty-all-4.1.66.Final.jar

cd ..

sudo sed -i 's/netty-all-4.0.31.Final.jar/netty-all-4.1.66.Final.jar/g' build.xml
sudo sed -i 's/libthrift-0.9.0.jar/libthrift-0.14.1.jar/g' build.xml

# Now manually change package names
# libthrift to 0.14.1
# netty to 4.1.66.Final

sudo ant clean
sudo ant

sudo ufw allow 8080

#echo "Bootstrapping VM"
#sudo apt-get update
#sudo apt-get upgrade
#
#sudo apt install python3-pip -y
#\
#git clone https://github.com/faucetsdn/ryu.git
#cd ryu
#pip install .
#
#
##sudo apt install maven
##sudo apt install openjdk-8-jdk openjdk-8-jre -y
##export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
##
##sudo curl -O https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/karaf/0.7.0/karaf-0.7.0.tar.gz
##tar -xzvf karaf-0.7.0.tar.gz
#
#echo "Controller VM Running"
