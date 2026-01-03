#!/usr/bin/env python3
"""
Configuration Web Server for Raspberry Pi Train Display
Provides web interface for WiFi setup and configuration
"""

import os
import json
import subprocess
from flask import Flask, render_template, request, jsonify, redirect
import threading
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

app = Flask(__name__, template_folder=os.path.join(SCRIPT_DIR, 'templates'))


def load_config():
    """Load configuration from JSON file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {
            "wifi_networks": [],
            "train_station": {
                "id": "900120004",
                "name": "Warschauer Straße"
            },
            "ap_mode": {
                "ssid": "TrainDisplay-Setup",
                "password": "trainsetup123"
            },
            "delay_minutes": 10
        }


def save_config(config):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def restart_wifi_async():
    """Restart WiFi manager in background after a delay."""
    def restart():
        print("Waiting 3 seconds before restarting WiFi...")
        time.sleep(3)
        print("Restarting WiFi manager...")
        try:
            # Stop the current hotspot
            subprocess.run(
                ['nmcli', 'connection', 'down', 'TrainDisplayHotspot'],
                capture_output=True,
                timeout=10
            )
            # Run wifi_manager.py to connect to the new network
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, 'wifi_manager.py')],
                timeout=60
            )
        except Exception as e:
            print(f"Error restarting WiFi: {e}")

    thread = threading.Thread(target=restart)
    thread.daemon = True
    thread.start()


def restart_train_display_async():
    """Restart train display service in background after a delay."""
    def restart():
        print("Waiting 2 seconds before restarting train display...")
        time.sleep(2)
        print("Restarting train display service...")
        try:
            # Try to restart the systemd service if it exists
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'train-display.service'],
                capture_output=True,
                timeout=10
            )
        except Exception as e:
            print(f"Error restarting train display: {e}")
            # If systemd service doesn't exist, try pkill and restart
            try:
                subprocess.run(['sudo', 'pkill', '-f', 'main_train_display.py'], capture_output=True)
                time.sleep(1)
                subprocess.Popen(['python3', os.path.join(SCRIPT_DIR, 'main_train_display.py')])
            except Exception as e2:
                print(f"Error using fallback restart method: {e2}")

    thread = threading.Thread(target=restart)
    thread.daemon = True
    thread.start()


@app.route('/')
def index():
    """Main configuration page."""
    config = load_config()
    return render_template('index.html', config=config)


@app.route('/api/networks', methods=['GET'])
def get_networks():
    """Get list of saved WiFi networks."""
    config = load_config()
    # Don't send passwords to the frontend
    networks = [{'ssid': n['ssid']} for n in config.get('wifi_networks', [])]
    return jsonify({'networks': networks})


@app.route('/api/wifi/add', methods=['POST'])
def add_wifi():
    """Add a new WiFi network."""
    try:
        data = request.get_json()
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '').strip()

        if not ssid:
            return jsonify({'success': False, 'error': 'SSID is required'}), 400

        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400

        config = load_config()

        # Check if network already exists
        existing_networks = config.get('wifi_networks', [])
        for i, network in enumerate(existing_networks):
            if network['ssid'] == ssid:
                # Update existing network and mark it as updated
                existing_networks[i]['password'] = password
                existing_networks[i]['password_updated'] = True
                config['wifi_networks'] = existing_networks
                save_config(config)

                # Trigger WiFi restart
                restart_wifi_async()

                return jsonify({
                    'success': True,
                    'message': f'Updated WiFi network: {ssid}. Connecting...'
                })

        # Add new network
        new_network = {
            'ssid': ssid,
            'password': password
        }

        if 'wifi_networks' not in config:
            config['wifi_networks'] = []

        config['wifi_networks'].append(new_network)
        save_config(config)

        # Trigger WiFi restart
        restart_wifi_async()

        return jsonify({
            'success': True,
            'message': f'Added WiFi network: {ssid}. Connecting...'
        })

    except Exception as e:
        print(f"Error adding WiFi: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wifi/remove', methods=['POST'])
def remove_wifi():
    """Remove a WiFi network."""
    try:
        data = request.get_json()
        ssid = data.get('ssid', '').strip()

        if not ssid:
            return jsonify({'success': False, 'error': 'SSID is required'}), 400

        config = load_config()
        networks = config.get('wifi_networks', [])

        # Filter out the network to remove
        config['wifi_networks'] = [n for n in networks if n['ssid'] != ssid]
        save_config(config)

        return jsonify({
            'success': True,
            'message': f'Removed WiFi network: {ssid}'
        })

    except Exception as e:
        print(f"Error removing WiFi: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/station/update', methods=['POST'])
def update_station():
    """Update train station configuration (for future use)."""
    try:
        data = request.get_json()
        station_id = data.get('station_id', '').strip()
        station_name = data.get('station_name', '').strip()

        if not station_id:
            return jsonify({'success': False, 'error': 'Station ID is required'}), 400

        config = load_config()
        config['train_station'] = {
            'id': station_id,
            'name': station_name
        }
        save_config(config)

        return jsonify({
            'success': True,
            'message': f'Updated station to: {station_name}'
        })

    except Exception as e:
        print(f"Error updating station: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status."""
    try:
        # Check WiFi connection
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'STATE', 'general'],
            capture_output=True,
            text=True,
            timeout=10
        )
        is_connected = 'connected' in result.stdout.lower()

        # Get current SSID if connected
        current_ssid = None
        if is_connected:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    current_ssid = line.split(':', 1)[1]
                    break

        config = load_config()

        return jsonify({
            'success': True,
            'wifi_connected': is_connected,
            'current_ssid': current_ssid,
            'train_station': config.get('train_station', {}),
            'saved_networks_count': len(config.get('wifi_networks', [])),
            'delay_minutes': config.get('delay_minutes', 10)
        })

    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delay/update', methods=['POST'])
def update_delay():
    """Update delay minutes configuration."""
    try:
        data = request.get_json()
        delay_minutes = data.get('delay_minutes')

        if delay_minutes is None:
            return jsonify({'success': False, 'error': 'delay_minutes is required'}), 400

        try:
            delay_minutes = int(delay_minutes)
            if delay_minutes < 0 or delay_minutes > 120:
                return jsonify({'success': False, 'error': 'Delay must be between 0 and 120 minutes'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'Delay must be a valid number'}), 400

        config = load_config()
        config['delay_minutes'] = delay_minutes
        save_config(config)

        # Restart the train display service
        restart_train_display_async()

        return jsonify({
            'success': True,
            'message': f'Updated delay to {delay_minutes} minutes. Restarting display...'
        })

    except Exception as e:
        print(f"Error updating delay: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    """Start the configuration web server."""
    print("=" * 50)
    print("Configuration Web Server Starting")
    print("=" * 50)
    print("Access at: http://192.168.4.1")
    print("=" * 50)

    # Run on all interfaces, port 80
    app.run(host='0.0.0.0', port=80, debug=False)


if __name__ == "__main__":
    main()
