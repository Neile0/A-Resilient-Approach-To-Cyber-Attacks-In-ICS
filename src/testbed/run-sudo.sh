# Run using shell
cd src/testbed
sudo pip install -q -r requirements.txt
sudo python3 run.py marine-ballast
echo "Exiting and performing Mininet Cleanup"
sudo mn -c
#sudo python3 run-old.py ics-example.xml