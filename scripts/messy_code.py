import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 192  # Adjust if your matrix width is different
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
    font_big.LoadFont("fonts/spleen-16x32.bdf")
except:
    try:
        font_big.LoadFont("fonts/FixedBold-13.bdf")
    except FileNotFoundError:
        print("Error: Could not load font 'FixedBold-13.bdf'.")
        print("Please ensure the font file exists at the specified path.")
        sys.exit(1)

textColor = graphics.Color(255, 255, 0)  # Yellow color for text
scroll_speed = 0.03  # Time in seconds between frame updates (lower is faster)

# Vertical position adjusted to center the text - assuming font height around 24px
# For a 32-row matrix, centering would be at approximately row 16
# But we need to account for the baseline of the font, so we'll position around 20-22
text_y_position = 22  # Center the text vertically (adjusted from 14)

# Initial position starts off-screen to the right
pos = offscreen_canvas.width

# Define the sequence of numbers to display
number_sequence = ["301", "302", "142", "333"]
sequence_index = 0

# Time to display each number (in seconds)
display_time = 30

try:
    print("Press CTRL-C to stop.")
    text_to_display = number_sequence[sequence_index]
    print(f"Displaying: {text_to_display} (for 30 seconds)")
    
    # Track when we started displaying the current number
    start_time = time.time()
    
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
        
        # Check if it's time to change to the next number
        current_time = time.time()
        if current_time - start_time >= display_time:
            # Move to next number in the sequence
            sequence_index = (sequence_index + 1) % len(number_sequence)
            text_to_display = number_sequence[sequence_index]
            print(f"Displaying: {text_to_display} (for 30 seconds)")
            
            # Reset the timer
            start_time = current_time
        
        # Update the matrix display
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        
        # Wait a bit to control scroll speed
        time.sleep(scroll_speed)
        
except KeyboardInterrupt:
    print("Exiting.")
    matrix.Clear()  # Clear the matrix display on exit
    sys.exit(0)
except Exception as e:
    print(f"An error occurred: {e}")
    matrix.Clear()
    sys.exit(1)
