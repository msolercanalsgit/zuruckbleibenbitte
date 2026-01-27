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
import logging
from datetime import datetime
import requests

# Set up logging
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "config_server.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

app = Flask(__name__, template_folder=os.path.join(SCRIPT_DIR, 'templates'))


def load_config():
    """Load configuration from JSON file."""
    try:
        logger.info(f"Loading config from: {CONFIG_FILE}")
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"Config file does not exist: {CONFIG_FILE}")
            default_config = {
                "wifi_networks": [],
                "train_station": {
                    "id": "900120004",
                    "name": "Warschauer Straße"
                },
                "ap_mode": {
                    "ssid": "TrainDisplay-Setup",
                    "password": "trainsetup123"
                },
                "delay_minutes": 10,
                "transport_type": "U"
            }
            logger.info("Returning default config")
            return default_config

        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            logger.info(f"Config loaded successfully. WiFi networks: {len(config.get('wifi_networks', []))}, Delay: {config.get('delay_minutes', 10)}")
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
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
            "delay_minutes": 10,
            "transport_type": "U"
        }


def save_config(config):
    """Save configuration to JSON file with sync to ensure persistence."""
    try:
        logger.info(f"Saving config to: {CONFIG_FILE}")
        logger.info(f"Config to save - WiFi networks: {len(config.get('wifi_networks', []))}, Delay: {config.get('delay_minutes', 10)}")

        # Write to a temporary file first to avoid corruption
        temp_file = CONFIG_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(config, f, indent=2)
            f.flush()  # Flush to OS buffer
            os.fsync(f.fileno())  # Force write to disk

        # Move temp file to actual config file (atomic operation)
        os.replace(temp_file, CONFIG_FILE)

        # Set file permissions to be readable/writable by owner and group
        # This ensures the file can be accessed by different users/services
        try:
            os.chmod(CONFIG_FILE, 0o664)
            logger.info(f"File permissions set to 0o664 for {CONFIG_FILE}")
        except Exception as chmod_error:
            logger.warning(f"Could not set file permissions: {chmod_error}")

        # Verify the save by reading it back
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                logger.info(f"Verified save - WiFi networks: {len(saved_config.get('wifi_networks', []))}, Delay: {saved_config.get('delay_minutes', 10)}")
        except Exception as verify_error:
            logger.error(f"Failed to verify saved config: {verify_error}")
            return False

        logger.info("Config saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        return False


def restart_wifi_async():
    """Signal that WiFi config has changed - wifi_manager will detect it."""
    # Note: We don't actually restart anything here to avoid race conditions.
    # The wifi_manager running in AP mode will detect the new config and handle it.
    logger.info("WiFi configuration updated - wifi_manager will detect and apply changes")
    pass


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
    """Get list of saved WiFi networks with status."""
    config = load_config()
    # Don't send passwords to the frontend, but include status info
    networks = []
    for n in config.get('wifi_networks', []):
        network_info = {
            'ssid': n['ssid'],
            'last_attempt': n.get('last_attempt'),
            'last_attempt_success': n.get('last_attempt_success'),
            'last_error': n.get('last_error')
        }
        networks.append(network_info)
    return jsonify({'networks': networks})


@app.route('/api/wifi/add', methods=['POST'])
def add_wifi():
    """Add a new WiFi network."""
    try:
        data = request.get_json()
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '').strip()

        logger.info(f"API request to add WiFi network: {ssid}")

        if not ssid:
            logger.warning("WiFi add failed: SSID is required")
            return jsonify({'success': False, 'error': 'SSID is required'}), 400

        if not password:
            logger.warning("WiFi add failed: Password is required")
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


