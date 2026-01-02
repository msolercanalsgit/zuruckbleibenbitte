#!/usr/bin/env python3
"""
WiFi Manager for Raspberry Pi Train Display
Handles switching between AP mode (for setup) and client mode (normal operation)
"""

import os
import json
import subprocess
import time
import socket

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
FONTS_DIR = os.path.join(SCRIPT_DIR, "fonts")
AP_INTERFACE = "wlan0"
AP_SSID_DEFAULT = "TrainDisplay-Setup"
AP_PASSWORD_DEFAULT = "trainsetup123"
AP_IP = "10.42.0.1"  # NetworkManager's default hotspot IP

# LED matrix globals (will be initialized in main)
matrix = None
screen = None
font = None
text_color = None


def display_message(message, display_time=2):
    """Display a message on the LED screen."""
    global matrix, screen, font, text_color

    try:
        print(message)

        if screen and matrix and font and text_color:
            from rgbmatrix import graphics
            screen.Clear()
            graphics.DrawText(screen, font, 3, 14, text_color, message[:30])
            matrix.SwapOnVSync(screen)

        time.sleep(display_time)
    except Exception as e:
        print(f"Display error: {e}")


def clear_screen():
    """Clear the LED screen."""
    global matrix, screen

    try:
        if screen and matrix:
            screen.Clear()
            matrix.SwapOnVSync(screen)
    except Exception as e:
        print(f"Screen clear error: {e}")


def load_config():
    """Load configuration from JSON file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default config if it doesn't exist
            default_config = {
                "wifi_networks": [],
                "train_station": {
                    "id": "900120004",
                    "name": "Warschauer Straße"
                },
                "ap_mode": {
                    "ssid": AP_SSID_DEFAULT,
                    "password": AP_PASSWORD_DEFAULT
                }
            }
            save_config(default_config)
            return default_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def save_config(config):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Check if we have internet connectivity."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except socket.error:
        return False


def get_local_ip():
    """Get the local IP address of the Pi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def is_wifi_connected():
    """Check if WiFi is connected using nmcli."""
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'STATE', 'general'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return 'connected' in result.stdout.lower()
    except Exception as e:
        print(f"Error checking WiFi connection: {e}")
        return False


def get_current_ssid():
    """Get the SSID of the currently connected network."""
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.split('\n'):
            if line.startswith('yes:'):
                return line.split(':', 1)[1]
        return None
    except Exception as e:
        print(f"Error getting current SSID: {e}")
        return None


