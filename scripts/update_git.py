import os
import subprocess
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
import socket
import shutil
import datetime

# Function to log messages with timestamp to both LED screen and log file
def log_message(screen, matrix, font, text_color, message, log_file_path="log_timestamp.txt", display_time=5):
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp}: {message}"
    
    # Log to file
    with open(log_file_path, "a") as log_file:
        log_file.write(log_entry + "\n")
    
    # Display on LED screen
    screen.Clear()
    graphics.DrawText(screen, font, 3, 14, text_color, message)
    matrix.SwapOnVSync(screen)
    
    # Wait the specified time
    time.sleep(display_time)

def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

# Function to clear the screen
def clear_screen(screen, matrix):
    screen.Clear()
    return matrix.SwapOnVSync(screen)

# Function to verify repository was downloaded correctly
def verify_repository(repo_path, expected_files=None):
    """
    Verify that the repository was downloaded correctly.
    
    Args:
        repo_path: Path to the repository
        expected_files: List of files that should exist in the repository
                        If None, just checks if the directory exists and is not empty
    
    Returns:
        bool: True if repository passes verification, False otherwise
    """
    # First check if the directory exists
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        return False
    
    # Check if there's a .git directory (indicating this is actually a git repo)
    if not os.path.exists(os.path.join(repo_path, '.git')):
        return False
    
    # If expected_files is provided, check each file exists
    if expected_files:
        for file in expected_files:
            if not os.path.exists(os.path.join(repo_path, file)):
                return False
    else:
        # Otherwise just check if the directory is not empty (contains at least one file)
        files = os.listdir(repo_path)
        if len(files) <= 1:  # Only .git directory would mean empty repo
            return False
    
    return True

# Function to download code with verification and retry
def download_code(repo_url, clone_dir, max_retries=10, expected_files=None):
    """
    Download code from repository with verification and retry logic.
    
    Args:
        repo_url: URL of the GitHub repository
        clone_dir: Directory to clone into
        max_retries: Maximum number of retry attempts
        expected_files: List of files to verify exist after download
    
    Returns:
        tuple: (success (bool), repo_path (str))
    """
    repo_name = repo_url.split("/")[-1].replace('.git', "")
    repo_path = os.path.join(clone_dir, repo_name)
    
    for attempt in range(max_retries):
        try:
            if not os.path.exists(repo_path):
                # Clone the repository
                result = subprocess.run(['git', 'clone', repo_url, repo_path], 
                                       check=True, capture_output=True)
            else:
                # Update existing repository
                subprocess.run(['git', '-C', repo_path, "fetch", '--all'],
                              check=True, capture_output=True)
                subprocess.run(['git', '-C', repo_path, "reset", '--hard', 'origin/main'],
                              check=True, capture_output=True)
            
            # Verify the repository was downloaded correctly
            if verify_repository(repo_path, expected_files):
                return True, repo_path
            else:
                log_message(first_screen, matrix, font_normal, textColor, 
                          f"Repo verify failed #{attempt+1}", display_time=5)
                # If verification failed, remove the repo and try again
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
        except subprocess.CalledProcessError as e:
            log_message(first_screen, matrix, font_normal, textColor, 
                      f"Git failed #{attempt+1}", display_time=5)
            # If git command failed, wait and retry
            time.sleep(5)
        except Exception as e:
            log_message(first_screen, matrix, font_normal, textColor, 
                      f"Error #{attempt+1}: {str(e)[:20]}", display_time=5)
            time.sleep(5)
    
    # If we've reached here, all attempts failed
    return False, repo_path

def update_code(first_screen, matrix, font_normal, textColor):
    try:
        log_message(first_screen, matrix, font_normal, textColor, 'Updating code')
        
        GITHUB_REPO_URL = 'https://github.com/msolercanalsgit/zuruckbleibenbitte.git'
        CLONE_DIR = os.getcwd()
        
        # Expected files or directories that should exist in the repository
        # Update this list with actual important files in the repo
        expected_files = ['test_file.py']
        
        success, repo_path = download_code(GITHUB_REPO_URL, CLONE_DIR, expected_files=expected_files)
        
        if success:
            log_message(first_screen, matrix, font_normal, textColor, 
                       f"Code updated in: {repo_path.split('/')[-1]}", display_time=3)
        else:
            log_message(first_screen, matrix, font_normal, textColor, 'Update failed!', display_time=3)
        
        clear_screen(first_screen, matrix)
    
    except Exception as e:
        log_message(first_screen, matrix, font_normal, textColor, 
                   f'Update error: {str(e)[:20]}', display_time=5)
        log_message(first_screen, matrix, font_normal, textColor, 'No wifi?', display_time=5)
        clear_screen(first_screen, matrix)

# Initialize matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 192
options.brightness = 100
options.gpio_slowdown = 5
options.disable_hardware_pulsing = 1
options.hardware_mapping = 'adafruit-hat'
options.pwm_lsb_nanoseconds = 100

matrix = RGBMatrix(options = options)
first_screen = matrix.CreateFrameCanvas()

font_normal = graphics.Font()
font_normal.LoadFont("fonts/bfvlowermargen.bdf")
textColor = graphics.Color(255, 1, 200)  # color of the text

# Log script start
log_message(first_screen, matrix, font_normal, textColor, 'Starting script')

# Wait for internet connection
while not check_internet():
    log_message(first_screen, matrix, font_normal, textColor, 
               "No internet. Retrying...", display_time=5)
    clear_screen(first_screen, matrix)

log_message(first_screen, matrix, font_normal, textColor, "Internet connected!")

log_message(first_screen, matrix, font_normal, textColor, "Starting update")
update_code(first_screen, matrix, font_normal, textColor)
log_message(first_screen, matrix, font_normal, textColor, "Cleaning screen")
clear_screen(first_screen, matrix)
