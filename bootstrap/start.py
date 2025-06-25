import sys
import os
import threading
import signal
import time
import queue

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from public.flask_app import create_app
from app.services.video_processor import video_processing
from app.core.memory_buffer import SharedFrameBuffer

stop_event = threading.Event()
shared_buffer = SharedFrameBuffer(name="frame_buffer", shape=(480, 640, 3), create=True)

# Throttle queue: used to send speed updates to the activation viewer
throttle_queue = queue.Queue()

def signal_handler(sig, frame):
    print('🔌 Signal received, shutting down...')
    stop_event.set()
    time.sleep(1)
    shared_buffer.close()
    os.system('tmux kill-session -t yolo_debug')

def input_loop():
    while not stop_event.is_set():
        try:
            cmd = input("Press Enter to update visualizations or type 'exit' or 'speed [float]': ").strip().lower()
            if cmd == 'exit':
                stop_event.set()
                break
            elif cmd.startswith('speed '):
                try:
                    delay = float(cmd.split()[1])
                    throttle_queue.put(delay)
                    print(f"⏱️ Update speed set to {delay} seconds.")
                except ValueError:
                    print("⚠️ Invalid speed value. Use: speed 2.5")
            else:
                print("🔄 Triggered update (handled by each script's internal loop).")
        except EOFError:
            break

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Launch threads
        threading.Thread(target=input_loop, daemon=True).start()
        threading.Thread(target=video_processing, args=(shared_buffer, stop_event), daemon=True).start()

        app = create_app(shared_buffer, stop_event)
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True), daemon=True).start()

        # Pass updates to disk for the activations process to read
        speed_file = os.path.join(os.path.dirname(__file__), '../.throttle')
        while not stop_event.is_set():
            try:
                while not throttle_queue.empty():
                    delay = throttle_queue.get_nowait()
                    with open(speed_file, 'w') as f:
                        f.write(str(delay))
            except Exception as e:
                print(f"⚠️ Failed to write speed file: {e}")
            time.sleep(1)

    except Exception as e:
        print(f"❌ Fatal error in start.py: {e}")
    finally:
        try:
            os.remove(os.path.join(os.path.dirname(__file__), '../.throttle'))
        except FileNotFoundError:
            pass
        print("🧹 Exited cleanly.")
        sys.exit(0)
