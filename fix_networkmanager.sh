#!/bin/bash
# Quick fix script for NetworkManager issues

echo "=========================================="
echo "NetworkManager Quick Fix"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Step 1: Checking NetworkManager status..."
echo "----------------------------------------"
if systemctl is-active --quiet NetworkManager; then
    echo "✓ NetworkManager is running"
else
    echo "✗ NetworkManager is NOT running"
fi
systemctl status NetworkManager --no-pager || true
echo ""

echo "Step 2: Stopping conflicting services..."
echo "----------------------------------------"
systemctl stop dhcpcd 2>/dev/null || true
systemctl disable dhcpcd 2>/dev/null || true
echo "✓ Stopped dhcpcd"

systemctl stop wpa_supplicant 2>/dev/null || true
echo "✓ Stopped wpa_supplicant"
echo ""

echo "Step 3: Starting NetworkManager..."
echo "----------------------------------------"
systemctl unmask NetworkManager 2>/dev/null || true
systemctl enable NetworkManager
systemctl restart NetworkManager
sleep 3
echo ""

echo "Step 4: Checking status again..."
echo "----------------------------------------"
if systemctl is-active --quiet NetworkManager; then
    echo "✓ NetworkManager is NOW RUNNING!"
    nmcli general status
else
    echo "✗ NetworkManager FAILED to start"
    echo ""
    echo "Checking logs:"
    journalctl -u NetworkManager -n 20 --no-pager
fi
echo ""

echo "Step 5: Checking WiFi device..."
echo "----------------------------------------"
nmcli device status || echo "nmcli command failed"
echo ""

echo "Step 6: Listing available WiFi networks..."
echo "----------------------------------------"
nmcli device wifi list || echo "WiFi scan failed"
echo ""

echo "=========================================="
echo "Manual WiFi Connection (if needed)"
echo "=========================================="
echo ""
echo "To connect to WiFi manually:"
echo "  sudo nmcli dev wifi connect 'YourSSID' password 'YourPassword'"
echo ""
echo "To check connection:"
echo "  nmcli connection show"
echo ""
echo "=========================================="
