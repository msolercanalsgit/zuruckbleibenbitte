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

font_normal.LoadFont(os.path.join(FONTS_DIR, "bfvlowermargen.bdf"))
font_big.LoadFont(os.path.join(FONTS_DIR, "FixedBold-13.bdf"))
font_small.LoadFont(os.path.join(FONTS_DIR, "bfvlowermargen.bdf"))

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
        transport_type = config.get('transport_type', 'U')  # Default to U-Bahn
        station_id = config.get('train_station', {}).get('id', '900120004')
        station_name = config.get('train_station', {}).get('name', 'Unknown Station')

        # Check if we should show station name (every 5 rounds)
        loop_counter += 1
        should_show_station_name = (loop_counter % 5 == 0)

        if should_show_station_name:
            loop_counter = 0  # Reset counter after showing station name

        if should_show_station_name:
            # Display station name centered
            offscreen_canvas.Clear()

            # Calculate text width for centering (approximate: 6 pixels per character for font_normal)
            text_width_estimate = len(station_name) * 6  # Rough estimate
            x_position = max(3, (options.cols - text_width_estimate) // 2)
            y_position = 16  # Middle of the 32-pixel height

            graphics.DrawText(offscreen_canvas, font_normal, x_position, y_position, textColor, station_name)
            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(1)  # Short sleep when showing station name
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

        # Build query string with only selected transport type enabled
        filter_params = []
        for code, param_name in transport_params.items():
            # Enable only the configured transport type, disable others
            filter_params.append(f"{param_name}={str(code == transport_type).lower()}")

        filter_string = '&'.join(filter_params)
        current_url = f'https://v6.vbb.transport.rest/stops/{station_id}/departures?duration=60&{filter_string}'

        if current_url != url:
            url = current_url
            logger.info(f"Station changed to: {config.get('train_station', {}).get('name', 'Unknown')} (ID: {station_id})")
            logger.info(f"Transport type filter: {transport_type} ({transport_params.get(transport_type, 'unknown')})")

        # Log when delay changes
        if delay_minutes != last_delay:
            logger.info(f"Delay setting changed from {last_delay} to {delay_minutes} minutes")
            last_delay = delay_minutes

        res = requests.get(url= url)
        data = pd.json_normalize(res.json(), record_path =['departures'])
        data['Date'] = pd.to_datetime(data['when'], format = '%Y-%m-%dT%H:%M:%S%z')
        data = data[data.Date.notnull()].reset_index()
        tz_info = data['Date'][0].tzinfo

        # Filter by delay (API already filtered by transport type)
        future_departures = data[
            data['Date'] > datetime.now(tz_info) + timedelta(minutes = delay_minutes)].reset_index()
        future_departures = future_departures[['Date','direction','line.name','line.productName']]

        # Check if we have enough departures
        if len(future_departures) < 2:
            logger.warning(f"Not enough {transport_type} departures found (found {len(future_departures)})")
            # Fallback: show whatever is available or show error message
            if len(future_departures) == 0:
                raise ValueError(f"No {transport_type} departures found")

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

        offscreen_canvas.Clear() #probably to take out so it does not refresh (taking out also the if)
    
        line_letter_0 = graphics.DrawText(offscreen_canvas, font_big, 3, 14, textColor, str(line_0)[0:1])
        line_number_0 = graphics.DrawText(offscreen_canvas, font_big, 12, 14, textColor, str(line_0)[1:2])

        estacion_0 = graphics.DrawText(offscreen_canvas, font_normal, 27, 14, textColor, station_0[0:20])

        min_0 = graphics.DrawText(offscreen_canvas, font_small, 140, 14, textColor, in_x_min_text_0)


        line_letter_1 = graphics.DrawText(offscreen_canvas, font_big, 3, 29, textColor, str(line_1)[0:1])
        line_number_1 = graphics.DrawText(offscreen_canvas, font_big, 12, 29, textColor, str(line_1)[1:2])
    
        estacion_1 = graphics.DrawText(offscreen_canvas, font_normal, 27, 29, textColor, station_1[0:20])
    
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
