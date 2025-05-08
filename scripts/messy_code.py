import time
import sys
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

def display_color_flash_market_mode(matrix, duration=30, set_duration=4, gpio_slowdown=4):
    """
    Display a negative market mode with randomly colored letters.
    Stocks are displayed in the four corners of the screen, with random letters 
    occasionally flashing in different colors for 0.5 seconds.
    
    Args:
        matrix: The initialized RGB matrix
        duration: Total time to display the mode (in seconds)
        set_duration: Time to display each set of 4 stocks (in seconds)
        gpio_slowdown: GPIO slowdown value to use (affects refresh rate)
    """
    import random
    
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
    
    # Set base color - text in red
    red_color = graphics.Color(255, 0, 0)
    
    # Define alternate flash colors
    flash_colors = [
        graphics.Color(0, 255, 0),     # Green
        graphics.Color(255, 255, 0),   # Yellow
        graphics.Color(255, 165, 0),   # Orange
        graphics.Color(0, 255, 255),   # Cyan
        graphics.Color(255, 0, 255)    # Magenta
    ]
    
    # Position settings for 4 quadrants
    # Y positions for top and bottom rows
    top_line_y_position = 14      # Top line position
    bottom_line_y_position = 28   # Bottom line position
    
    # X positions for left and right columns
    left_x_position = 3           # Left column position
    right_x_position = 100        # Right column position
    
    # Define the stocks with negative percentages
    negative_stocks = [
        "AAPL ---12.4%", "NFLX ---11.2%", "TSLA ---38.9%", "DB ---23.5%",
        "SSPH ---22.7%", "KBLAU ---7.9%", "MSFT ---8.5%", "META ---4.6%",
        "BRGHN ---45.6%", "SSPH ---18.7%", "AMZN ---17.3%", "SAP ---39.4%",
        "TRSR ---31.2%", "BRGHN ---9.1%", "BMW ---6.7%", "TSLA ---47.8%",
        "KTKT ---10.4%", "ABLNK ---6.3%", "GOOG ---29.8%", "ZLNDO ---8.8%",
        "ABLNK ---14.1%", "KTKT ---25.6%", "SIEM ---9.6%", "SIEM ---13.4%",
        "GRSM ---27.9%", "TRSR ---30.2%", "ADBE ---19.2%", "BMW ---15.0%"
    ]
    
    # Group stocks into sets of 4
    stock_sets = [negative_stocks[i:i+4] for i in range(0, len(negative_stocks), 4)]
    
    # Set start time
    start_time = time.time()
    set_index = 0
    set_start_time = time.time()
    
    # Initialize color flash timing variables
    flash_state = False  # Whether we're currently in a color flash state
    next_flash_time = time.time() + random.uniform(0.75, 1.25)  # Time for next color flash (~ every 1 second)
    flash_end_time = 0  # When the current flash should end
    
    # For tracking which characters will flash in which colors
    flash_chars = {}  # Will hold positions and colors for flashing characters
    
    print("Starting color flash market mode for", duration, "seconds")
    
    while time.time() - start_time < duration:
        current_time = time.time()
        
        # Check if it's time to change to the next set of 4 stocks
        if current_time - set_start_time >= set_duration:
            set_index = (set_index + 1) % len(stock_sets)
            set_start_time = current_time
            print(f"Displaying set {set_index + 1}/{len(stock_sets)}: {stock_sets[set_index]}")
            # Reset flash state when changing stock sets
            flash_state = False
            next_flash_time = current_time + random.uniform(1.5, 2.5)
        
        # Get current set of 4 stocks
        current_stocks = stock_sets[set_index]
        
        # Check if we need to start or end a flash
        if not flash_state and current_time >= next_flash_time:
            # Start a new flash
            flash_state = True
            flash_end_time = current_time + 0.5  # Flash for 0.5 seconds
            
            # Determine which characters to flash and what colors to use
            flash_chars = {}
            
            # For each stock string, randomly select 1-3 character positions to flash
            for stock_idx, stock in enumerate(current_stocks[:min(4, len(current_stocks))]):
                num_chars_to_flash = random.randint(1, min(3, len(stock)))
                positions = random.sample(range(len(stock)), num_chars_to_flash)
                
                for pos in positions:
                    # Assign a random color from our flash colors
                    flash_chars[(stock_idx, pos)] = random.choice(flash_colors)
            
            print(f"Flashing {len(flash_chars)} characters for 0.5 seconds")
        
        elif flash_state and current_time >= flash_end_time:
            # End the flash
            flash_state = False
            next_flash_time = current_time + random.uniform(0.75, 1.25)  # Schedule next flash (~every 1 second)
            print(f"Normal display for ~{round(next_flash_time - current_time, 1)} seconds")
        
        # Clear the canvas
        canvas.Clear()
        
        # Draw each of the 4 stocks in its designated corner
        stock_positions = [
            (left_x_position, top_line_y_position),      # Top-left
            (right_x_position, top_line_y_position),     # Top-right
            (left_x_position, bottom_line_y_position),   # Bottom-left
            (right_x_position, bottom_line_y_position)   # Bottom-right
        ]
        
        # Make sure we have stocks to display
        displayed_stocks = min(len(current_stocks), 4)
        for i in range(displayed_stocks):
            stock = current_stocks[i]
            x_pos, y_pos = stock_positions[i]
            
            if flash_state:
                # Draw character by character with some flashing
                for char_idx, char in enumerate(stock):
                    # Determine the color for this character
                    if (i, char_idx) in flash_chars:
                        char_color = flash_chars[(i, char_idx)]
                    else:
                        char_color = red_color
                    
                    # Calculate position for this character
                    # This is an approximation; character width varies with proportional fonts
                    # For monospace fonts, you can multiply by a fixed width
                    char_x = x_pos + char_idx * 6  # Assuming average 6 pixels per character
                    
                    # Draw the character
                    graphics.DrawText(canvas, font_stock, char_x, y_pos, char_color, char)
            else:
                # Regular display - draw the entire stock ticker in red
                graphics.DrawText(canvas, font_stock, x_pos, y_pos, red_color, stock)
        
        # Update the display
        canvas = matrix.SwapOnVSync(canvas)
        
        # Small delay for refresh rate
        time.sleep(0.05)  # Faster refresh during flashing
    
    print("Color flash market mode completed")
    
    # Clear the canvas before returning
    canvas.Clear()
    matrix.SwapOnVSync(canvas)
    
