#!/bin/bash
LOGFILE="/home/msolercanals/launcher.log"
echo "=== Launcher started at $(date) ===" >> $LOGFILE
cd /home/msolercanals/zuruckbleibenbitte
echo "Changed to directory: $(pwd)" >> $LOGFILE

# WiFi setup - ensure WiFi connection before running updates
echo "Running WiFi manager..." >> $LOGFILE
sudo python3 scripts/wifi_manager.py >> $LOGFILE 2>&1
echo "WiFi manager finished with exit code: $?" >> $LOGFILE
sleep 3

echo "Running update script..." >> $LOGFILE
sudo -u msolercanals python3 scripts/update_git.py
echo "Update script finished with exit code: $?" >> $LOGFILE
echo "Sleeping 5 seconds..." >> $LOGFILE
sleep 5
echo "Running main_train_display.py..." >> $LOGFILE
sudo python3 scripts/main_train_display.py 2>> $LOGFILE
EXIT_CODE=$?
echo "main_train_display.py finished with exit code: $EXIT_CODE" >> $LOGFILE