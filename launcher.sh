#!/bin/bash
LOGFILE="/home/msolercanals/launcher.log"
echo "=== Launcher started at $(date) ===" >> $LOGFILE
cd /home/msolercanals/zuruckbleibenbitte
echo "Changed to directory: $(pwd)" >> $LOGFILE
echo "Running update script..." >> $LOGFILE
sudo -u msolercanals python3 scripts/update_git.py
echo "Update script finished with exit code: $?" >> $LOGFILE
echo "Sleeping 5 seconds..." >> $LOGFILE
sleep 5
echo "Running messy_code_old.py..." >> $LOGFILE
sudo python3 scripts/messy_code_old.py 2>> $LOGFILE
EXIT_CODE=$?
echo "messy_code_old.py finished with exit code: $EXIT_CODE" >> $LOGFILE