import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

def display_stock_market_mode(matrix, duration=30, scroll_speed=0.03):
    """
    Display a stock market mode showing two scrolling lines of companies and their percentages.
    
    Args:
        matrix: The initialized RGB matrix
        duration: How long to display the stock market (in seconds)
        scroll_speed: Time between frame updates (should match main program)
    """
    # Create a canvas
    canvas = matrix.CreateFrameCanvas()
    
    # Load the font for stock display
    font_stock = graphics.Font()
    try:
        font_stock.LoadFont("fonts/bfvlowermargen.bdf")
    except FileNotFoundError:
        print("Error: Could not load font 'bfvlowermargen.bdf'.")
        print("Please ensure the font file exists at the specified path.")
        return
    
    # Set color - all text in red
    red_color = graphics.Color(255, 0, 0)
    
    # Position settings
    top_line_y_position = 14      # Top line position
    bottom_line_y_position = 28   # Bottom line position
    
    # Define the ticker text for both lines
    top_line = "Apple +12.4% Tesla +38.9% Sisyphos +22.7% Microsoft +8.5% Berghain +45.6% Amazon +17.3% Tresor +31.2% BMW +6.7% KitKat +10.4% Google +29.8% About Blank +14.1% Siemens +9.6% Griessmuehle +27.9% Adobe +19.2%"
    bottom_line = "Netflix +11.2% Deutsche Bank +23.5% Kater Blau +7.9% Meta +4.6% Sisyphos +18.7% SAP +39.4% Berghain +9.1% Tesla +47.8% About Blank +6.3% Zalando +8.8% KitKat +25.6% Siemens +13.4% Tresor +30.2% BMW +15.0%"
    
    # Get the width of text to set initial positions
    canvas.Clear()
    top_line_width = graphics.DrawText(canvas, font_stock, 0, 0, red_color, top_line)
    bottom_line_width = graphics.DrawText(canvas, font_stock, 0, 0, red_color, bottom_line)
    
    # Initial positions - start from right edge
    top_pos = canvas.width
    bottom_pos = canvas.width
    
    # Set start time
    start_time = time.time()
    
    print("Starting stock market ticker mode for", duration, "seconds")
    
    while time.time() - start_time < duration:
        canvas.Clear()
        
        # Draw top scrolling line
        graphics.DrawText(canvas, font_stock, top_pos, top_line_y_position, red_color, top_line)
        
        # Draw bottom scrolling line
        graphics.DrawText(canvas, font_stock, bottom_pos, bottom_line_y_position, red_color, bottom_line)
        
        # Move positions one step to the left
        top_pos -= 1
        bottom_pos -= 1
        
        # If text has scrolled off the left edge, reset to right
        if top_pos + top_line_width < 0:
            top_pos = canvas.width
        
        if bottom_pos + bottom_line_width < 0:
            bottom_pos = canvas.width
        
        # Update the display
        canvas = matrix.SwapOnVSync(canvas)
        
        # Control the scrolling speed - match the main program's scroll speed
        time.sleep(scroll_speed)
    
    print("Stock market ticker mode completed")
    
    # Clear the canvas before returning
    canvas.Clear()
    matrix.SwapOnVSync(canvas)

# Main script
# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 192  # Adjust if your matrix width is different
options.brightness = 100
options.gpio_slowdown = 4
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

textColor = graphics.Color(255, 0, 0)  # Red color for text
scroll_speed = 0.03  # Time in seconds between frame updates (lower is faster)

# Vertical position adjusted to center the text
text_y_position = 24  # Center the text vertically

# Initial position starts off-screen to the right
pos = offscreen_canvas.width

# Define the sequence of numbers to display
number_sequence = ["301", "302", "142", "333"]
sequence_index = 0

# Time to display each number (in seconds)
display_time = 30

try:
    print("Press CTRL-C to stop.")
    
    # First display the stock market mode - passing the same scroll_speed
    display_stock_market_mode(matrix, duration=30, scroll_speed=scroll_speed)
    
    # Then continue with the number sequence display
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
