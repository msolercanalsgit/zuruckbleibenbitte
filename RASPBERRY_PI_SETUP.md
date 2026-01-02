# Raspberry Pi Train Display - Setup Guide

Quick setup guide for deploying the train display on a new Raspberry Pi.

## Hardware Requirements

- Raspberry Pi 5 (or compatible)
- RGB LED Matrix Panel (192x32 pixels)
- Adafruit RGB Matrix HAT or Bonnet
- Power supply (5V, sufficient amperage for LED panel)
- MicroSD card (16GB minimum)

## Initial Raspberry Pi Setup

### 1. Flash Raspberry Pi OS
- Download Raspberry Pi OS Lite (64-bit recommended)
- Flash to SD card using Raspberry Pi Imager
- Enable SSH in Imager settings
- Set hostname, username: `msolercanals`, password

### 2. First Boot & Update
```bash
# SSH into the Pi
ssh msolercanals@[pi-ip-address]

# Update system
sudo apt-get update
sudo apt-get upgrade -y
```

### 3. Install RGB Matrix Library
```bash
# Install build dependencies
sudo apt-get install -y git python3-dev python3-pillow

# Clone and build rpi-rgb-led-matrix library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Build the library
make build-python PYTHON=$(which python3)

# Install Python bindings
sudo make install-python PYTHON=$(which python3)
```

### 4. Install System Dependencies
```bash
sudo apt-get install -y \
    python3-pip \
    python3-flask \
    network-manager \
    git
```

### 5. Clone Train Display Repository
```bash
cd /home/msolercanals
git clone https://github.com/marcsolercanals/zuruckbleibenbitte.git
cd zuruckbleibenbitte
```

### 6. Install Python Dependencies
```bash
# Install from requirements.txt
pip3 install -r requirements.txt --break-system-packages

# Or install manually:
pip3 install Flask pandas requests --break-system-packages
```

### 7. Setup WiFi Provisioning System
```bash
# Run the setup script
sudo ./setup_wifi_provisioning.sh

# Fix ownership
sudo chown -R msolercanals:msolercanals /home/msolercanals/zuruckbleibenbitte
```

### 8. Configure Auto-Start on Boot
```bash
# Edit crontab
crontab -e

# Add this line (if not already present):
@reboot sleep 30 && /home/msolercanals/zuruckbleibenbitte/launcher.sh
```

### 9. Reboot
```bash
sudo reboot
```

## First-Time WiFi Setup

After reboot, the Pi will:

1. **Create WiFi hotspot** named: `TrainDisplay-Setup`
2. **Password**: `trainsetup123`
3. **Connect** to this network with your phone
4. **Open browser** and go to: `http://10.42.0.1`
5. **Enter your home WiFi** credentials
6. **Pi will connect** and display IP address on LED screen for 10 seconds

## Accessing Configuration Interface

### When Connected to WiFi

1. **Find IP address**:
   - Shown on LED screen at boot (10 seconds)
   - Or SSH in and run: `hostname -I`

2. **Access web interface**: `http://[ip-address]`

3. **View status**: Connection info and train station settings

## Useful Commands

### Check IP Address
```bash
hostname -I
```

### Stop WiFi Manager
```bash
sudo pkill -f wifi_manager.py
sudo systemctl stop train-display-config.service
```

### Restart WiFi Manager
```bash
sudo systemctl start train-display-config.service
```

### View Logs
```bash
tail -f /home/msolercanals/launcher.log
```

### Update Code from Git
```bash
# IMPORTANT: Stop WiFi manager first to avoid conflicts
sudo pkill -f wifi_manager.py
sudo pkill -f config_server.py

# Now update from git
cd /home/msolercanals/zuruckbleibenbitte
git pull

# Reboot to restart all services
sudo reboot
```

### Fix Permissions (if git fails)
```bash
sudo chown -R msolercanals:msolercanals /home/msolercanals/zuruckbleibenbitte
```

### Manually Run WiFi Manager
```bash
sudo python3 /home/msolercanals/zuruckbleibenbitte/scripts/wifi_manager.py
```

## Troubleshooting

### WiFi Not Connecting
- Wait 20 seconds for internet verification
- Check password is correct
- Use "Show" button to verify password
- Check logs: `tail -f /home/msolercanals/launcher.log`

### LED Matrix Not Working
- Check power supply (needs sufficient amperage)
- Verify GPIO connections
- Run with sudo (LED matrix requires root access)

### Git Errors (corrupt files, error 255)
```bash
# Fix ownership
sudo chown -R msolercanals:msolercanals /home/msolercanals/zuruckbleibenbitte

# If still failing, rebuild git index
cd /home/msolercanals/zuruckbleibenbitte
rm -f .git/index
git reset
git pull
```

### Config Web Server Not Running
```bash
# Check if running
sudo lsof -i :80

# Start manually
sudo python3 /home/msolercanals/zuruckbleibenbitte/scripts/config_server.py

# Or via systemd
sudo systemctl start train-display-config.service
```

## File Structure

```
/home/msolercanals/zuruckbleibenbitte/
├── scripts/
│   ├── wifi_manager.py          # WiFi provisioning
│   ├── config_server.py          # Web interface
│   ├── main_train_display.py    # Main display script
│   ├── update_git.py             # Auto-update from git
│   ├── config.json               # WiFi & station config (gitignored)
│   ├── fonts/                    # LED fonts
│   └── templates/
│       └── index.html            # Web interface template
├── launcher.sh                   # Startup script
├── setup_wifi_provisioning.sh   # WiFi setup installer
├── train-display-config.service # Systemd service
└── networkmanager-wifi.pkla     # NetworkManager permissions
```

## Notes

- **config.json** is gitignored (contains WiFi passwords)
- WiFi provisioning runs automatically at boot
- Display shows IP for 10 seconds after connecting
- Config web server always runs in background on port 80
- LED matrix requires root/sudo access