def display_stock_market_mode(matrix, duration=30, scroll_speed=0.03, gpio_slowdown=4):
    """
    Display a stock market mode showing two scrolling lines of companies and their percentages.
    
    Args:
        matrix: The initialized RGB matrix
        duration: How long to display the stock market (in seconds)
        scroll_speed: Time between frame updates (should match main program)
        gpio_slowdown: GPIO slowdown value to use (affects refresh rate)
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
    red_color = graphics.Color(0, 0, 255)
    
    # Position settings
    top_line_y_position = 14      # Top line position
    bottom_line_y_position = 28   # Bottom line position
    
    # Define the ticker text for both lines
    top_line = "   Apple +12.4%   Tesla +38.9%   Sisyphos +22.7%   Microsoft +8.5%   Berghain +45.6%   Amazon +17.3%   Tresor +31.2%   BMW +6.7%   KitKat +10.4%   Google +29.8%   About Blank +14.1%   Siemens +9.6%   Griessmuehle +27.9%   Adobe +19.2%"
    bottom_line = "   Netflix +11.2%   Deutsche Bank +23.5%   Kater Blau +7.9%   Meta +4.6%   Sisyphos +18.7%   SAP +39.4%   Berghain +9.1%   Tesla +47.8%   About Blank +6.3%   Zalando +8.8%   KitKat +25.6%   Siemens +13.4%   Tresor +30.2%   BMW +15.0%"
        
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


def display_negative_market_mode(matrix, duration=30, set_duration=4, gpio_slowdown=4):
    """
    Display a negative market mode showing 4 stocks simultaneously,
    positioned in the four corners of the screen (top-left, top-right, bottom-left, bottom-right).
    Each set of 4 stocks is displayed for 4 seconds.
    
    Args:
        matrix: The initialized RGB matrix
        duration: Total time to display the negative market mode (in seconds)
        set_duration: Time to display each set of 4 stocks (in seconds)
        gpio_slowdown: GPIO slowdown value to use (affects refresh rate)
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
    
    # Position settings for 4 quadrants
    # Y positions for top and bottom rows
    top_line_y_position = 14      # Top line position
    bottom_line_y_position = 28   # Bottom line position
    
    # X positions for left and right columns
    left_x_position = 3           # Left column position
    right_x_position = 100         # Right column position (adjusted based on your spec)
    
    # Define the stocks with negative percentages
    negative_stocks = [
        "AAPL ---12.4%", "NFLX ---11.2%", "TSLA ---38.9%", "DB ---23.5%",
        "SSPH ---22.7%", "KBLAU ---7.9%", "MSFT ---8.5%", "META ---4.6%",
        "BRGHN ---45.6%", "SSPH ---18.7%", "AMZN ---17.3%", "SAP ---39.4%",
        "TRSR ---31.2%", "BRGHN ---9.1%", "BMW ---6.7%", "TSLA ---47.8%",
        "KTKT ---10.4%", "ABLNK ---6.3%", "GOOG ---29.8%", "ZLNDO ---8.8%",
        "ABLNK ---14.1%", "KTKT ---25.6%", "SIEM ---9.6%", "SIEM ---13.4%",
        "GRSM ---27.9%", "TRSR ---30.2%", "ADBE ---19.2%", "BMW ---15.0%"
    ]
    
    # Group stocks into sets of 4
    stock_sets = [negative_stocks[i:i+4] for i in range(0, len(negative_stocks), 4)]
    
    # Set start time
    start_time = time.time()
    set_index = 0
    set_start_time = time.time()
    
    print("Starting negative market mode for", duration, "seconds")
    
    while time.time() - start_time < duration:
        # Check if it's time to change to the next set of 4 stocks
        current_time = time.time()
        if current_time - set_start_time >= set_duration:
            set_index = (set_index + 1) % len(stock_sets)
            set_start_time = current_time
            print(f"Displaying set {set_index + 1}/{len(stock_sets)}: {stock_sets[set_index]}")
        
        # Get current set of 4 stocks
        current_stocks = stock_sets[set_index]
        
        # Clear the canvas
        canvas.Clear()
        
        # Draw each of the 4 stocks in its designated corner
        # Make sure we have 4 stocks in the current set
        if len(current_stocks) >= 4:
            # Top-left corner
            graphics.DrawText(canvas, font_stock, left_x_position, top_line_y_position, red_color, current_stocks[0])
            
            # Top-right corner
            graphics.DrawText(canvas, font_stock, right_x_position, top_line_y_position, red_color, current_stocks[1])
            
            # Bottom-left corner
            graphics.DrawText(canvas, font_stock, left_x_position, bottom_line_y_position, red_color, current_stocks[2])
            
            # Bottom-right corner
            graphics.DrawText(canvas, font_stock, right_x_position, bottom_line_y_position, red_color, current_stocks[3])
        else:
            # If we have fewer than 4 stocks in the set, place them in order
            for i, stock in enumerate(current_stocks):
                if i == 0:
                    graphics.DrawText(canvas, font_stock, left_x_position, top_line_y_position, red_color, stock)
                elif i == 1:
                    graphics.DrawText(canvas, font_stock, right_x_position, top_line_y_position, red_color, stock)
                elif i == 2:
                    graphics.DrawText(canvas, font_stock, left_x_position, bottom_line_y_position, red_color, stock)
                # No need for i == 3 since we've already checked if len >= 4
        
        # Update the display
        canvas = matrix.SwapOnVSync(canvas)
        
        # Small delay for refresh rate
        time.sleep(0.1)
    
    print("Negative market mode completed")
    
    # Clear the canvas before returning
    canvas.Clear()
    matrix.SwapOnVSync(canvas)


