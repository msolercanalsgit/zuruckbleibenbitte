# Quick Start Guide - WiFi Provisioning

## 🚀 Installation (One-time setup)

On your Raspberry Pi 5:

```bash
cd /home/msolercanals/zuruckbleibenbitte
sudo ./setup_wifi_provisioning.sh
sudo reboot
```

## 📱 First Time WiFi Setup

### Step 1: Connect to Setup Network
After reboot, the Pi creates a WiFi hotspot:

- **Network Name**: `TrainDisplay-Setup`
- **Password**: `trainsetup123`

Connect your phone to this network.

### Step 2: Configure WiFi
Open your phone's browser and go to:
```
http://192.168.4.1
```

You'll see a purple configuration page.

### Step 3: Add Your WiFi
- Enter your home WiFi name (SSID)
- Enter your WiFi password
- Click "Connect to WiFi"

### Step 4: Reconnect
- The Pi will disconnect from setup mode
- It will connect to your home WiFi
- The train display will start showing trains!

## 🔄 Adding More WiFi Networks Later

Once connected to your home WiFi, you can still access the configuration:

1. Find your Pi's IP address (check your router or use `hostname -I` on the Pi)
2. Visit `http://[pi-ip-address]` in any browser
3. Add additional WiFi networks (home, office, etc.)

The Pi will try all saved networks in order if one fails.

## 🎯 What Happens on Boot

```
1. WiFi Manager runs
   ├─ If WiFi saved → Try to connect
   │  ├─ Success → Continue to step 2
   │  └─ Fail → Start AP mode (TrainDisplay-Setup)
   └─ No WiFi saved → Start AP mode

2. Config server starts (always available in background)

3. Git updater pulls latest code

4. Train display shows trains
```

## ⚠️ Troubleshooting

**Can't see TrainDisplay-Setup network**
- Wait 2-3 minutes after boot
- Make sure you're within range

**Can't access http://192.168.4.1**
- Verify you're connected to TrainDisplay-Setup
- Try disabling mobile data on your phone
- Use http:// not https://

**WiFi not connecting**
- Double-check password (case-sensitive!)
- Ensure WiFi is 2.4GHz (Pi 5 supports both, but check)
- View logs: `tail -f /home/msolercanals/launcher.log`

## 📝 Files Created

- `scripts/wifi_manager.py` - WiFi connection manager
- `scripts/config_server.py` - Web server
- `scripts/config.json` - Your WiFi credentials
- `scripts/templates/index.html` - Web interface
- `train-display-config.service` - Systemd service
- `WIFI_SETUP.md` - Detailed documentation

## 🔐 Security Note

WiFi passwords are stored in `scripts/config.json`. The web interface has no login - it's only accessible on your local network.

To change the setup network password, edit `scripts/config.json` after installation.

## 🎨 Future Features

The web interface is ready to be extended with:
- Train station selection
- Display brightness control
- Timezone settings
- Display on/off schedule

See `WIFI_SETUP.md` for technical details and API documentation.
