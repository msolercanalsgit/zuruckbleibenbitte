# WiFi Provisioning System for Train Display

This system allows you to configure your Raspberry Pi's WiFi connection through a mobile-friendly web interface, without needing a keyboard or monitor.

## How It Works

### Initial Setup Mode
When your Raspberry Pi boots up without a WiFi connection:

1. **Automatic Hotspot Creation**: The Pi creates a WiFi access point named `TrainDisplay-Setup`
2. **Connect with Phone**: Use your phone to connect to this network
   - Network: `TrainDisplay-Setup`
   - Password: `trainsetup123`
3. **Configure WiFi**: Open a browser and go to `http://192.168.4.1`
4. **Enter Credentials**: Add your home WiFi name and password
5. **Automatic Connection**: The Pi will disconnect from AP mode and connect to your WiFi

### Normal Operation Mode
Once connected to your home WiFi:

- The Pi stays connected and runs the train display normally
- The configuration web server runs in the background
- Access it at `http://[raspberry-pi-ip]` to add more networks or change settings
- If the WiFi connection fails, the Pi automatically falls back to AP mode

## Installation

On your Raspberry Pi, run:

```bash
cd /home/msolercanals/zuruckbleibenbitte
sudo ./setup_wifi_provisioning.sh
sudo reboot
```

## File Structure

```
zuruckbleibenbitte/
├── scripts/
│   ├── wifi_manager.py         # Manages AP/client mode switching
│   ├── config_server.py        # Flask web server for configuration
│   ├── config.json             # Stores WiFi credentials
│   ├── templates/
│   │   └── index.html         # Web interface
│   ├── main_train_display.py  # Main train display (existing)
│   └── update_git.py          # Git updater (existing)
├── launcher.sh                 # Updated to include WiFi setup
├── train-display-config.service # Systemd service
└── setup_wifi_provisioning.sh  # Installation script
```

## Components

### 1. WiFi Manager (`wifi_manager.py`)
- Checks for internet connectivity on boot
- Attempts to connect to saved WiFi networks
- Falls back to AP mode if no connection is available
- Uses NetworkManager for all WiFi operations

### 2. Configuration Server (`config_server.py`)
- Flask web server running on port 80
- Provides REST API for WiFi management
- Always runs in background (systemd service)
- Accessible in both AP mode and normal operation

### 3. Web Interface (`templates/index.html`)
- Mobile-friendly responsive design
- Add/remove WiFi networks
- View connection status
- Future: Configure train station settings

### 4. Configuration Storage (`config.json`)
```json
{
  "wifi_networks": [
    {
      "ssid": "YourWiFiName",
      "password": "YourPassword"
    }
  ],
  "train_station": {
    "id": "900120004",
    "name": "Warschauer Straße"
  },
  "ap_mode": {
    "ssid": "TrainDisplay-Setup",
    "password": "trainsetup123"
  }
}
```

## Startup Sequence

When the Raspberry Pi boots:

1. **Launcher Script** (`launcher.sh`) runs
2. **WiFi Manager** checks connection and sets up network
3. **Config Server** starts as systemd service (always running)
4. **Git Updater** pulls latest code (if connected)
5. **Train Display** shows train information

## API Endpoints

The configuration server provides these endpoints:

- `GET /` - Main configuration page
- `GET /api/networks` - List saved networks
- `POST /api/wifi/add` - Add WiFi network
- `POST /api/wifi/remove` - Remove WiFi network
- `GET /api/status` - Get connection status
- `POST /api/station/update` - Update train station (future)

## Troubleshooting

### Can't connect to TrainDisplay-Setup
- Wait 2-3 minutes after boot for AP mode to start
- Make sure you're close to the Raspberry Pi
- Try forgetting the network and reconnecting

### Can't access http://192.168.4.1
- Verify you're connected to `TrainDisplay-Setup`
- Some phones require disabling mobile data
- Try `http://192.168.4.1` (not https)

### WiFi not connecting after configuration
- Verify WiFi password is correct
- Check if your WiFi is 2.4GHz (Raspberry Pi might not support 5GHz depending on model)
- Look at logs: `cat /home/msolercanals/launcher.log`

### Finding Pi on home network
After connecting to your WiFi, find the Pi's IP address:

```bash
# On the Raspberry Pi (with keyboard/monitor):
hostname -I

# From your computer (on same network):
nmap -sn 192.168.1.0/24  # Adjust subnet to match your network
# or
arp -a
```

## Security Notes

- WiFi passwords are stored in plain text in `config.json`
- The web server has no authentication (add if needed)
- Only accessible on local network (AP or home WiFi)
- Consider changing the default AP password in `config.json`

## Future Enhancements

- [ ] Add train station selection through web interface
- [ ] Add authentication to web server
- [ ] Support for hidden WiFi networks
- [ ] Network scanning to show available networks
- [ ] Encrypt stored passwords
- [ ] Mobile app integration
- [ ] WiFi signal strength indicator
- [ ] Automatic reconnection retry logic improvements

## Technical Details

### NetworkManager Commands Used

```bash
# Check connection state
nmcli -t -f STATE general

# Get current SSID
nmcli -t -f active,ssid dev wifi

# Connect to WiFi
nmcli dev wifi connect SSID password PASSWORD

# Create hotspot
nmcli dev wifi hotspot ifname wlan0 ssid SSID password PASSWORD

# Stop hotspot
nmcli connection down TrainDisplayHotspot
```

### Dependencies

- Python 3
- Flask (web framework)
- NetworkManager (WiFi management)
- systemd (service management)

## Support

For issues or questions, check the logs:

```bash
# Launcher log (includes WiFi manager output)
tail -f /home/msolercanals/launcher.log

# Config server log
sudo journalctl -u train-display-config -f

# NetworkManager log
sudo journalctl -u NetworkManager -f
```
