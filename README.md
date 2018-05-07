# 00. Suricata + Barnyard2 + Snorby == True

This is an attempt to document the process of installing Suricata, Barnyard2, Pulledpork and Snorby on Ubuntu 16.04LTS<br>

# 01. Install Suricata and dependencies
```
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt-get update
sudo apt-get install suricata
```

# 02. Update monitoring interface

```
sudo nano /etc/network/interfaces
```
Add monitoring network interface;<br>
```
# The secondary (monitoring) network interface
auto enp0s8
iface enp0s8 inet manual
up ifconfig $IFACE -arp up
up ip link set $IFACE promisc on
down ip link set $IFACE promisc off
down ifconfig $IFACE down
post-up ethtool -G $IFACE rx 4096; for i in rx tx sg tso ufo gso gro lro; do ethtool -K $IFACE $i off; done
```
Make sure to set the interface in promiscuous mode and to use Paravirtualized Network (virtio-net) as adapter if you intend to run it in VirtualBox... 
# 03. Create system user for Suricata
```
sudo adduser --disabled-login --shell /bin/false --system --home  /nonexistent --ingroup root suricata
sudo chown -R suricata:root /var/log/suricata
```
# 04. Update /etc/defaults/suricata
```
RUN_AS_USER=suricata
LISTENMODE=pcap
IFACE=enp0s8
```
# 05. Update /etc/suricata/suricata.yaml
```
# Cross platform libpcap capture support
pcap:
  - interface: enp0s8
```  
# 06. (Re-)start the Suricata service
```
sudo service suricata stop
sudo rm -f  /var/run/suricata.pid
sudo service suricata start
sudo service suricata status
```
# 07. Install suricata-update
suricata-update will be included in upcoming versions of Suricata but is not included in version 4.0.4
```
sudo apt-get install python-pip
sudo pip install --pre --upgrade pip
sudo pip install --pre --upgrade pyyaml suricata-update
sudo mkdir -p /var/lib/suricata/rules
sudo mkdir -p /var/lib/suricata/update
sudo touch /etc/suricata/update.yaml
sudo touch /etc/suricata/enable.conf
sudo touch /etc/suricata/disable.conf
sudo touch /etc/suricata/drop.conf
sudo touch /etc/suricata/modify.conf
```
See https://suricata-update.readthedocs.io/en/latest/update.html#example-configuration-files for further details about the suricata-update configuration files.<br>

The ET ruleset is updated by running:<br>
```
sudo suricata-update
```
Add suricata-update to crontab to ensure that you always have fresh rules installed...<br>

# 08. Install pulledpork.pl for Snort rules
```
sudo apt-get install -y libcrypt-ssleay-perl liblwp-useragent-determined-perl
git clone https://github.com/shirkdog/pulledpork.git
cd pulledpork
```

Update etc/pulledpork.conf to only include the Snort rules<br>

```
sudo cp pulledpork.pl /usr/local/bin
sudo chmod +x /usr/local/bin/pulledpork.pl
sudo mkdir -p /etc/pulledpork
sudo cp etc/pulledpork.conf /etc/pulledpork
```
The Snort ruleset is updated by running:<br>
```
sudo pulledpork.pl -c /etc/pulledpork/pulledpork.conf -l
```
# 09. Install DAQ

