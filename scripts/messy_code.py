import time
import random
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 192 # Adjust if your matrix width is different
options.brightness = 100
options.gpio_slowdown = 5
options.disable_hardware_pulsing = 1
options.hardware_mapping = 'adafruit-hat'
options.pwm_lsb_nanoseconds = 100

matrix = RGBMatrix(options=options)
offscreen_canvas = matrix.CreateFrameCanvas()

# Load the big font
font_big = graphics.Font()
try:
    # Adjust path as needed for your setup
    font_big.LoadFont("rpi-rgb-led-matrix/fonts/FixedBold-13.bdf")
except:
    try:
        font_big.LoadFont("fonts/FixedBold-13.bdf")
    except FileNotFoundError:
        print("Error: Could not load font 'FixedBold-13.bdf'.")
        print("Please ensure the font file exists at the specified path.")
        sys.exit(1)


textColor = graphics.Color(255, 255, 0) # Yellow color for text
scroll_speed = 0.03 # Time in seconds between frame updates (lower is faster)
text_y_position = 14 # Vertical position of the text baseline

# Initial position starts off-screen to the right
pos = offscreen_canvas.width

def generate_random_numbers_text():
    """Generates a string of 3 random digits."""
    return "".join(str(random.randint(0, 9)) for _ in range(3))

try:
    print("Press CTRL-C to stop.")
    text_to_display = generate_random_numbers_text()
    while True:
        offscreen_canvas.Clear()

        # Draw the scrolling text
        # graphics.DrawText returns the width of the drawn text
        text_width = graphics.DrawText(offscreen_canvas, font_big, pos, text_y_position, textColor, text_to_display)

        # Move the position one step to the left
        pos -= 1

        # If the text has completely scrolled off the left edge...
        if (pos + text_width < 0):
            # Reset position to the right edge
            pos = offscreen_canvas.width
            # Generate new random numbers
            text_to_display = generate_random_numbers_text()
            print(f"Generated new numbers: {text_to_display}") # Optional: print new numbers to console

        # Update the matrix display
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

        # Wait a bit to control scroll speed
        time.sleep(scroll_speed)

except KeyboardInterrupt:
    print("Exiting.")
    matrix.Clear() # Clear the matrix display on exit
    sys.exit(0)
except Exception as e:
    print(f"An error occurred: {e}")
    matrix.Clear()
    sys.exit(1)