def connect_to_wifi(ssid, password, force_recreate=False):
    """Connect to a WiFi network using NetworkManager."""
    display_message(f"Connecting to {ssid[:15]}...", 1)

    try:
        # Check if connection already exists
        check_result = subprocess.run(
            ['nmcli', 'connection', 'show', ssid],
            capture_output=True,
            timeout=10
        )
        connection_exists = (check_result.returncode == 0)

        # If forcing recreate or connection doesn't exist, create new one
        if force_recreate or not connection_exists:
            if connection_exists:
                print(f"Removing old connection profile for: {ssid}")
                subprocess.run(
                    ['nmcli', 'connection', 'delete', ssid],
                    capture_output=True,
                    timeout=10
                )

            # Trigger a WiFi scan to ensure network is visible
            print("Scanning for WiFi networks...")
            subprocess.run(
                ['nmcli', 'dev', 'wifi', 'rescan'],
                capture_output=True,
                timeout=10
            )
            time.sleep(3)  # Wait for scan to complete

            # Create new connection with the password
            print(f"Creating new connection: {ssid}")
            result = subprocess.run(
                ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password],
                capture_output=True,
                text=True,
                timeout=30
            )
        else:
            # Connection exists, just try to activate it
            print(f"Connection profile exists, activating: {ssid}")
            result = subprocess.run(
                ['nmcli', 'connection', 'up', ssid],
                capture_output=True,
                text=True,
                timeout=30
            )

        if result.returncode == 0:
            print(f"Successfully connected to {ssid}")
            return True
        else:
            print(f"Failed to connect to {ssid}: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False


def start_ap_mode(ssid, password):
    """Start Access Point mode using NetworkManager."""
    display_message("Starting setup mode...", 1)

    try:
        # Delete existing hotspot connection if it exists
        subprocess.run(
            ['nmcli', 'connection', 'delete', 'TrainDisplayHotspot'],
            capture_output=True,
            timeout=10
        )

        # Create new hotspot
        result = subprocess.run(
            [
                'nmcli', 'dev', 'wifi', 'hotspot',
                'ifname', AP_INTERFACE,
                'con-name', 'TrainDisplayHotspot',
                'ssid', ssid,
                'password', password
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"AP mode started successfully: {ssid}")
            print(f"Connect to this network and visit http://{AP_IP}")
            return True
        else:
            print(f"Failed to start AP mode: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error starting AP mode: {e}")
        return False


def stop_ap_mode():
    """Stop Access Point mode."""
    print("Stopping AP mode...")

    try:
        result = subprocess.run(
            ['nmcli', 'connection', 'down', 'TrainDisplayHotspot'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("AP mode stopped")
            return True
        else:
            print(f"Failed to stop AP mode: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error stopping AP mode: {e}")
        return False


def try_saved_networks(config, max_retries=2):
    """Try to connect to saved WiFi networks in order with retries."""
    networks = config.get('wifi_networks', [])

    if not networks:
        print("No saved WiFi networks found")
        return False

    print(f"Found {len(networks)} saved network(s)")
    display_message(f"Trying {len(networks)} network(s)...", 1)

    # Check if we're already connected to one of the saved networks
    current_ssid = get_current_ssid()
    if current_ssid:
        for network in networks:
            if network.get('ssid') == current_ssid:
                print(f"Already connected to saved network: {current_ssid}")
                if check_internet():
                    print(f"Internet OK on {current_ssid}")
                    display_message(f"Connected to {current_ssid[:15]}", 2)

                    # Display IP address for 10 seconds
                    ip = get_local_ip()
                    if ip:
                        print(f"IP Address: {ip}")
                        print(f"Access config at: http://{ip}")
                        display_message(f"IP: {ip}", 10)

                    return True
                else:
                    print(f"Connected to {current_ssid} but no internet, will retry...")
                    break

    for network in networks:
        ssid = network.get('ssid')
        password = network.get('password')
        password_updated = network.get('password_updated', False)

        if not ssid or not password:
            continue

        # Try this network multiple times before giving up
        for attempt in range(1, max_retries + 1):
            print(f"Trying to connect to: {ssid} (attempt {attempt}/{max_retries})")
            display_message(f"Try {attempt}/{max_retries}: {ssid[:12]}", 2)

            # Force recreate connection if password was just updated
            if connect_to_wifi(ssid, password, force_recreate=password_updated):
                # Wait for connection to stabilize and internet to come up
                display_message("Verifying...", 3)
                time.sleep(5)

                # Check if WiFi is connected
                if is_wifi_connected():
                    # Give internet more time to come up (DHCP, DNS, etc.)
                    print("WiFi connected, waiting for internet...")
                    time.sleep(15)

                    if check_internet():
                        print(f"Successfully connected to {ssid} with internet!")
                        display_message(f"Connected to {ssid[:15]}", 2)

                        # Clear password_updated flag if it was set
                        if password_updated:
                            config = load_config()
                            for net in config.get('wifi_networks', []):
                                if net.get('ssid') == ssid:
                                    net.pop('password_updated', None)
                            save_config(config)

                        # Display IP address for 10 seconds so user can access config
                        ip = get_local_ip()
                        if ip:
                            print(f"IP Address: {ip}")
                            print(f"Access config at: http://{ip}")
                            display_message(f"IP: {ip}", 10)

                        return True
                    else:
                        print(f"Connected to {ssid} but no internet yet, retrying...")
                        display_message("No internet, retry...", 2)
                else:
                    print(f"Connection to {ssid} failed")
                    display_message("Connection failed", 2)
            else:
                print(f"Connection attempt {attempt} failed")
                if attempt < max_retries:
                    display_message("Retrying...", 2)
                    time.sleep(2)

        # All retries failed for this network
        print(f"Failed to connect to {ssid} after {max_retries} attempts")
        display_message(f"Failed: {ssid[:15]}", 2)
        time.sleep(1)

    return False


def main():
    """Main WiFi manager logic."""
    global matrix, screen, font, text_color

    print("=" * 50)
    print("WiFi Manager Starting")
    print("=" * 50)

    # Initialize the LED matrix
    try:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 192
        options.brightness = 100
        options.gpio_slowdown = 5
        options.disable_hardware_pulsing = 1
        options.hardware_mapping = 'adafruit-hat'
        options.pwm_lsb_nanoseconds = 100

        matrix = RGBMatrix(options=options)
        screen = matrix.CreateFrameCanvas()

        # Load font
        font = graphics.Font()
        font_path = os.path.join(FONTS_DIR, "bfvlowermargen.bdf")

        if not os.path.exists(font_path):
            print(f"WARNING: Font not found at {font_path}")
            matrix = None
            screen = None
        else:
            font.LoadFont(font_path)
            text_color = graphics.Color(255, 1, 200)

    except Exception as e:
        print(f"Cannot initialize LED matrix (need root): {e}")
        print("Continuing without LED display...")
        matrix = None
        screen = None

    display_message("WiFi Manager...", 1)

    config = load_config()
    if not config:
        display_message("Config error!", 3)
        print("ERROR: Could not load configuration")
        return

    # Check if already connected
    display_message("Checking WiFi...", 1)
    if is_wifi_connected():
        current_ssid = get_current_ssid()
        print(f"Already connected to: {current_ssid}")

        if check_internet():
            print("Internet connection verified!")
            display_message(f"WiFi OK: {current_ssid[:15]}", 2)

            # Display IP address for 10 seconds so user can access config
            ip = get_local_ip()
            if ip:
                print(f"IP Address: {ip}")
                print(f"Access config at: http://{ip}")
                display_message(f"IP: {ip}", 10)

            clear_screen()
            return
        else:
            print("Connected but no internet, will retry...")
            display_message("No internet!", 2)

    # Try to connect to saved networks
    print("\nAttempting to connect to saved networks...")
    if try_saved_networks(config):
        print("Successfully connected to WiFi!")
        clear_screen()
        return

    # No saved networks or couldn't connect - start AP mode
    print("\nNo WiFi connection available")
    print("Starting Access Point mode for setup...")

    ap_config = config.get('ap_mode', {})
    ap_ssid = ap_config.get('ssid', AP_SSID_DEFAULT)
    ap_password = ap_config.get('password', AP_PASSWORD_DEFAULT)

    if start_ap_mode(ap_ssid, ap_password):
        print("\n" + "=" * 50)
        print("SETUP MODE ACTIVE")
        print("=" * 50)
        print(f"WiFi Network: {ap_ssid}")
        print(f"Password: {ap_password}")
        print(f"Setup URL: http://{AP_IP}")
        print("=" * 50)

        # Start the config web server in background
        print("Starting configuration web server...")
        try:
            config_server_path = os.path.join(SCRIPT_DIR, 'config_server.py')
            subprocess.Popen(
                ['sudo', 'python3', config_server_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)  # Give it time to start
            print("Config server started on port 80")
        except Exception as e:
            print(f"Warning: Could not start config server: {e}")

        # Display setup instructions on LED - loop until WiFi is configured
        print("Waiting for WiFi configuration via web interface...")

        check_count = 0
        while True:
            # Cycle through setup messages
            if check_count % 4 == 0:
                display_message("SETUP MODE", 2)
            elif check_count % 4 == 1:
                display_message(f"WiFi: {ap_ssid[:20]}", 2)
            elif check_count % 4 == 2:
                display_message(f"Pass: {ap_password[:20]}", 2)
            else:
                display_message(f"Go to {AP_IP}", 2)

            check_count += 1

            # Check if WiFi networks have been added to config
            config = load_config()
            if config and config.get('wifi_networks'):
                networks = config.get('wifi_networks', [])
                print(f"\n{len(networks)} WiFi network(s) configured!")
                display_message("WiFi configured!", 2)
                display_message("Connecting...", 2)

                # Stop AP mode
                stop_ap_mode()

                # Try to connect to the configured networks
                if try_saved_networks(config):
                    display_message("Connected!", 2)
                    print("Successfully connected to WiFi!")
                    clear_screen()
                    return
                else:
                    # Failed to connect, go back to AP mode
                    display_message("Connection failed!", 2)
                    print("Failed to connect to configured network, restarting AP mode...")
                    time.sleep(3)
                    if not start_ap_mode(ap_ssid, ap_password):
                        print("ERROR: Could not restart AP mode")
                        break
                    check_count = 0  # Reset display cycle

            # Wait before checking again
            time.sleep(1)
    else:
        print("ERROR: Could not start AP mode")
        display_message("AP mode failed!", 3)

    # Clear screen before exiting
    clear_screen()


if __name__ == "__main__":
    main()
