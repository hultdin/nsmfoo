# 00. Suricata + Barnyard2 + Snorby == True

# 01. Install Suricata and dependencies

sudo apt-get install software-properties-common<br>
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt-get update
sudo apt-get install suricata

# 02. Update monitoring interface

sudo nano /etc/network/interfaces<br>

Add monitoring network interface;<br>

&#35; The secondary (monitoring) network interface<br>
auto enp0s8<br>
iface enp0s8 inet manual<br>
up ifconfig $IFACE -arp up<br>
up ip link set $IFACE promisc on<br>
down ip link set $IFACE promisc off<br>
down ifconfig $IFACE down<br>
post-up ethtool -G $IFACE rx 4096; for i in rx tx sg tso ufo gso gro lro; do ethtool -K $IFACE $i off; done<br>

# 03. Create system user (suricata)

sudo adduser --disabled-login --shell /bin/false --system --home  /nonexistent --ingroup root suricata<br>
sudo chown -R suricata:root /var/log/suricata<br>

# 04. Update default configuration for suricata (/etc/defaults/suricata)

RUN_AS_USER=suricata<br>
LISTENMODE=pcap<br>
IFACE=enp0s8<br>

# 05. Update /etc/suricata/suricata.yaml

&#35; Cross platform libpcap capture support<br>
pcap:<br>
  - interface: enp0s8<br>
  
# 06. (Re-)start suricata

sudo service suricata stop<br>
sudo rm -f  /var/run/suricata.pid<br>
sudo service suricata start<br>
sudo service suricata status<br>

# 07. Install suricata-update if not included in the Suricata package

sudo apt-get install python-pip<br>
sudo pip install --pre --upgrade pip<br>
sudo pip install --pre --upgrade pyyaml suricata-update<br>
sudo mkdir -p /var/lib/suricata/rules<br>
sudo mkdir -p /var/lib/suricata/update<br>
sudo touch /etc/suricata/update.yaml<br>
sudo touch /etc/suricata/enable.conf<br>
sudo touch /etc/suricata/disable.conf<br>
sudo touch /etc/suricata/drop.conf<br>
sudo touch /etc/suricata/modify.conf<br>

See https://suricata-update.readthedocs.io/en/latest/update.html#example-configuration-files for further details about the suricata-update configuration files<br>

The ET ruleset is updated by running:<br>

sudo suricata-update<br>

Add suricata-update to crontab to ensure that you always have fresh rules installed...<br>

# 08. Install pulledpork.pl for Snort rules

sudo apt-get install -y libcrypt-ssleay-perl liblwp-useragent-determined-perl<br>
git clone https://github.com/shirkdog/pulledpork.git<br>
cd pulledpork<br>

Update etc/pulledpork.conf to only include the Snort rules<br>

sudo cp pulledpork.pl /usr/local/bin<br>
sudo chmod +x /usr/local/bin/pulledpork.pl<br>
sudo mkdir -p /etc/pulledpork<br>
sudo cp etc/pulledpork.conf /etc/pulledpork<br>

The Snort ruleset is updated by running:<br>

sudo pulledpork.pl -c /etc/pulledpork/pulledpork.conf -l<br>

# 09. Install DAQ (current version is 2.0.6)

sudo apt-get install bison flex libpcap-dev<br>
wget https://www.snort.org/downloads/snort/daq-2.0.6.tar.gz<br>
tar zxvf daq-2.0.6.tar.gz<br>
cd daq-2.0.6<br>
./configure<br>
make<br>
sudo make install<br>

# 10. Install Barnyard2

sudo apt-get install build-essential libtool autoconf git libpcap-dev libmysqld-dev libpcre3-dev libdumbnet-dev libdnet-dev<br>

git clone https://github.com/firnsy/barnyard2.git<br>

sudo ln -s /usr/include/dumbnet.h /usr/include/dnet.h<br>
./autogen.sh CFLAGS='-lpthread'<br>
./configure --with-mysql --with-mysql-libraries=/usr/lib/x86_64-linux-gnu<br>
make<br>
sudo make install<br>

# 11. Create system user for barnyard2

