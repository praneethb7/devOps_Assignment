#!/bin/bash
#
# sysinfo.sh - print a short report about this machine, then ask the user
# where to keep a full process listing and write it there.
#
# Usage:  ./sysinfo.sh      (press Enter at either prompt to take the default)

# ---- collect the facts into variables --------------------------------------
CURRENT_DATE=$(date)
HOST_NAME=$(hostname)
USER_NAME=$(whoami)
ROOT_DISK=$(df -h / | awk 'NR==2 {print $3 " of " $2 " used (" $5 ")"}')
PROC_COUNT=$(($(ps aux | wc -l) - 1))    # -1 drops the ps header row

# ---- print the summary -----------------------------------------------------
echo "===== System Information ====="
echo "Date       : $CURRENT_DATE"
echo "Hostname   : $HOST_NAME"
echo "User       : $USER_NAME"
echo "Root disk  : $ROOT_DISK"
echo "Processes  : $PROC_COUNT running"
echo

echo "===== Disk Usage (df -h) ====="
df -h
echo

echo "===== Running Processes (top 8 by CPU) ====="
ps aux --sort=-%cpu | head -9 | cut -c1-100
echo

# ---- ask where the report should go ----------------------------------------
read -p "Directory for the report [reports]: " REPORT_DIR
read -p "Report file name [processes.txt]: " REPORT_FILE

# an empty answer falls back to the default rather than breaking mkdir
REPORT_DIR=${REPORT_DIR:-reports}
REPORT_FILE=${REPORT_FILE:-processes.txt}
REPORT_PATH="$REPORT_DIR/$REPORT_FILE"

# ---- create the directory and the file -------------------------------------
if [ -d "$REPORT_DIR" ]; then
  echo "Directory '$REPORT_DIR' already exists - reusing it."
else
  mkdir -p "$REPORT_DIR"
  echo "Directory '$REPORT_DIR' created."
fi

# touch either creates the file or, if it is already there, just bumps its
# modification time - so say which one actually happened
if [ -e "$REPORT_PATH" ]; then
  touch "$REPORT_PATH"
  echo "File '$REPORT_PATH' already exists - timestamp updated."
else
  touch "$REPORT_PATH"
  echo "File '$REPORT_PATH' created."
fi

# ---- write the full process list into the file with > redirection ----------
ps aux > "$REPORT_PATH"

echo
echo "Wrote $(wc -l < "$REPORT_PATH") lines to $REPORT_PATH"
echo "First 5 lines of $REPORT_PATH:"
head -5 "$REPORT_PATH" | cut -c1-100
