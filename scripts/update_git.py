import os
import subprocess
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
import socket
import datetime

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
FONTS_DIR = os.path.join(SCRIPT_DIR, "rpi-rgb-led-matrix/fonts")
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "log_timestamp.txt")

GITHUB_REPO_URL = 'https://github.com/msolercanalsgit/zuruckbleibenbitte.git'
EXPECTED_FILES = ['messy_code_old.py']

# =============================================================================
# VERSION TRACKING
# =============================================================================
def get_git_version(repo_path):
    """Get the current git commit hash and date from a repository."""
    try:
        # Get short commit hash (7 characters)
        result = subprocess.run(
            ['git', '-C', repo_path, 'rev-parse', '--short=7', 'HEAD'],
            capture_output=True, text=True, timeout=10
        )
        commit_hash = result.stdout.strip() if result.returncode == 0 else "unknown"
        
        # Get commit date
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-1', '--format=%cd', '--date=format:%d/%m %H:%M'],
            capture_output=True, text=True, timeout=10
        )
        commit_date = result.stdout.strip() if result.returncode == 0 else ""
        
        return commit_hash, commit_date
    except Exception as e:
        print(f"Error getting git version: {e}")
        return "error", ""


def display_version_info(screen, matrix, font, text_color, repo_path, update_success):
    """Display the current version on the LED screen for verification."""
    try:
        commit_hash, commit_date = get_git_version(repo_path)
        
        screen.Clear()
        
        if update_success:
            # Line 1: Success message with commit hash
            line1 = f"Updated: {commit_hash}"
            # Line 2: Commit date
            line2 = f"Date: {commit_date}"
        else:
            line1 = "Update FAILED!"
            line2 = f"Local: {commit_hash}"
        
        graphics.DrawText(screen, font, 3, 14, text_color, line1)
        graphics.DrawText(screen, font, 3, 28, text_color, line2)
        matrix.SwapOnVSync(screen)
        
        # Display for 8 seconds so you can see it
        time.sleep(8)
        
        print(f"Displayed version: {commit_hash} ({commit_date})")
        
    except Exception as e:
        print(f"Error displaying version: {e}")


# =============================================================================
# LOGGING FUNCTION
# =============================================================================
def log_message(screen, matrix, font, text_color, message, display_time=3):
    """Log messages to both the LED screen and a log file with timestamps."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}: {message}"
        
        print(log_entry)
        
        try:
            with open(LOG_FILE_PATH, "a") as log_file:
                log_file.write(log_entry + "\n")
        except Exception as e:
            print(f"Could not write to log file: {e}")

        screen.Clear()
        graphics.DrawText(screen, font, 3, 14, text_color, message[:30])
        matrix.SwapOnVSync(screen)
        time.sleep(display_time)
    except Exception as e:
        print(f"Logging/display error: {e}")


def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Check if internet connection is available."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except socket.error:
        return False


def clear_screen(screen, matrix):
    """Clear the LED screen."""
    try:
        screen.Clear()
        matrix.SwapOnVSync(screen)
    except Exception as e:
        print(f"Screen clear error: {e}")


def verify_repository(repo_path, expected_files=None):
    """Verify that the repository was cloned correctly."""
    try:
        if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
            print(f"Repository path does not exist: {repo_path}")
            return False

        git_dir = os.path.join(repo_path, '.git')
        if not os.path.exists(git_dir):
            print(f".git directory not found in: {repo_path}")
            return False

        if expected_files:
            for file in expected_files:
                file_path = os.path.join(repo_path, file)
                if not os.path.exists(file_path):
                    print(f"Expected file not found: {file_path}")
                    return False

        return True
    except Exception as e:
        print(f"Verify error: {e}")
        return False


def download_code(screen, matrix, font, text_color, repo_url, repo_path, max_retries=5, expected_files=None):
    """Update the repository in place with retry logic."""
    print(f"Repository URL: {repo_url}")
    print(f"Repository path: {repo_path}")

    for attempt in range(1, max_retries + 1):
        try:
            log_message(screen, matrix, font, text_color, f"Update {attempt}/{max_retries}...")

            if not os.path.exists(os.path.join(repo_path, '.git')):
                print(f"No git repo found at {repo_path}, cannot update")
                return False, repo_path

            print(f"Updating repository at {repo_path}...")

            # Fetch all changes
            subprocess.run(
                ['git', '-C', repo_path, 'fetch', '--all'],
                check=True, capture_output=True, text=True, timeout=60
            )

            # Reset to origin/main
            subprocess.run(
                ['git', '-C', repo_path, 'reset', '--hard', 'origin/main'],
                check=True, capture_output=True, text=True, timeout=60
            )
            print("Git fetch and reset completed")

            if verify_repository(repo_path, expected_files):
                return True, repo_path
            else:
                log_message(screen, matrix, font, text_color, f"Verify failed #{attempt}")

        except subprocess.TimeoutExpired:
            log_message(screen, matrix, font, text_color, f"Timeout #{attempt}")
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            log_message(screen, matrix, font, text_color, f"Git error #{attempt}")
            print(f"Git error: {e.stderr}")
            time.sleep(5)
        except Exception as e:
            log_message(screen, matrix, font, text_color, f"Error #{attempt}")
            print(f"Exception: {e}")
            time.sleep(5)

    return False, repo_path


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print("=" * 50)
    print("ZURUCKBLEIBENBITTE UPDATE SCRIPT")
    print(f"Started at: {datetime.datetime.now()}")
    print(f"Script location: {SCRIPT_DIR}")
    print("=" * 50)
    
    os.chdir(SCRIPT_DIR)
    
    try:
        # Initialize the LED matrix
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 192
        options.brightness = 100
        options.gpio_slowdown = 5
        options.disable_hardware_pulsing = 1
        options.hardware_mapping = 'adafruit-hat'
        options.pwm_lsb_nanoseconds = 100

        matrix = RGBMatrix(options=options)
        screen = matrix.CreateFrameCanvas()

        # Load font
        font_normal = graphics.Font()
        font_path = os.path.join(FONTS_DIR, "bfvlowermargen.bdf")
        
        if not os.path.exists(font_path):
            print(f"ERROR: Font not found at {font_path}")
            return
            
        font_normal.LoadFont(font_path)
        text_color = graphics.Color(255, 1, 200)

        log_message(screen, matrix, font_normal, text_color, 'Starting...')

        # Wait for internet
        internet_attempts = 0
        while not check_internet():
            internet_attempts += 1
            log_message(screen, matrix, font_normal, text_color, f"No wifi #{internet_attempts}", display_time=2)
            if internet_attempts > 30:
                log_message(screen, matrix, font_normal, text_color, "No internet!")
                return
            time.sleep(3)

        log_message(screen, matrix, font_normal, text_color, "Internet OK!")
        
        # Perform the update
        success, repo_path = download_code(
            screen, matrix, font_normal, text_color,
            GITHUB_REPO_URL, REPO_DIR,
            expected_files=EXPECTED_FILES
        )
        
        # =================================================================
        # DISPLAY VERSION INFO - This is the key verification step!
        # =================================================================
        display_version_info(screen, matrix, font_normal, text_color, repo_path, success)
        
        clear_screen(screen, matrix)
        print("Update script completed")

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()