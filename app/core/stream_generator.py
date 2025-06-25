# app/core/stream_generator.py

import cv2
import time
import logging

logger = logging.getLogger(__name__)

def generate_stream(shared_buffer, stop_event):
    last_sent = 0
    send_interval = 1.0 / 10  # 10 FPS

    while not stop_event.is_set():
        now = time.time()
        if now - last_sent < send_interval:
            time.sleep(0.005)
            continue

        try:
            frame = shared_buffer.read()
            if frame is None:
                logger.warning("⚠️ No frame in shared buffer.")
                time.sleep(0.01)
                continue

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                logger.error("❌ Failed to encode frame as JPEG.")
                continue

            last_sent = now
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            logger.exception("🔥 Exception in generate_stream()")
            break