Current version of DAQ is 2.0.6
```
sudo apt-get install bison flex libpcap-dev
wget https://www.snort.org/downloads/snort/daq-2.0.6.tar.gz
tar zxvf daq-2.0.6.tar.gz
cd daq-2.0.6
./configure
make
sudo make install
```
# 10. Install Barnyard2
```
sudo apt-get install build-essential libtool autoconf git libpcap-dev libmysqld-dev libpcre3-dev libdumbnet-dev libdnet-dev

git clone https://github.com/firnsy/barnyard2.git

sudo ln -s /usr/include/dumbnet.h /usr/include/dnet.h
./autogen.sh CFLAGS='-lpthread'
./configure --with-mysql --with-mysql-libraries=/usr/lib/x86_64-linux-gnu
make
sudo make install
```
# 11. Create system user for barnyard2
```
sudo adduser --no-create-home --disabled-login --shell /bin/false --system --home  /nonexistent --ingroup root barnyard2
sudo mkdir -p /var/log/barnyard2
sudo chown barnyard2:root /var/log/barnyard2
```
# 12. Update /etc/barnyard2/barnyard2.conf
```
config reference_file:      /etc/suricata/reference.config
config classification_file: /etc/suricata/classification.config
config gen_file:            /etc/suricata/rules/gen-msg.map
config sid_file:            /etc/suricata/rules/sid-msg.map
...
output database: log, mysql, host=localhost dbname=barnyard2 user=suricata password=password123 sensor_name=suricata
```
# 13. Install MySQL
```
sudo apt-get install mysql-server mysql-client libmysqlclient-dev
```
# 14. (OPTIONAL) Create database and schema
Database and schema is "automagically" created by Snorby during installation, so there is no use to manually create the database and schema if you intend to use Snorby.
```
cd barnyard2/schemas
mysql -uroot -p
CREATE DATABASE snorby;
GRANT INSERT, UPDATE, SELECT ON snorby.* TO 'suricata'@'localhost' IDENTIFIED BY 'password123';
SOURCE create_mysql;

sudo chmod 660 /var/log/suricata/suricata.waldo
```
Barnyard2 can be started by running:<br>
```
sudo -u barnyard2 /usr/local/bin/barnyard2 -c /etc/barnyard2/barnyard2.conf -d /var/log/suricata -f unified2.alert -w /var/log/suricata/suricata.waldo -D
```
# 15. Create init.d script for Barnyard2

Edit /etc/init.d/barnyard2<br>

```
#!/bin/sh -e
#
### BEGIN INIT INFO
# Provides:          barnyard2
# Required-Start:    $time $network $local_fs $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Open source interpreter for Snort unified2 binary output files
# Description:       The primary usage of Barnyard2 is allowing Snort (Suricata) to write to
#                    disk in and leaving the task of parsing binary data in various formats to
#                    a separate process that will not Snort to miss network traffic.
### END INIT INFO

. /lib/lsb/init-functions

BARNYARD2="/usr/local/bin/barnyard2"
CONFIG="/etc/barnyard2/barnyard2.conf"
SPOOL_DIRECTORY="/var/log/suricata"
SPOOL_FILE="unified2.alert"
BOOKMARKING_FILE="/var/log/suricata/suricata.waldo"
INTERFACE="enp0s8"
PIDFILE="/var/run/barnyard2_$INTERFACE.pid"
PIDFILE_OWNER="barnyard2:root"

case "$1" in
  start)
       echo -n "Starting barynard2 as daemon..."
       "$BARNYARD2" -c "$CONFIG" -d "$SPOOL_DIRECTORY" -f "$SPOOL_FILE" -w "$BOOKMARKING_FILE" -D > /dev/null 2>&1
       chown "$PIDFILE_OWNER" "$PIDFILE"
       echo " done."
       ;;
  stop)
       if [ -f "$PIDFILE" ]; then
           kill `cat "$PIDFILE"`
           if [ -f "$PIDFILE" ]; then
               rm -f "$PIDFILE"
           fi
       fi
       echo " done."
    ;;
  status)
       # Check if running...
       exit 0
    ;;
  restart)
```
Enable and start the Barnyard2 service:

```
sudo update-rc.d barnyard2 defaults
sudo update-rc.d barnyard2 enable
sudo service barnyard2 start
sudo service barnyard2 status
```

# 16. (OPTIONAL) Install Java

```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get install oracle-java8-installer
```

# 17. Install Snorby and dependencies
```
sudo apt-get install -y imagemagick ruby2.3 ruby2.3-dev postgresql-server-dev-all libyaml-dev libxml2-dev libxslt-dev whois (libpq-dev)

echo "gem: --no-rdoc --no-ri" > ~/.gemrc
sudo sh -c "echo gem: --no-rdoc --no-ri > /etc/gemrc"
sudo gem install wkhtmltopdf bundler rails rake

mkdir ~/src
cd ~/src
git clone https://github.com/Snorby/snorby.git
sudo mkdir -p /var/www
sudo cp -r ./snorby/ /var/www/

cd /var/www/html/snorby
sudo bundle install
```
If error during install, follow the on screen instuctions i.e run;<br>
```
sudo bundle update do_mysql
sudo bundle update dm-mysql-adapter
```