def display_number_sequence(matrix, duration=30, scroll_speed=0.03, gpio_slowdown=4):
    """
    Display a scrolling sequence of numbers.
    
    Args:
        matrix: The initialized RGB matrix
        duration: How long to display each number (in seconds)
        scroll_speed: Time between frame updates
        gpio_slowdown: GPIO slowdown value to use (affects refresh rate)
    """
    # Create an offscreen canvas
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
            return

    # Set text color to red
    textColor = graphics.Color(255, 0, 0)
    
    # Vertical position adjusted to center the text
    text_y_position = 24  # Center the text vertically
    
    # Define the sequence of numbers to display
    number_sequence = ["301", "302", "142", "333"]
    sequence_index = 0
    
    # Start with the first number
    text_to_display = number_sequence[sequence_index]
    print(f"Displaying: {text_to_display} (for {duration} seconds)")
    
    # Initial position starts off-screen to the right
    pos = offscreen_canvas.width
    
    # Track when we started displaying the current number
    start_time = time.time()
    number_start_time = time.time()
    
    print("Starting number sequence display for", duration, "seconds")
    
    while time.time() - start_time < duration:
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
        if current_time - number_start_time >= duration / len(number_sequence):
            # Move to next number in the sequence
            sequence_index = (sequence_index + 1) % len(number_sequence)
            text_to_display = number_sequence[sequence_index]
            print(f"Displaying: {text_to_display}")
            
            # Reset the timer for this number
            number_start_time = current_time
        
        # Update the matrix display
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        
        # Wait a bit to control scroll speed
        time.sleep(scroll_speed)
    
    print("Number sequence display completed")
    
    # Clear the canvas before returning
    offscreen_canvas.Clear()
    matrix.SwapOnVSync(offscreen_canvas)


