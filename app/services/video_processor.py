# app/services/video_processor.py
import cv2
import threading
import time
from queue import Queue
from ultralytics import YOLO
from app.core.detection_worker import detection_worker
from config.yolo_config import MODEL_PATH, VIDEO_SOURCE, TARGET_CLASSES
from app.core.memory_buffer import SharedFrameBuffer

def video_processing(shared_buffer: SharedFrameBuffer, stop_event):
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_queue = Queue(maxsize=1)
    box_queue = Queue()
    last_boxes = []

    threading.Thread(
        target=detection_worker,
        args=(frame_queue, box_queue, model, stop_event, TARGET_CLASSES),
        daemon=True
    ).start()

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed")
            time.sleep(0.05)
            continue

        # Push frame to detection queue if available
        if frame_queue.empty():
            frame_queue.put(frame.copy())

        # Retrieve latest detection results
        while not box_queue.empty():
            last_boxes = box_queue.get()

        current_time = time.time()
        for (x1, y1, x2, y2, conf, class_id, timestamp) in last_boxes:
            is_fresh = current_time - timestamp < 0.3
            color = (0, 255, 0) if is_fresh else (128, 128, 128)
            label = f"{TARGET_CLASSES[class_id]}: {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Write frame to shared memory
        shared_buffer.write(frame)

    cap.release()