# 18. Create snorby database user and update Snorby configuration

```
mysql GRANT ALL ON snorby.* TO 'snorby'@'localhost' IDENTIFIED BY 'password123';

sudo cp /var/www/snorby/config/database.yml.example /var/www/snorby/config/database.yml
```
Update the database user found in /var/www/snorby/config/database.yml to match the newly created database user (snorby)<br>
```
sudo cp /var/www/snorby/config/snorby_config.yml.example /var/www/snorby/config/snorby_config.yml

sudo bundle exec rake snorby:setup

DROP USER 'snorby'@'localhost';
CREATE USER 'snorby'@'localhost' IDENTIFIED BY 'password124';
GRANT SELECT, INSERT, UPDATE, DELETE ON snorby.* TO 'snorby'@'localhost';
```
Test Snorby by running:
```
sudo bundle exec rails server -e production
```

Browse to http://<ip_of_your_snorby_server>:3000<br>

Default username: snorby@example.com<br>
Default password: snorby<br>

# 19. Install Apache and Passenger

https://www.phusionpassenger.com/library/install/apache/install/oss/xenial<br>
```
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 561F9B9CAC40B2F7
sudo sh -c 'echo deb https://oss-binaries.phusionpassenger.com/apt/passenger xenial main > /etc/apt/sources.list.d/passenger.list'
sudo apt-get update
sudo apt-get install -y libapache2-mod-passenger
sudo /usr/bin/passenger-config validate-install
```

Update site configuration in Apache:<br>
```
<VirtualHost *:{PORT}>
  DocumentRoot /var/www/snorby/public
  <Directory "/var/www/snorby/public">
    AllowOverride all
    Order deny,allow
    Allow from all
    Options -MultiViews
  </Directory>
</VirutalHost>
```
... or (if you will host Snorby under /snorby) ...<br>
```
<VirtualHost *:{PORT}>
  Alias /snorby /var/www/snorby/public
  <Location "/snorby">
    PassengerBaseURI /snorby
    PassengerAppRoot /var/www/snorby
  </Location>
  <Directory "/var/www/snorby/public">
    AllowOverride all
    Order deny,allow
    Allow from all
    Options -MultiViews
  </Directory>
</VirtualHost>
```

Enable the site in Apache and reload the service configuration:<br>
```
sudo a2ensite <snorby-site-name>
sudo service apache2 reload
```
# 20. Create database user for Barnyard2 to be used together with Snorby
```
CREATE USER 'barnyard2'@'localhost' IDENTIFIED BY 'password123';
GRANT SELECT, INSERT, UPDATE ON snorby.sensor TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.event TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.iphdr TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.tcphdr TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.udphdr TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.opt TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.icmphdr TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.data TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.reference TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.reference_system TO 'barnyard2'@'localhost';
GRANT SELECT ON snorby.schema TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.sig_class TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT, UPDATE ON snorby.signature TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.sig_reference TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.detail TO 'barnyard2'@'localhost';
GRANT SELECT, INSERT ON snorby.encoding TO 'barnyard2'@'localhost';
```
# 21. References

https://blog.rapid7.com/2017/02/14/how-to-install-suricata-nids-on-ubuntu-linux/<br>
https://web.nsrc.org/workshops/2015/pacnog17-ws/raw-attachment/wiki/Track2Agenda/ex-installing-suricata.htm<br>
https://redmine.openinfosecfoundation.org/projects/suricata/wiki/suricatayaml<br>
https://redmine.openinfosecfoundation.org/projects/suricata/wiki/Suricata_Snorby_and_Barnyard2_set_up_guide<br>
https://suricata-update.readthedocs.io/en/latest/update.html<br>
https://www.aldeid.com/wiki/Snorby<br>
https://github.com/bensooter/Snort16OnUbuntu<br>
https://suricata-update.readthedocs.io/en/latest/update.html#example-configuration-files<br>
https://www.phusionpassenger.com/library/install/apache/install/oss/xenial<br>
