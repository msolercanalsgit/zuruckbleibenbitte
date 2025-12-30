#!/bin/bash
# Installation script for Train Display WiFi Provisioning System
# Run this script on your Raspberry Pi to set up the WiFi provisioning feature

set -e  # Exit on error

echo "=========================================="
echo "Train Display WiFi Provisioning Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Install required packages
echo "Step 1: Installing required packages..."
echo "----------------------------------------"
apt-get update
apt-get install -y python3-pip python3-flask network-manager dnsmasq hostapd

# Install Python dependencies
echo ""
echo "Step 2: Installing Python dependencies..."
echo "----------------------------------------"
pip3 install flask --break-system-packages

# Make scripts executable
echo ""
echo "Step 3: Making scripts executable..."
echo "----------------------------------------"
chmod +x "$SCRIPT_DIR/scripts/wifi_manager.py"
chmod +x "$SCRIPT_DIR/scripts/config_server.py"
chmod +x "$SCRIPT_DIR/launcher.sh"

# Install systemd service for config server
echo ""
echo "Step 4: Installing systemd service..."
echo "----------------------------------------"
cp "$SCRIPT_DIR/train-display-config.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable train-display-config.service

# Stop conflicting services that might interfere with NetworkManager
echo ""
echo "Step 5: Configuring network services..."
echo "----------------------------------------"
systemctl stop dnsmasq
systemctl disable dnsmasq
systemctl stop hostapd
systemctl disable hostapd

# Enable and start NetworkManager
systemctl enable NetworkManager
systemctl start NetworkManager

# Create initial config if it doesn't exist
echo ""
echo "Step 6: Creating initial configuration..."
echo "----------------------------------------"
if [ ! -f "$SCRIPT_DIR/scripts/config.json" ]; then
    cat > "$SCRIPT_DIR/scripts/config.json" << 'EOF'
{
  "wifi_networks": [],
  "train_station": {
    "id": "900120004",
    "name": "Warschauer Straße"
  },
  "ap_mode": {
    "ssid": "TrainDisplay-Setup",
    "password": "trainsetup123"
  }
}
EOF
    echo "Created default config.json"
else
    echo "config.json already exists, skipping..."
fi

# Set proper permissions
chown -R msolercanals:msolercanals "$SCRIPT_DIR/scripts"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "The WiFi provisioning system is now installed."
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. On first boot, if no WiFi is configured, it will create"
echo "   a hotspot named: TrainDisplay-Setup"
echo "   Password: trainsetup123"
echo "3. Connect to this network with your phone"
echo "4. Open a browser and go to: http://192.168.4.1"
echo "5. Enter your WiFi credentials and connect"
echo ""
echo "The config web server will always run in the background,"
echo "so you can access it anytime at the Pi's IP address once"
echo "it's connected to your home WiFi."
echo ""
echo "=========================================="
