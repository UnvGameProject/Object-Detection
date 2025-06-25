#!/bin/bash
set -e

SESSION="yolo_debug"
PROJECT_DIR="$(pwd)"
IMAGE_NAME="test_frame.jpg"

mkdir -p logs

WINDOWS_HOST=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
export DISPLAY="${WINDOWS_HOST}:0"
export LIBGL_ALWAYS_INDIRECT=1

echo "start_tmux"
echo "windows_host: $WINDOWS_HOST"
echo "DISPLAY: $DISPLAY"
echo "LIBGL_ALWAYS_INDIRECT: $LIBGL_ALWAYS_INDIRECT"

# Manually override if needed
export DISPLAY="10.0.0.219:0"
echo "Overriding DISPLAY manually..."
echo "DISPLAY: $DISPLAY"
echo "LIBGL_ALWAYS_INDIRECT: $LIBGL_ALWAYS_INDIRECT"

# Kill session if exists
tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION

# Detector window (runs bootstrap/start.py)
tmux new-session -d -s $SESSION -n detector -c "$PROJECT_DIR"
tmux send-keys -t $SESSION:0 "
export DISPLAY=$DISPLAY && \
export LIBGL_ALWAYS_INDIRECT=$LIBGL_ALWAYS_INDIRECT && \
export PYTHONPATH=$PROJECT_DIR && \
source venv/bin/activate && \
python3 bootstrap/start.py 2>&1 | tee logs/start.log
" C-m

# Window 1: Activations
tmux new-window -t $SESSION:1 -n activations -c "$PROJECT_DIR"
tmux send-keys -t $SESSION:1 "
export DISPLAY=$DISPLAY && \
export LIBGL_ALWAYS_INDIRECT=$LIBGL_ALWAYS_INDIRECT && \
source venv/bin/activate && \
python3 scripts/show_activations.py ${IMAGE_NAME} 2>&1 | tee logs/activations.log
" C-m

# Window 2: Weights
tmux new-window -t $SESSION:2 -n weights -c "$PROJECT_DIR"
tmux send-keys -t $SESSION:2 "
export DISPLAY=$DISPLAY && \
export LIBGL_ALWAYS_INDIRECT=$LIBGL_ALWAYS_INDIRECT && \
source venv/bin/activate && \
python3 scripts/inspect_weights.py 2>&1 | tee logs/weights.log
" C-m

# Window 3: Loss Landscape
tmux new-window -t $SESSION:3 -n loss_landscape -c "$PROJECT_DIR"
tmux send-keys -t $SESSION:3 "
export DISPLAY=$DISPLAY && \
export LIBGL_ALWAYS_INDIRECT=$LIBGL_ALWAYS_INDIRECT && \
source venv/bin/activate && \
python3 scripts/loss_landscape.py 2>&1 | tee logs/loss.log
" C-m

tmux select-layout -t $SESSION tiled
tmux attach -t $SESSION
