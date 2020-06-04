This repository turns a Raspberry Pi into a bluetooth keyboard.

The initial instructions and the code can be found here:
http://yetanotherpointlesstechblog.blogspot.com/2016/04/emulating-bluetooth-keyboard-with.html

The code presented in the blog is outdated, using very old libraries, have dirty hacks(e.g depens on GTK while not having GUI), and does not handle device disconnection correclty(you have to restart __eveything__ to reconnect your keyboard).
The port to Python3 is done by @ukBaz. You can check the changes he made at: https://gist.github.com/ukBaz/a47e71e7b87fbc851b27cde7d1c0fcf0

## Usage

### 1. Configure Raspberry Pi.

These instructions assuming you have BlueZ >=5.43 installed. 

```shell
$ bluetoothctl -v
bluetoothctl: 5.50
```

Ensure Raspberry Pi is at the latest version:

```shell
sudo apt update
sudo apt upgrade
sudo apt dist-upgrade
```

Check that the packages required for this are installed:

```shell
sudo apt-get install python3-dbus
```

By default, Raspberry Pi uses Python2, you have to install `python3-pip` manually:

```shell
sudo apt install python3-pip
```

Then you can install the required dependency:

```shell
sudo pip3 install evdev
```

### 2. Reconfigure the Bluetooth Daemon

First we have to stop the bluetooth daemon, if it is already running:

```shell
sudo systemctl stop bluetooth
```

The `input` Bluetooth plugin needs to be removed so that it does not grab the sockets we require access to. As the original author says the way this was documented could be improved. If you want to restart the daemon (without the input plugin) from the command line then the following would seem the preferred:

```shell
sudo /usr/lib/bluetooth/bluetoothd -P input
```

The service file to start the bluetooth daemon is located at `/lib/systemd/system/bluetooth.service`, you can modify it directly, but your edition might be overwritten after system updates. I strongly recommend to utilize systemd's service priority feature:

```shell
sudo cp /lib/systemd/system/bluetooth.service /etc/systemd/system/bluetooth.service
```

The service file located in `/etc/systemd/system/` has higer priority, and will overwrite the ones located in `/lib/systemd/system/`.

Then edit `/etc/systemd/system/bluetooth.service` with your favourite text editor(requires root):

Change the following line:

```
ExecStart=/usr/lib/bluetooth/bluetoothd
```
to

```
ExecStart=/usr/lib/bluetooth/bluetoothd -P input
```

After that, reload your service file:

```
sudo systemctl daemon-reload
sudo systemctl reenable bluetooth
```

Now you can do `sudo systemctl start bluetooth`, and the configuration will survive reboot and system updates.

### 3. Configure D-Bus

When a new service is created on the D-Bus, this service needs to be configured.

```shell
sudo cp org.yaptb.btkkbservice.conf /etc/dbus-1/system.d
```

### 4. Pair your device
With the settings used in this setup the pairing steps described in the original tutorial should not be required. 

The following assume you have started the modified `bluetooth` service:

#### Terminal 1

```shell
pi@raspberrypi:~/ $ sudo python3 btk_server.py
Setting up service
Setting up BT device
Configuring for name BT_HID_Keyboard
Configuring Bluez Profile
Reading service record
Profile registered
Waiting for connections
 ```
Scan for the keyboard Pi and connect from main computer
```
8C:2D:AA:44:0E:3A connected on the control socket
8C:2D:AA:44:0E:3A connected on the interrupt channel
```

Connect a keyboard to your Raspberry Pi(if you have not yet):

#### Terminal 2
```shell
pi@raspberrypi:~/ $ python3 kb_client.py
Setting up keyboard
found a keyboard
starting event loop
Listening...
```

Now the keyboard inputs should be forwarded to the bluetooth client.

You can use GNU `screen` to keep scripts running even you have disconnected from ssh.

After the initial pairing, you can modify `btk_server`, change:

```python
self.discoverable = True
```

to 

```python
self.discoverable = False
```

So that only paired devices could connect.

### Limitation

iOS devices do not want to automatically reconnect after disconnection, you have to manually connect to the Pi-Keyboard again.






