#!/bin/bash

echo "Installing drivers..."
apt-get install xboxdrv
bash -c 'echo -e "# allow programs without root permissions to use uinput\nKERNEL==\"uinput\", MODE=\"0666\"" >> /etc/udev/rules.d/50-uinput.rules'
udevadm trigger
bash -c 'echo -e "pi ALL=NOPASSWD: /usr/bin/xboxdrv\n" > /etc/sudoers.d/xboxdrv'
