#!/bin/bash
# Quick diagnostic script to check WiFi provisioning system status

echo "=========================================="
echo "WiFi Provisioning System Status Check"
echo "=========================================="
echo ""

echo "1. NetworkManager Status"
echo "----------------------------------------"
if systemctl is-active --quiet NetworkManager; then
    echo "✓ NetworkManager is RUNNING"
    nmcli general status
else
    echo "✗ NetworkManager is NOT RUNNING"
    echo "  Fix: sudo systemctl start NetworkManager"
fi
echo ""

echo "2. Current WiFi Connection"
echo "----------------------------------------"
nmcli device status | grep wifi || echo "No WiFi device found"
echo ""
CURRENT_SSID=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
if [ -n "$CURRENT_SSID" ]; then
    echo "✓ Connected to: $CURRENT_SSID"
else
    echo "✗ Not connected to any WiFi"
fi
echo ""

echo "3. Internet Connectivity"
echo "----------------------------------------"
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo "✓ Internet connection is working"
else
    echo "✗ No internet connection"
fi
echo ""

echo "4. Config Server Status"
echo "----------------------------------------"
if systemctl is-active --quiet train-display-config; then
    echo "✓ Config server is RUNNING"
else
    echo "✗ Config server is NOT RUNNING"
    echo "  Fix: sudo systemctl start train-display-config"
fi
echo ""

echo "5. Configuration File"
echo "----------------------------------------"
CONFIG_FILE="/home/msolercanals/zuruckbleibenbitte/scripts/config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "✓ Config file exists"
    echo "Saved networks:"
    python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print(f\"  {len(d.get('wifi_networks', []))} network(s) saved\")"
else
    echo "✗ Config file not found"
fi
echo ""

echo "6. Hostname Resolution"
echo "----------------------------------------"
HOSTNAME=$(hostname)
if grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts; then
    echo "✓ Hostname is in /etc/hosts"
else
    echo "✗ Hostname not in /etc/hosts (causes sudo warnings)"
    echo "  Fix: echo '127.0.1.1       $HOSTNAME' | sudo tee -a /etc/hosts"
fi
echo ""

echo "7. Required Packages"
echo "----------------------------------------"
packages=("network-manager" "python3-flask")
for pkg in "${packages[@]}"; do
    if dpkg -l | grep -q "^ii  $pkg"; then
        echo "✓ $pkg is installed"
    else
        echo "✗ $pkg is NOT installed"
    fi
done
echo ""

echo "=========================================="
echo "Quick Fixes"
echo "=========================================="
echo ""
echo "If NetworkManager is not running:"
echo "  sudo systemctl enable NetworkManager"
echo "  sudo systemctl start NetworkManager"
echo ""
echo "If config server is not running:"
echo "  sudo systemctl enable train-display-config"
echo "  sudo systemctl start train-display-config"
echo ""
echo "To re-run full setup:"
echo "  cd /home/msolercanals/zuruckbleibenbitte"
echo "  sudo ./setup_wifi_provisioning.sh"
echo ""
echo "=========================================="