sudo adduser --no-create-home --disabled-login --shell /bin/false --system --home  /nonexistent --ingroup root barnyard2<br>
sudo mkdir -p /var/log/barnyard2<br>
sudo chown barnyard2:root /var/log/barnyard2<br>

# 12. Update /etc/barnyard2/barnyard2.conf

config reference_file:      /etc/suricata/reference.config<br>
config classification_file: /etc/suricata/classification.config<br>
config gen_file:            /etc/suricata/rules/gen-msg.map<br>
config sid_file:            /etc/suricata/rules/sid-msg.map<br>
...<br>
output database: log, mysql, host=localhost dbname=barnyard2 user=suricata password=password123 sensor_name=suricata<br>

# 13. Install MySQL

sudo apt-get install mysql-server mysql-client libmysqlclient-dev<br>

# 14. (OPTIONAL) Create database and schema unless you intend to use Snorby

cd barnyard2/schemas<br>
mysql -uroot -p<br>
CREATE DATABASE snorby;<br>
GRANT INSERT, UPDATE, SELECT ON snorby.* TO 'suricata'@'localhost' IDENTIFIED BY 'password123';<br>
SOURCE create_mysql;<br>

sudo chmod 660 /var/log/suricata/suricata.waldo<br>

Barnyard2 can be started by running:<br>

sudo -u barnyard2 /usr/local/bin/barnyard2 -c /etc/barnyard2/barnyard2.conf -d /var/log/suricata -f unified2.alert -w /var/log/suricata/suricata.waldo -D<br>

# 15. Create init.d script for Barnyard2

Edit /etc/init.d/barnyard2<br>

&#35;!/bin/sh -e<br>
&#35;<br>
&#35;&#35;&#35; BEGIN INIT INFO<br>
&#35; Provides:          barnyard2<br>
&#35; Required-Start:    $time $network $local_fs $remote_fs<br>
&#35; Required-Stop:     $remote_fs<br>
&#35; Default-Start:     2 3 4 5<br>
&#35; Default-Stop:      0 1 6<br>
&#35; Short-Description: Open source interpreter for Snort unified2 binary output files<br>
&#35; Description:       The primary usage of Barnyard2 is allowing Snort (Suricata) to write to<br>
&#35;                    disk in and leaving the task of parsing binary data in various formats to<br>
&#35;                    a separate process that will not Snort to miss network traffic.<br>
&#35;&#35;&#35; END INIT INFO<br>
<br>
. /lib/lsb/init-functions<br>
<br>
BARNYARD2="/usr/local/bin/barnyard2"<br>
CONFIG="/etc/barnyard2/barnyard2.conf"<br>
SPOOL_DIRECTORY="/var/log/suricata"<br>
SPOOL_FILE="unified2.alert"<br>
BOOKMARKING_FILE="/var/log/suricata/suricata.waldo"<br>
INTERFACE="enp0s8"<br>
PIDFILE="/var/run/barnyard2_$INTERFACE.pid"<br>
PIDFILE_OWNER="barnyard2:root"<br>
<br>
case "$1" in<br>
  start)<br>
       echo -n "Starting barynard2 as daemon..."<br>
       "$BARNYARD2" -c "$CONFIG" -d "$SPOOL_DIRECTORY" -f "$SPOOL_FILE" -w "$BOOKMARKING_FILE" -D > /dev/null 2>&1<br>
       chown "$PIDFILE_OWNER" "$PIDFILE"<br>
       echo " done."<br>
       ;;<br>
  stop)<br>
       if [ -f "$PIDFILE" ]; then<br>
           kill `cat "$PIDFILE"`<br>
           if [ -f "$PIDFILE" ]; then<br>
               rm -f "$PIDFILE"<br>
           fi<br>
       fi<br>
       echo " done."<br>
    ;;<br>
  status)<br>
       # Check if running...<br>
       exit 0<br>
    ;;<br>
  restart)<br>
<br>
sudo update-rc.d barnyard2 defaults<br>
sudo update-rc.d barnyard2 enable<br>
sudo service barnyard2 start<br>
sudo service barnyard2 status<br>

# 16. (OPTIONAL) Install Java

...<br>

# 17. Install Snorby and dependencies

sudo add-apt-repository ppa:webupd8team/java<br>
sudo apt-get install oracle-java8-installer<br>

