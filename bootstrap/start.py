import sys
import os
import threading
import signal
import time
import queue
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from public.flask_app import create_app
from app.services.video_processor import video_processing
from app.core.memory_buffer import SharedFrameBuffer

stop_event = threading.Event()
shared_buffer = SharedFrameBuffer(name="frame_buffer", shape=(480, 640, 3), create=True)

throttle_queue = queue.Queue()

def signal_handler(sig, frame):
    print('🔌 Signal received, shutting down...')
    stop_event.set()
    time.sleep(1)
    shared_buffer.close()
    os.system('tmux kill-session -t yolo_debug')

def throttle_writer_thread(speed_file):
    while not stop_event.is_set():
        try:
            while not throttle_queue.empty():
                delay = throttle_queue.get_nowait()
                with open(speed_file, 'w') as f:
                    f.write(str(delay))
        except Exception as e:
            print(f"⚠️ Failed to write speed file: {e}")
            traceback.print_exc()
        time.sleep(1)

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start background threads for video and flask
        threading.Thread(target=video_processing, args=(shared_buffer, stop_event), daemon=True).start()

        app = create_app(shared_buffer, stop_event)
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True), daemon=True).start()

        # Start throttle writer thread
        speed_file = os.path.join(os.path.dirname(__file__), '../.throttle')
        threading.Thread(target=throttle_writer_thread, args=(speed_file,), daemon=True).start()

        # Run input loop in MAIN thread so prompt and input work correctly
        while not stop_event.is_set():
            try:
                print("⏳ Waiting for input in start.py main thread...")
                cmd = input("Press Enter to update visualizations or type 'exit' or 'speed [float]': ").strip().lower()
                print(f"✅ Input received: {cmd}")
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
            except Exception as e:
                print(f"⚠️ Exception in input loop: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Fatal error in start.py: {e}")
        traceback.print_exc()
    finally:
        try:
            os.remove(os.path.join(os.path.dirname(__file__), '../.throttle'))
        except FileNotFoundError:
            pass
        print("🧹 Exited cleanly.")
        sys.exit(0)