@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    """Search for stations by name using VBB API."""
    try:
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query parameter is required'}), 400

        logger.info(f"Searching for stations with query: {query}")

        # Use VBB API /locations endpoint which is more straightforward
        vbb_api_url = 'https://v6.vbb.transport.rest/locations'
        params = {
            'query': query,
            'results': 20,  # Limit to 20 results
            'stops': True,
            'addresses': False,
            'poi': False
        }

        response = requests.get(vbb_api_url, params=params, timeout=10)
        response.raise_for_status()

        locations_data = response.json()

        # Format the response - extract stations and deduplicate by name
        seen_stations = {}
        for location in locations_data:
            if location.get('type') != 'stop':
                continue

            station_name = location.get('name', '')
            station_id = location.get('id', '')

            # Extract base stop ID from station ID format: "de:11000:900100003" -> "900100003"
            stop_id = station_id
            if ':' in station_id:
                parts = station_id.split(':')
                if len(parts) >= 3:
                    # Get the numeric part: "de:11000:900100003" -> "900100003"
                    # Handle formats like "de:11000:900100003::1" -> "900100003"
                    base_part = parts[2].split('::')[0]
                    stop_id = base_part

            # Deduplicate by station name (keep first occurrence)
            if stop_id and station_name and station_name not in seen_stations:
                seen_stations[station_name] = {
                    'id': stop_id,  # Use the base stop ID for departures API
                    'name': station_name,
                    'latitude': location.get('location', {}).get('latitude'),
                    'longitude': location.get('location', {}).get('longitude'),
                    'products': location.get('products', {})
                }

        stations = list(seen_stations.values())

        logger.info(f"Found {len(stations)} stations matching '{query}'")
        
        return jsonify({
            'success': True,
            'stations': stations,
            'count': len(stations)
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling VBB API: {e}")
        return jsonify({'success': False, 'error': f'Failed to search stations: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error searching stations: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stations/nearby', methods=['GET'])
def nearby_stations():
    """Find stations near a given geolocation using VBB API."""
    try:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        
        if not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Latitude and longitude parameters are required'}), 400

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid latitude or longitude format'}), 400

        logger.info(f"Searching for stations near ({latitude}, {longitude})")

        # Use VBB API to find nearby locations
        vbb_api_url = 'https://v6.vbb.transport.rest/locations/nearby'
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'results': 20,  # Limit to 20 results
            'stops': True,  # Only return stops/stations
            'poi': False,  # Don't return POIs
            'language': 'en'
        }

        response = requests.get(vbb_api_url, params=params, timeout=10)
        response.raise_for_status()
        
        locations = response.json()
        
        # Format the response
        stations = []
        for location in locations:
            if location.get('type') == 'stop':
                stations.append({
                    'id': location.get('id'),
                    'name': location.get('name'),
                    'latitude': location.get('location', {}).get('latitude'),
                    'longitude': location.get('location', {}).get('longitude'),
                    'distance': location.get('distance'),  # Distance in meters
                    'products': location.get('products', {})
                })

        logger.info(f"Found {len(stations)} stations near ({latitude}, {longitude})")
        
        return jsonify({
            'success': True,
            'stations': stations,
            'count': len(stations)
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling VBB API: {e}")
        return jsonify({'success': False, 'error': f'Failed to find nearby stations: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error finding nearby stations: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/station/update', methods=['POST'])
def update_station():
    """Update train station configuration."""
    try:
        data = request.get_json()
        station_id = data.get('station_id', '').strip()
        station_name = data.get('station_name', '').strip()
        transport_type = data.get('transport_type', '').strip()

        if not station_id:
            return jsonify({'success': False, 'error': 'Station ID is required'}), 400

        # Validate transport type(s) if provided (can be comma-separated like "U,T,B")
        valid_transport_types = ['S', 'U', 'T', 'B', 'F', 'E', 'R']
        if transport_type:
            # Split by comma to support multiple types
            transport_types_list = [t.strip() for t in transport_type.split(',')]
            for tt in transport_types_list:
                if tt not in valid_transport_types:
                    return jsonify({'success': False, 'error': f'Invalid transport type "{tt}". Must be one of: {", ".join(valid_transport_types)}'}), 400

        logger.info(f"Updating station to: {station_name} (ID: {station_id})" + (f", transport type(s): {transport_type}" if transport_type else ""))

        config = load_config()
        config['train_station'] = {
            'id': station_id,
            'name': station_name
        }

        # Update transport type(s) if provided (stores as comma-separated string)
        if transport_type:
            config['transport_type'] = transport_type
        
        if save_config(config):
            logger.info(f"Station updated successfully to: {station_name}")
        else:
            logger.error("Failed to save config after station update")
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500

        # Restart the train display service to use the new station
        restart_train_display_async()

        message = f'Updated station to: {station_name}'
        if transport_type:
            transport_names = {'S': 'S-Bahn', 'U': 'U-Bahn', 'T': 'Tram', 'B': 'Bus', 'F': 'Ferry', 'E': 'Express', 'R': 'Regional'}
            # Convert comma-separated types to readable names
            types_list = [t.strip() for t in transport_type.split(',')]
            readable_types = [transport_names.get(t, t) for t in types_list]
            message += f' ({", ".join(readable_types)})'
        message += '. Restarting display...'

        return jsonify({
            'success': True,
            'message': message
        })

    except Exception as e:
        logger.error(f"Error updating station: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transport/update', methods=['POST'])
def update_transport_type():
    """Update transport type filter configuration."""
    try:
        data = request.get_json()
        transport_type = data.get('transport_type', '').strip().upper()

        # Validate transport type
        valid_transport_types = ['S', 'U', 'T', 'B', 'F', 'E', 'R']
        if not transport_type:
            return jsonify({'success': False, 'error': 'Transport type is required'}), 400
        
        if transport_type not in valid_transport_types:
            return jsonify({'success': False, 'error': f'Invalid transport type. Must be one of: {", ".join(valid_transport_types)}'}), 400

        logger.info(f"Updating transport type to: {transport_type}")

        config = load_config()
        config['transport_type'] = transport_type
        
        if save_config(config):
            logger.info(f"Transport type updated successfully to: {transport_type}")
        else:
            logger.error("Failed to save config after transport type update")
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500

        # Restart the train display service
        restart_train_display_async()

        transport_names = {'S': 'S-Bahn', 'U': 'U-Bahn', 'T': 'Tram', 'B': 'Bus', 'F': 'Ferry', 'E': 'Express', 'R': 'Regional'}
        return jsonify({
            'success': True,
            'message': f'Updated transport type to {transport_names.get(transport_type, transport_type)}. Restarting display...'
        })

    except Exception as e:
        logger.error(f"Error updating transport type: {e}", exc_info=True)
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
            'transport_type': config.get('transport_type', 'U'),
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

        logger.info(f"API request to update delay: {delay_minutes}")

        if delay_minutes is None:
            logger.warning("Delay update failed: delay_minutes is required")
            return jsonify({'success': False, 'error': 'delay_minutes is required'}), 400

        try:
            delay_minutes = int(delay_minutes)
            if delay_minutes < 0 or delay_minutes > 120:
                logger.warning(f"Delay update failed: Invalid value {delay_minutes}")
                return jsonify({'success': False, 'error': 'Delay must be between 0 and 120 minutes'}), 400
        except ValueError:
            logger.warning(f"Delay update failed: Invalid number format {delay_minutes}")
            return jsonify({'success': False, 'error': 'Delay must be a valid number'}), 400

        config = load_config()
        old_delay = config.get('delay_minutes', 10)
        config['delay_minutes'] = delay_minutes

        if save_config(config):
            logger.info(f"Delay updated successfully from {old_delay} to {delay_minutes}")
        else:
            logger.error("Failed to save config after delay update")
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500

        # Restart the train display service
        logger.info("Triggering train display restart")
        restart_train_display_async()

        return jsonify({
            'success': True,
            'message': f'Updated delay to {delay_minutes} minutes. Restarting display...'
        })

    except Exception as e:
        logger.error(f"Error updating delay: {e}", exc_info=True)
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