sudo apt-get install -y imagemagick ruby2.3 ruby2.3-dev postgresql-server-dev-all libyaml-dev libxml2-dev libxslt-dev (libpq-dev)<br>

echo "gem: --no-rdoc --no-ri" > ~/.gemrc<br>
sudo sh -c "echo gem: --no-rdoc --no-ri > /etc/gemrc"<br>
sudo gem install wkhtmltopdf bundler rails rake<br>

mkdir ~/src<br>
cd ~/src<br>
git clone https://github.com/Snorby/snorby.git<br>
sudo mkdir -p /var/www<br>
sudo cp -r ./snorby/ /var/www/<br>

cd /var/www/html/snorby<br>
sudo bundle install<br>

If error during install, follow the on screen instuctions i.e run;<br>
sudo bundle update do_mysql<br>
sudo bundle update dm-mysql-adapter<br>

# 18. Create snorby database user and update Snorby configuration

mysql GRANT ALL ON snorby.* TO 'snorby'@'localhost' IDENTIFIED BY 'password123';<br>

sudo cp /var/www/snorby/config/database.yml.example /var/www/snorby/config/database.yml<br>

Update the database user found in /var/www/snorby/config/database.yml<br>

sudo cp /var/www/snorby/config/snorby_config.yml.example /var/www/snorby/config/snorby_config.yml<br>

sudo bundle exec rake snorby:setup<br>

DROP USER 'snorby'@'localhost';<br>
CREATE USER 'snorby'@'localhost' IDENTIFIED BY 'password124';<br>
GRANT SELECT, INSERT, UPDATE, DELETE ON snorby.* TO 'snorby'@'localhost';<br>
<br>
Test Snorby by running:<br>

sudo bundle exec rails server -e production<br>

Browse to http://<ip_of_your_snorby_server>:3000<br>

Default username: snorby@example.com<br>
Default password: snorby<br>

# 19. Install Apache and Passenger

https://www.phusionpassenger.com/library/install/apache/install/oss/xenial<br>

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 561F9B9CAC40B2F7<br>
sudo sh -c 'echo deb https://oss-binaries.phusionpassenger.com/apt/passenger xenial main > /etc/apt/sources.list.d/passenger.list'<br>
sudo apt-get update<br>
sudo apt-get install -y libapache2-mod-passenger<br>
sudo /usr/bin/passenger-config validate-install<br>

Update site configuration in Apache:<br>

<VirtualHost *:{PORT}><br>
  DocumentRoot /var/www/snorby/public<br>
  <Directory "/var/www/snorby/public"><br>
    AllowOverride all<br>
    Order deny,allow<br>
    Allow from all<br>
    Options -MultiViews<br>
  </Directory><br>
</VirutalHost><br>
<br>
... or (if you will host Snorby under /snorby) ...<br>
<br>
<VirtualHost *:{PORT}><br>
  Alias /snorby /var/www/snorby/public<br>
  <Location "/snorby"><br>
    PassengerBaseURI /snorby<br>
    PassengerAppRoot /var/www/snorby<br>
  </Location><br>
  <Directory "/var/www/snorby/public"><br>
    AllowOverride all<br>
    Order deny,allow<br>
    Allow from all<br>
    Options -MultiViews<br>
  </Directory><br>
</VirtualHost><br>

Enable the site in Apache and reload the service configuration:<br>

sudo a2ensite <snorby-site-name><br>
sudo service apache2 reload<br>

# 20. Create database user for Barnyard2 to be used together with Snorby

CREATE USER 'barnyard2'@'localhost' IDENTIFIED BY 'password123';<br>
GRANT SELECT, INSERT, UPDATE ON snorby.sensor TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.event TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.iphdr TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.tcphdr TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.udphdr TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.opt TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.icmphdr TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.data TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.reference TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.reference_system TO 'barnyard2'@'localhost';<br>
GRANT SELECT ON snorby.schema TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.sig_class TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT, UPDATE ON snorby.signature TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.sig_reference TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.detail TO 'barnyard2'@'localhost';<br>
GRANT SELECT, INSERT ON snorby.encoding TO 'barnyard2'@'localhost';<br>

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
