from datetime import date, time, datetime, timedelta
import pandas as pd
import requests
import time
import time
import sys
import json
import logging
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Load configuration
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "main_train_display.log")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_line_name(line_name):
    """Parse a line name into letter prefix and number.

    Handles various formats:
    - U5 -> ('U', '5')
    - S7 -> ('S', '7')
    - M10 -> ('M', '10')
    - 100 -> ('', '100')
    - 1 -> ('', '1')
    - N42 -> ('N', '42')

    Returns:
        tuple: (letter_part, number_part) - either can be empty string
    """
    line_str = str(line_name)

    # Find where digits start
    first_digit_pos = -1
    for i, char in enumerate(line_str):
        if char.isdigit():
            first_digit_pos = i
            break

    if first_digit_pos == -1:
        # No digits found, it's all letters (rare case)
        return (line_str, '')
    elif first_digit_pos == 0:
        # Starts with digit, no letter prefix
        return ('', line_str)
    else:
        # Has letter prefix
        return (line_str[:first_digit_pos], line_str[first_digit_pos:])


def load_config():
    """Load configuration from JSON file."""
    try:
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"Config file does not exist: {CONFIG_FILE}")
            return {
                "delay_minutes": 10,
                "train_station": {
                    "id": "900120004",
                    "name": "Warschauer Straße"
                },
                "transport_type": "U"  # Default to U-Bahn
            }

        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Only log this during startup and when delay changes
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
        return {
            "delay_minutes": 10,
            "train_station": {
                "id": "900120004",
                "name": "Warschauer Straße"
            },
            "transport_type": "U"  # Default to U-Bahn
        }

# Initial load
logger.info("Train Display starting up...")
config = load_config()
initial_delay = config.get('delay_minutes', 10)
initial_transport_type = config.get('transport_type', 'U')
logger.info(f"Initial delay setting: {initial_delay} minutes")
logger.info(f"Initial transport type: {initial_transport_type}")
id = config.get('train_station', {}).get('id', '900120004')
logger.info(f"Station ID: {id}")
url = 'https://v6.vbb.transport.rest/stops/' + id + '/departures?duration=60&duration=60'
options = RGBMatrixOptions()
options.rows = 32
options.cols = 192
options.brightness = 100
options.gpio_slowdown = 5
options.disable_hardware_pulsing = 1
options.hardware_mapping = 'adafruit-hat'
options.pwm_lsb_nanoseconds = 100


#options.isolcpus = 3
matrix = RGBMatrix(options = options)


offscreen_canvas = matrix.CreateFrameCanvas()

font_normal = graphics.Font()
font_big = graphics.Font()
font_small = graphics.Font()

FONTS_DIR = os.path.join(SCRIPT_DIR, "fonts")

font_normal.LoadFont(os.path.join(FONTS_DIR, "zuruckbleibenbitte_long.bdf"))
font_big.LoadFont(os.path.join(FONTS_DIR, "zuruckbleibenbitte_big.bdf"))
font_small.LoadFont(os.path.join(FONTS_DIR, "zuruckbleibenbitte_long.bdf"))

# real color =     textColor = graphics.Color(255, 1, 200) #color of the text

textColor = graphics.Color(255, 1, 200) #color of the text



last_delay = initial_delay  # Track last known delay value

# Display cycle tracking - show station name every 5 rounds
loop_counter = 0

