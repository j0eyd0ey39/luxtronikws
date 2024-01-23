# luxtronikws

This is an attempt at polling Luxtronik over its websocket to Home Assistant. There are no controls, just sensors. If you want controls, try fhem. 

This probably only works with AIT fw version 3.88.x, give or take a few minor versions. Tested with PWZSV9. If it doesn't work for you, write a bug and add your Luxtronik fw version information. I make no promises to fix it, but at least other people will know it is a known issue.

# installation
First install [HACS](https://hacs.xyz/) to your Home Assistant.

Then add this repository to HACS as a custom integration repository. Download it with HACS. Reboot your Home Assistant. Add the luxtronikws integration to HA. Provide the IP and password for the web interface of your luxtronik device.

Use a static IP for your Luxtronik, because the code does not have a flow for searching your device after the initial config. You will have to re-create the hub, if the IP changes.
