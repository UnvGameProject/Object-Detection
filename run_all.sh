#!/bin/bash

# Dynamically grab host IP for DISPLAY export
WINDOWS_HOST=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
export DISPLAY=${WINDOWS_HOST}:0
export LIBGL_ALWAYS_INDIRECT=1

echo "run_all"
# Optionally override DISPLAY manually:
export DISPLAY="10.0.0.219:0"
echo "Overriding DISPLAY manually..."
echo "DISPLAY: $DISPLAY"
echo "LIBGL_ALWAYS_INDIRECT: $LIBGL_ALWAYS_INDIRECT"

# Define the project root
PROJECT_DIR="$(pwd)"

echo "🌐 DISPLAY set to $DISPLAY"
echo "🚀 Starting backend server..."

# Activate venv
source venv/bin/activate

# Clean up any existing tmux session first
tmux has-session -t yolo_debug 2>/dev/null && tmux kill-session -t yolo_debug

# Launch tmux session which includes starting the backend
bash ./scripts/start_tmux.sh
