import cv2
from ultralytics import YOLO
import time
import datetime
import threading
from queue import Queue
from flask import Flask, Response
import signal
import sys

app = Flask(__name__)
output_frame = None
lock = threading.Lock()

TARGET_CLASSES = {
    0: "person",
    46: "banana",
    64: "mouse",
    67: "cell phone"
}

stop_event = threading.Event()

def detection_worker(frame_queue, box_queue, model, max_boxes=5):
    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=0.5)
        except:
            continue
        if frame is None:
            break

        try:
            results = model(frame, verbose=False)
            current_time = time.time()
            new_boxes = []

            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls)
                    if class_id in TARGET_CLASSES:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf)
                        timestamp = current_time
                        new_boxes.append((x1, y1, x2, y2, conf, class_id, timestamp))

            box_queue.put(new_boxes[:max_boxes])
        except Exception as e:
            print(f"Detection error: {e}")

def video_processing():
    global output_frame
    model = YOLO('yolov8n.pt')
    cap = cv2.VideoCapture("http://10.0.0.219:8080/video")
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_queue = Queue(maxsize=1)
    box_queue = Queue()
    last_boxes = []

    threading.Thread(
        target=detection_worker,
        args=(frame_queue, box_queue, model),
        daemon=True
    ).start()

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed")
            time.sleep(0.1)
            continue

        if frame_queue.empty():
            frame_queue.put(frame.copy())

        while not box_queue.empty():
            last_boxes = box_queue.get()

        # Draw detections
        current_time = time.time()
        for (x1, y1, x2, y2, conf, class_id, timestamp) in last_boxes:
            is_fresh = current_time - timestamp < 0.2
            color = (0, 255, 0) if is_fresh else (128, 128, 128)
            label = f"{TARGET_CLASSES[class_id]}: {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        with lock:
            output_frame = frame.copy()

    cap.release()

def generate_stream():
    global output_frame
    while not stop_event.is_set():
        with lock:
            if output_frame is None:
                continue
            success, buffer = cv2.imencode('.jpg', output_frame)
            if not success:
                continue
            frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)

def signal_handler(sig, frame):
    print('Signal received, shutting down...')
    stop_event.set()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination

    video_thread = threading.Thread(target=video_processing, daemon=True)
    flask_thread = threading.Thread(target=run_flask, daemon=True)

    video_thread.start()
    flask_thread.start()

    try:
        # Block here waiting for stop_event to be set
        while not stop_event.is_set():
            time.sleep(0.1)

        # Once stop_event set, wait max 3 seconds for threads to exit cleanly
        start_wait = time.time()
        while video_thread.is_alive() or flask_thread.is_alive():
            if time.time() - start_wait > 3:
                print("Force exit after timeout.")
                sys.exit(0)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, exiting.")
        stop_event.set()

    print("Exited cleanly.")
    sys.exit(0)