while True:
    #Basic info
    try:
        # Reload config to get latest settings
        config = load_config()
        delay_minutes = config.get('delay_minutes', 10)
        transport_type_config = config.get('transport_type', 'U')  # Default to U-Bahn
        station_id = config.get('train_station', {}).get('id', '900120004')
        station_name = config.get('train_station', {}).get('name', 'Unknown Station')

        # Support multiple transport types (comma-separated string like "U,T,B")
        if isinstance(transport_type_config, str) and ',' in transport_type_config:
            selected_transport_types = [t.strip() for t in transport_type_config.split(',')]
        elif isinstance(transport_type_config, str):
            selected_transport_types = [transport_type_config]
        else:
            selected_transport_types = ['U']  # Default fallback

        # Check if we should show station name (every 5 rounds)
        loop_counter += 1
        should_show_station_name = (loop_counter % 5 == 0)

        if should_show_station_name:
            loop_counter = 0  # Reset counter after showing station name

        if should_show_station_name:
            # Display station name centered (split to 2 lines if too long)
            offscreen_canvas.Clear()

            # Character limit per line (roughly 30 chars at 6 pixels each for 192 pixel width)
            max_chars_per_line = 30

            if len(station_name) <= max_chars_per_line:
                # Short name - single line, vertically centered
                text_width_estimate = len(station_name) * 6
                x_position = max(3, (options.cols - text_width_estimate) // 2)
                y_position = 16  # Middle of the 32-pixel height
                graphics.DrawText(offscreen_canvas, font_normal, x_position, y_position, textColor, station_name)
            else:
                # Long name - split into two lines
                # Try to split at a good point (space, slash, or parenthesis)
                split_point = max_chars_per_line

                # Look for a good split point (space, slash, or paren) near the middle
                for delimiter in [' ', '/', '(']:
                    pos = station_name.rfind(delimiter, 0, max_chars_per_line + 5)
                    if pos > max_chars_per_line // 2:  # Only if it's reasonably centered
                        split_point = pos
                        break

                line1 = station_name[:split_point].strip()
                line2 = station_name[split_point:].strip()

                # Draw line 1 (top half)
                text_width_1 = len(line1) * 6
                x_pos_1 = max(3, (options.cols - text_width_1) // 2)
                graphics.DrawText(offscreen_canvas, font_normal, x_pos_1, 12, textColor, line1)

                # Draw line 2 (bottom half)
                text_width_2 = len(line2) * 6
                x_pos_2 = max(3, (options.cols - text_width_2) // 2)
                graphics.DrawText(offscreen_canvas, font_normal, x_pos_2, 24, textColor, line2)

            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(5)  # Short sleep when showing station name
            continue  # Skip the rest and loop again

        # Build URL with transport type filters
        # Map transport type codes to API parameter names
        transport_params = {
            'S': 'suburban',
            'U': 'subway',
            'T': 'tram',
            'B': 'bus',
            'F': 'ferry',
            'E': 'express',
            'R': 'regional'
        }

        # Build query string with selected transport types enabled
        filter_params = []
        for code, param_name in transport_params.items():
            # Enable if code is in selected_transport_types
            is_enabled = code in selected_transport_types
            filter_params.append(f"{param_name}={str(is_enabled).lower()}")

        filter_string = '&'.join(filter_params)
        current_url = f'https://v6.vbb.transport.rest/stops/{station_id}/departures?duration=60&{filter_string}'

        if current_url != url:
            url = current_url
            logger.info(f"Station changed to: {config.get('train_station', {}).get('name', 'Unknown')} (ID: {station_id})")
            logger.info(f"Transport type filter: {', '.join(selected_transport_types)}")

        # Log when delay changes
        if delay_minutes != last_delay:
            logger.info(f"Delay setting changed from {last_delay} to {delay_minutes} minutes")
            last_delay = delay_minutes

        res = requests.get(url= url)
        data = pd.json_normalize(res.json(), record_path =['departures'])

        # Use 'when' if available (actual/predicted time), otherwise fall back to 'plannedWhen'
        # Trams and buses often have 'when' as null, so we need the fallback
        data['Date'] = pd.to_datetime(data['when'].fillna(data['plannedWhen']), format = '%Y-%m-%dT%H:%M:%S%z')
        data = data[data.Date.notnull()].reset_index()

        if len(data) == 0:
            raise ValueError(f"No valid departure times found for {', '.join(selected_transport_types)}")

        tz_info = data['Date'][0].tzinfo

        # Filter by delay (API already filtered by transport type)
        future_departures = data[
            data['Date'] > datetime.now(tz_info) + timedelta(minutes = delay_minutes)].reset_index()
        future_departures = future_departures[['Date','direction','line.name','line.productName']]

        # Check if we have enough departures
        transport_types_str = ', '.join(selected_transport_types)
        if len(future_departures) < 2:
            logger.warning(f"Not enough {transport_types_str} departures found (found {len(future_departures)})")
            # Fallback: show whatever is available or show error message
            if len(future_departures) == 0:
                raise ValueError(f"No {transport_types_str} departures found")

        #Data scraped
        #building text:
        departure_time_0 = future_departures['Date'][0]
        departure_time_1 = future_departures['Date'][1] if len(future_departures) > 1 else future_departures['Date'][0]
        station_0 = str(future_departures['direction'][0])[0:16] + '         '
        station_1 = str(future_departures['direction'][1])[0:16] + '         ' if len(future_departures) > 1 else station_0

        line_0 = future_departures['line.name'][0]
        line_1 = future_departures['line.name'][1] if len(future_departures) > 1 else line_0

        train_0 = future_departures['line.productName'][0]
        train_1 = future_departures['line.productName'][1] if len(future_departures) > 1 else train_0

        time_diff_0 = departure_time_0 - datetime.now(tz_info)
        time_diff_1 = departure_time_1 - datetime.now(tz_info)

        minutes_0 = round(time_diff_0.seconds/60)
        minutes_1 = round(time_diff_1.seconds/60)

        in_x_min_text_0 = 'in ' + str(minutes_0) + ' min'
        in_x_min_text_1 = 'in ' + str(minutes_1) + ' min'

        # Parse line names to handle different formats (U5, M10, 100, etc.)
        letter_0, number_0 = parse_line_name(line_0)
        letter_1, number_1 = parse_line_name(line_1)

        offscreen_canvas.Clear() #probably to take out so it does not refresh (taking out also the if)

        # Draw first line - handle letter and number separately
        x_pos = 3
        if letter_0:
            # Draw letter if it exists
            x_pos += graphics.DrawText(offscreen_canvas, font_big, x_pos, 14, textColor, letter_0)
        if number_0:
            # Draw number
            x_pos += graphics.DrawText(offscreen_canvas, font_big, x_pos, 14, textColor, number_0)

        # Draw destination for first line (adjust spacing based on line name length)
        station_x_0 = max(27, x_pos + 3)  # At least 27, or after line name + small gap
        estacion_0 = graphics.DrawText(offscreen_canvas, font_normal, station_x_0, 14, textColor, station_0[0:20])

        min_0 = graphics.DrawText(offscreen_canvas, font_small, 140, 14, textColor, in_x_min_text_0)

        # Draw second line - handle letter and number separately
        x_pos = 3
        if letter_1:
            # Draw letter if it exists
            x_pos += graphics.DrawText(offscreen_canvas, font_big, x_pos, 29, textColor, letter_1)
        if number_1:
            # Draw number
            x_pos += graphics.DrawText(offscreen_canvas, font_big, x_pos, 29, textColor, number_1)

        # Draw destination for second line (adjust spacing based on line name length)
        station_x_1 = max(27, x_pos + 3)  # At least 27, or after line name + small gap
        estacion_1 = graphics.DrawText(offscreen_canvas, font_normal, station_x_1, 29, textColor, station_1[0:20])

        min_1 = graphics.DrawText(offscreen_canvas, font_small, 140, 29, textColor, in_x_min_text_1)

        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(30)  # Sleep for 30 seconds when showing train departures
    except Exception as error:
        logger.error(f"Error in main loop: {error}", exc_info=True)
        offscreen_canvas.Clear()  # Clear canvas before drawing error message
        texto_conectando = 'Connecting to Wifi.Wait 60 sec.'
        connectando_imprimir= graphics.DrawText(offscreen_canvas, font_small, 3, 14, textColor, texto_conectando)

        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(60)
