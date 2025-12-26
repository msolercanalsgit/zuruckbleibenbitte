from datetime import date, time, datetime, timedelta
import pandas as pd
import requests
import time
import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics


id = '900120004' #warschauerstrasse station id  
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

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(SCRIPT_DIR, "fonts")

font_normal.LoadFont(os.path.join(FONTS_DIR, "bfvlowermargen.bdf"))
font_big.LoadFont(os.path.join(FONTS_DIR, "FixedBold-13.bdf"))
font_small.LoadFont(os.path.join(FONTS_DIR, "bfvlowermargen.bdf"))

# real color =     textColor = graphics.Color(255, 1, 200) #color of the text

textColor = graphics.Color(255, 1, 200) #color of the text



while True:
    #Basic info
    try:
        res = requests.get(url= url)
        data = pd.json_normalize(res.json(), record_path =['departures'])
        data['Date'] = pd.to_datetime(data['when'], format = '%Y-%m-%dT%H:%M:%S%z')
        data = data[data.Date.notnull()].reset_index()
        tz_info = data['Date'][0].tzinfo

        future_ubahns = data[
            (data['Date'] > datetime.now(tz_info) + timedelta(minutes = 10))
            & (data['line.productName'] == 'U')].reset_index()
        future_ubahns = future_ubahns[['Date','direction','line.name','line.productName']]

        #Data scraped
        #building text:
        departure_time_0 = future_ubahns['Date'][0]
        departure_time_1 = future_ubahns['Date'][1]
        station_0 = str(future_ubahns['direction'][0]) + '         '
        station_1 = str(future_ubahns['direction'][1]) + '         '

        line_0 = future_ubahns['line.name'][0]
        line_1 = future_ubahns['line.name'][1]

        train_0 = future_ubahns['line.productName'][0]
        train_1 = future_ubahns['line.productName'][1]

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
    except Exception as error:
        print(error)
        texto_conectando = 'Connecting to Wifi.Wait 60 sec.'
        connectando_imprimir= graphics.DrawText(offscreen_canvas, font_small, 3, 14, textColor, texto_conectando)

        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

    #print(pos_test)
    time.sleep(60)
