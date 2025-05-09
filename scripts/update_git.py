import os
import subprocess
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
import socket
import shutil
import datetime

# Function to log messages with timestamp to both LED screen and log file
def log_message(screen, matrix, font, text_color, message, log_file_path="log_timestamp.txt", display_time=5):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}: {message}"

        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry + "\n")

        screen.Clear()
        graphics.DrawText(screen, font, 3, 14, text_color, message[:30])  # Truncate to avoid overflow
        matrix.SwapOnVSync(screen)
        time.sleep(display_time)
    except Exception as e:
        print(f"Logging/display error: {e}")


def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False


def clear_screen(screen, matrix):
    try:
        screen.Clear()
        matrix.SwapOnVSync(screen)
    except Exception as e:
        log_message(screen, matrix, font_normal, textColor, f"Screen clear err: {str(e)[:20]}")


def verify_repository(repo_path, expected_files=None):
    try:
        if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
            return False

        if not os.path.exists(os.path.join(repo_path, '.git')):
            return False

        if expected_files:
            for file in expected_files:
                if not os.path.exists(os.path.join(repo_path, file)):
                    return False
        else:
            files = os.listdir(repo_path)
            if len(files) <= 1:
                return False

        return True
    except Exception as e:
        log_message(first_screen, matrix, font_normal, textColor, f"Verify err: {str(e)[:20]}")
        return False


def download_code(repo_url, clone_dir, max_retries=10, expected_files=None):
    repo_name = repo_url.split("/")[-1].replace('.git', "")
    repo_path = os.path.join(clone_dir, repo_name)

    for attempt in range(1, max_retries + 1):
        try:
            log_message(first_screen, matrix, font_normal, textColor, f"Attempt {attempt} to get code")

            if not os.path.exists(repo_path):
                result = subprocess.run(['git', 'clone', repo_url, repo_path], check=True, capture_output=True)
            else:
                subprocess.run(['git', '-C', repo_path, 'fetch', '--all'], check=True, capture_output=True)
                subprocess.run(['git', '-C', repo_path, 'reset', '--hard', 'origin/main'], check=True, capture_output=True)

            if verify_repository(repo_path, expected_files):
                log_message(first_screen, matrix, font_normal, textColor, "Repo verified")
                return True, repo_path
            else:
                log_message(first_screen, matrix, font_normal, textColor, f"Verify failed #{attempt}")
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
        except subprocess.CalledProcessError as e:
            log_message(first_screen, matrix, font_normal, textColor, f"Git err #{attempt}: {e.stderr.decode()[:30]}")
            time.sleep(5)
        except Exception as e:
            log_message(first_screen, matrix, font_normal, textColor, f"Err #{attempt}: {str(e)[:30]}")
            time.sleep(5)

    return False, repo_path


def update_code(first_screen, matrix, font_normal, textColor):
    try:
        log_message(first_screen, matrix, font_normal, textColor, 'Starting update')

        GITHUB_REPO_URL = 'https://github.com/msolercanalsgit/zuruckbleibenbitte.git'
        CLONE_DIR = os.getcwd()
        expected_files = ['test_file.py']

        success, repo_path = download_code(GITHUB_REPO_URL, CLONE_DIR, expected_files=expected_files)

        if success:
            log_message(first_screen, matrix, font_normal, textColor, f"Updated: {repo_path.split('/')[-1]}")
        else:
            log_message(first_screen, matrix, font_normal, textColor, 'Update failed!')
    except Exception as e:
        log_message(first_screen, matrix, font_normal, textColor, f'Update exc: {str(e)[:30]}')

    clear_screen(first_screen, matrix)


try:
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 192
    options.brightness = 100
    options.gpio_slowdown = 5
    options.disable_hardware_pulsing = 1
    options.hardware_mapping = 'adafruit-hat'
    options.pwm_lsb_nanoseconds = 100

    matrix = RGBMatrix(options=options)
    first_screen = matrix.CreateFrameCanvas()

    font_normal = graphics.Font()
    font_normal.LoadFont("fonts/bfvlowermargen.bdf")
    textColor = graphics.Color(255, 1, 200)

    log_message(first_screen, matrix, font_normal, textColor, 'Starting script')

    while not check_internet():
        log_message(first_screen, matrix, font_normal, textColor, "No internet. Retry...")
        time.sleep(5)

    log_message(first_screen, matrix, font_normal, textColor, "Internet OK")
    update_code(first_screen, matrix, font_normal, textColor)
    log_message(first_screen, matrix, font_normal, textColor, "Done.")
    clear_screen(first_screen, matrix)

except Exception as main_e:
    try:
        log_message(first_screen, matrix, font_normal, textColor, f"Fatal error: {str(main_e)[:30]}")
    except:
        print(f"Fatal error (no LED): {main_e}")
