# cambridge_cxa
Home Assistant Custom Component for controlling Cambridge Audio CXA amplifiers

This component assumes you have a seperate device like a Raspberry Pi that has a USB to Serial connection to the CXA. You'll need to install ser2net on that Raspberry Pi, so the serial port can be accessed over the network.

Add a config like this to your `/etc/ser2net.yaml` file on the Raspberry Pi:

```
connection: &cambridge
    accepter: tcp,5000
    enable: on
    options:
      kickolduser: true
      telnet-brk-on-sync: true
    connector: serialdev,
              /dev/ttyUSB0,
              9600n81,local
```

On your Home Assistant, create a directory called `cambridge_cxa` under the `custom_components` directory, and save the files from this repo in there.

Then, add the following to your configuration.yaml file:

```
media_player:
  - platform: cambridge_cxa
    host: <IP address of the Raspberry Pi that has the USB to serial connection to the amp>
    port: 5000 <or any other port you have configured in ser2net.yaml>
    type: CXA81 or XCA61
    name: <Optional value, to override default name: Cambridge Audio CXA>
    slave: <Optional value, if you have a CXN, enter its IP address here, so you can control the CXA's volume through the CXN>
```

Reboot Home Assistant, and see you have a new media_player entity for your CXA.