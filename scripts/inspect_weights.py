import matplotlib
matplotlib.use('TkAgg')

import torch
import matplotlib.pyplot as plt
import numpy as np
import time
import tkinter
from ultralytics import YOLO
import os

def load_throttle_delay(default=5.0):
    try:
        throttle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.throttle'))
        if os.path.exists(throttle_path):
            with open(throttle_path, 'r') as f:
                return float(f.read().strip())
    except Exception as e:
        print(f"⚠️ Failed to read throttle file: {e}")
    return default

def inspect_weights():
    print("📦 Weights viewer running... Press Ctrl+C to close.")
    model = YOLO('yolov8n.pt')  # Optional: make this a config var
    state_dict = model.model.state_dict()
    conv_weights = {k: v for k, v in state_dict.items() if "conv" in k and "weight" in k}

    fig = plt.figure(figsize=(16, 3))
    plt.ion()
    fig.show()

    try:
        while True:
            delay = load_throttle_delay()
            for name, weights in conv_weights.items():
                try:
                    weight_tensor = weights.detach().cpu().numpy()
                    if weight_tensor.ndim != 4:
                        continue

                    num_filters = min(weight_tensor.shape[0], 8)
                    input_channels = min(weight_tensor.shape[1], 1)

                    fig.clf()
                    for i in range(num_filters):
                        kernel = weight_tensor[i, 0] if input_channels > 0 else weight_tensor[i]
                        kernel -= kernel.min()
                        kernel /= kernel.max() + 1e-5

                        ax = fig.add_subplot(1, num_filters, i + 1)
                        ax.imshow(kernel, cmap='gray')
                        ax.axis('off')
                        ax.set_title(f'{name.split(".")[0]}\nF{i}')

                    fig.suptitle(f"Conv Weights - {name}")
                    fig.tight_layout()
                    fig.canvas.draw()
                    fig.canvas.flush_events()

                    time.sleep(delay)

                except (tkinter.TclError, RuntimeError) as e:
                    print(f"❌ Error in weights viewer loop: {e}")
                    plt.close('all')
                    return

    except KeyboardInterrupt:
        print("🛑 Weights viewer closed.")

if __name__ == "__main__":
    inspect_weights()
