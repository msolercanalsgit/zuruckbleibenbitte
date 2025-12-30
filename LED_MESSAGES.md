# LED Screen Messages During Boot

This document shows what messages will appear on the LED screen during the boot sequence.

## WiFi Manager Messages

### Scenario 1: Already Connected to WiFi
```
WiFi Manager...      (1 second)
Checking WiFi...     (1 second)
WiFi OK: [network]   (2 seconds)
[screen clears]
```

### Scenario 2: Connecting to Saved Network
```
WiFi Manager...          (1 second)
Checking WiFi...         (1 second)
Trying 1 network(s)...   (1 second)
Connecting to [name]...  (1 second)
Verifying...             (3 seconds)
Connected to [name]      (2 seconds)
[screen clears]
```

### Scenario 3: No WiFi - Setup Mode
```
WiFi Manager...              (1 second)
Checking WiFi...             (1 second)
Starting setup mode...       (1 second)
SETUP MODE                   (3 seconds)
WiFi: TrainDisplay-Setup     (3 seconds)
Pass: trainsetup123          (3 seconds)
Go to 192.168.4.1            (3 seconds)
Waiting for setup...         (2 seconds)
[screen clears]
```

### Scenario 4: Connection Failed - Fallback to Setup
```
WiFi Manager...              (1 second)
Checking WiFi...             (1 second)
Trying 2 network(s)...       (1 second)
Connecting to Home...        (1 second)
Verifying...                 (3 seconds)
Connecting to Office...      (1 second)
Verifying...                 (3 seconds)
Starting setup mode...       (1 second)
SETUP MODE                   (3 seconds)
WiFi: TrainDisplay-Setup     (3 seconds)
Pass: trainsetup123          (3 seconds)
Go to 192.168.4.1            (3 seconds)
Waiting for setup...         (2 seconds)
[screen clears]
```

## Update Script Messages (after WiFi)

After WiFi manager completes, `update_git.py` runs and shows:

```
Starting...              (3 seconds)
No wifi #1               (2 seconds - if no internet)
Internet OK!             (3 seconds)
Update 1/5...            (3 seconds)
Fetching...              (1 second)
Resetting...             (1 second)
Updated: [commit hash]   (8 seconds)
Date: [commit date]      (shown above)
[screen clears]
```

## Train Display Messages (normal operation)

After updates complete, the train display shows:

```
[Train line] [Destination]     [Time]
[Train line] [Destination]     [Time]
```

Example:
```
U1 Warschauer Str.        in 12 min
U1 Uhlandstraße           in 18 min
```

Or if no connection:
```
Connecting to Wifi. Wait 60 sec.
```

## Timeline Example (Fresh Boot, No WiFi)

Total time from boot to setup mode display: ~17 seconds

```
00:00 - WiFi Manager...
00:01 - Checking WiFi...
00:02 - Starting setup mode...
00:03 - SETUP MODE
00:06 - WiFi: TrainDisplay-Setup
00:09 - Pass: trainsetup123
00:12 - Go to 192.168.4.1
00:15 - Waiting for setup...
00:17 - [Screen clears, config server is ready]
```

## Color and Font

- **Color**: Purple/Magenta (`RGB(255, 1, 200)`)
- **Font**: `bfvlowermargen.bdf`
- **Position**: Line 1, starting at pixel 3
- **Max characters**: 30 characters (text is truncated if longer)

## Notes

- All messages print to both the LED screen AND the log file
- If LED matrix initialization fails (e.g., not running as root), messages only go to logs
- Screen is cleared before transitioning to the next script
- Messages use same styling as the git updater for consistency
