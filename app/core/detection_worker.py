import time

def detection_worker(frame_queue, box_queue, model, stop_event, target_classes, max_boxes=5):
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
                    if class_id in target_classes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf)
                        timestamp = current_time
                        new_boxes.append((x1, y1, x2, y2, conf, class_id, timestamp))

            box_queue.put(new_boxes[:max_boxes])
        except Exception as e:
            print(f"Detection error: {e}")