def initialize_matrix(gpio_slowdown=4):
    """
    Initialize and configure the RGB matrix.
    
    Args:
        gpio_slowdown: GPIO slowdown value to use
        
    Returns:
        The configured RGB matrix object
    """
    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 192  # Adjust if your matrix width is different
    options.brightness = 100
    options.gpio_slowdown = gpio_slowdown
    options.disable_hardware_pulsing = 1
    options.hardware_mapping = 'adafruit-hat'
    options.pwm_lsb_nanoseconds = 100
    
    # Initialize and return the matrix
    return RGBMatrix(options=options)


def run_display_cycle(matrix, mode_duration, scroll_speed, gpio_slowdown):
    """
    Run through a full cycle of all display modes.
    
    Args:
        matrix: The initialized RGB matrix
        mode_duration: Duration for each display mode
        scroll_speed: Scroll speed for scrolling displays
        gpio_slowdown: GPIO slowdown value to use
    """
    print(f"\nRunning display cycle with GPIO slowdown = {gpio_slowdown}")
    
    display_color_flash_market_mode(matrix, duration=mode_duration,
                              set_duration=4, gpio_slowdown=gpio_slowdown)

    # Display the negative market mode
    display_negative_market_mode(matrix, duration=mode_duration, 
                                set_duration=4, gpio_slowdown=gpio_slowdown)
    
    # Display the stock market mode
    display_stock_market_mode(matrix, duration=mode_duration, 
                             scroll_speed=scroll_speed, gpio_slowdown=gpio_slowdown)
    
    # Display the number sequence
    display_number_sequence(matrix, duration=mode_duration, 
                           scroll_speed=scroll_speed, gpio_slowdown=gpio_slowdown)


def main():
    # Set the default scroll speed and duration for each mode
    scroll_speed = 0.03  # Time in seconds between frame updates (lower is faster)
    mode_duration = 30   # Time in seconds to display each mode
    
    try:
        print("Press CTRL-C to stop.")
        
        # Main display loop - alternate between GPIO slowdown values
        while True:
            # First run with gpio_slowdown = 4
            gpio_slowdown = 4
            matrix = initialize_matrix(gpio_slowdown)
            run_display_cycle(matrix, mode_duration, scroll_speed, gpio_slowdown)
            
            # Then run with gpio_slowdown = 2
            gpio_slowdown = 2
            matrix = initialize_matrix(gpio_slowdown)
            run_display_cycle(matrix, mode_duration, scroll_speed, gpio_slowdown)
            
    except KeyboardInterrupt:
        print("Exiting.")
        matrix.Clear()  # Clear the matrix display on exit
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            matrix.Clear()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
