# Home Assistant Custom Component for controlling Cambridge Audio CXA 61/81 amplifiers

For this component to work, you'll need to have a serial connection between your Cambridge CXA amplifier and your Home Assistant instance.
This can be either a direct serial connection, or you could use a remote device like a Raspberry Pi to provide the serial connection from your CXA to your Home Assistant instance. 

In case you have a direct serial connection between your Cambridge CXA and Home Assistant, follow the steps below. If you have a Raspberry Pi in between, scroll down to the next section.

## Direct serial connection

On your Home Assistant, create a directory called `cambridge_cxa` under the `custom_components` directory, and save the files from this repo in there.

Then you need to add the following to your `configuration.yaml` file:

```
media_player:
  - platform: cambridge_cxa
    device: /dev/serial/by-id/<insert id of USB to serial device here>
    name: CXA
    type: CXA61 or CXA81
    slave: <Optional value, if you have a CXN, enter its IP address here, so you can control the CXA's volume through the CXN>
```

Restart Home Assistant, and see you have a new media_player entity for your CXA.


## Indirect serial connection

You'll need to install ser2net on the Raspberry Pi where you have the serial connection to your Cambridge CXA, so the serial port can be accessed over the network.

Install ser2net: `sudo apt install ser2net`

If you installed ser2net version 3.x, add this to `/etc/ser2net.conf` file on the Raspberry Pi:

```
5000:raw:600:/dev/serial/by-id/<insert id of USB to serial device here>:9600 8DATABITS NONE 1STOPBIT
```

If you installed ser2net version 4.x, add this to `/etc/ser2net.yaml` file on the Raspberry Pi:

```
connection: &cambridge
    accepter: tcp,5000
    enable: on
    options:
      kickolduser: true
      telnet-brk-on-sync: true
    connector: serialdev,
              /dev/serial/by-id/<insert id of USB to serial device here>,
              9600n81,local
```

Make sure the ser2net service is enabled and running on your Raspberry Pi. Enter following commands.
`sudo systemctl enable ser2net`
`sudo systemctl start ser2net`

Then, on the PC/Raspberry Pi/VM/... where your Home Assistant instance is running, we'll need to connect to the serial on the Raspberry Pi. We will do this using an utility called socat.

Make sure socat is installed by running `sudo apt install socat`

Next, create a file `/etc/default/socat.conf` and add the following:

```
OPTIONS="pty,link=/dev/ttyCXA,raw,ignoreeof,echo=0 tcp:<IP address of the Raspberry Pi>:5000"
```

Change the IP address to the IP address of your Raspberry Pi. Leave port to 5000, unless you changed it in the `/etc/ser2net.yaml` file.
Notice the name of the device `/dev/ttyCXA`. You'll need this later on!

Then you'll need to create a systemd service. Create a file `/etc/init.d/socat` and add this:

```
#! /bin/sh
### BEGIN INIT INFO
# Provides:          socat
# Required-Start:    $local_fs $time $network $named
# Required-Stop:     $local_fs $time $network $named
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start/stop (socat a multipurpose relay)
#
# Description: The socat init script will start/stop socat as specified in /etc/default/socat
#              Then log (FATAL,ERROR,WARN,INFO and Notic) in /var/log/socat.log
### END INIT INFO

NAME=socat
DAEMON=/usr/bin/socat
SOCAT_DEFAULTS='-d -d -d -lf /var/log/socat.log'

. /lib/lsb/init-functions
. /etc/default/socat.conf

PATH=/bin:/usr/bin:/sbin:/usr/sbin

[ -x $DAEMON ] || exit 0

start_socat() {
        start-stop-daemon --oknodo --quiet --start \
                --pidfile /var/run/socat.pid \
                --background --make-pidfile \
                --exec $DAEMON -- $SOCAT_DEFAULTS $OPTIONS < /dev/null
}

stop_socat() {
        start-stop-daemon --oknodo --stop --quiet --pidfile /var/run/socat.pid --exec $DAEMON
        rm -f /var/run/socat.pid
}

start () {
        start_socat
        return $?
}

stop () {
        for PIDFILE in `ls /var/run/socat.pid 2> /dev/null`; do
                NAME=`echo $PIDFILE | cut -c16-`
                NAME=${NAME%%.pid}
                stop_socat
        done
}

case "$1" in
    start)
            log_daemon_msg "Starting multipurpose relay" "socat"
            if start ; then
                    log_end_msg $?
            else
                    log_end_msg $?
            fi
            ;;
    stop)
            log_daemon_msg "Stopping multipurpose relay" "socat"
            if stop ; then
                   log_end_msg $?
           else
                   log_end_msg $?
           fi
           ;;
    restart)
            log_daemon_msg "Restarting multipurpose relay" "socat"
            stop
            if start ; then
                    log_end_msg $?
            else
                    log_end_msg $?
            fi
            ;;
    reload|force-reload)
            log_daemon_msg "Reloading multipurpose relay" "socat"
            stop
            if start ; then
                    log_end_msg $?
            else
                    log_end_msg $?
            fi
            ;;
    status)
            status_of_proc -p /var/run/socat.pid /usr/bin/socat socat && exit 0 || exit $?
            ;;
    *)
        echo "Usage: /etc/init.d/$NAME {start|stop|restart|reload|force-reload|status}"
        exit 3
        ;;
esac

exit 0
```

Then enable and start the service:
`sudo systemctl enable socat`
`sudo systemctl start socat`

On your Home Assistant, create a directory called `cambridge_cxa` under the `custom_components` directory, and save the files from this repo in there.

Then, add the following to your configuration.yaml file:

```
media_player:
  - platform: cambridge_cxa
    device: /dev/ttyCXA
    name: CXA
    type: CXA61 or CXA81
    slave: <Optional value, if you have a CXN, enter its IP address here, so you can control the CXA's volume through the CXN>
```

Restart Home Assistant, and see you have a new media_player entity for your CXA.

Note: When running Home Assistant in Docker, you need to forward the serial port /dev/ttyCXA to your container as a volume, not a device! So add `-v /dev/ttyCXA:/dev/ttyCXA` to your docker command, or add this to your docker-composer file:
```
volumes:
  - /dev/ttyCXA:/dev/ttyCXA
```

