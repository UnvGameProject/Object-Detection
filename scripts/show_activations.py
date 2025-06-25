import sys
import os
import matplotlib
matplotlib.use('TkAgg')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO
import cv2
import time
import tkinter
import traceback
import matplotlib.patches as patches
from app.core.memory_buffer import SharedFrameBuffer

def get_activations(model, input_tensor, layer_names=None):
    activations = {}
    def hook_fn(module, input, output):
        layer_name = module._get_name()
        if (layer_names is None) or (layer_name in layer_names):
            activations[layer_name] = output.detach().cpu().numpy()

    hooks = []
    for name, module in model.model.named_modules():
        if layer_names is None or module.__class__.__name__ in layer_names:
            hooks.append(module.register_forward_hook(hook_fn))

    model.eval()
    with torch.no_grad():
        model(input_tensor)

    for h in hooks:
        h.remove()
    return activations

def load_throttle_delay(default=5.0):
    try:
        throttle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.throttle'))
        if os.path.exists(throttle_path):
            with open(throttle_path, 'r') as f:
                return float(f.read().strip())
    except Exception as e:
        print(f"⚠️ Failed to read throttle file: {e}")
        traceback.print_exc()
    return default

def visualize_activations(activations, max_channels=8, fig=None, delay=5.0):
    try:
        for layer_name, activation in activations.items():
            batch_act = activation[0]
            if batch_act.ndim != 3:
                continue

            num_channels = min(batch_act.shape[0], max_channels)

            # Flash green overlay at start of update WITHOUT clearing figure immediately
            ax_flash = fig.add_subplot(111)
            rect = patches.Rectangle((0, 0), 1, 1, transform=ax_flash.transAxes,
                                     linewidth=0, edgecolor=None,
                                     facecolor='lime', alpha=0.5)
            ax_flash.add_patch(rect)
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(0.15)  # brief flash pause
            rect.remove()  # remove the flash overlay patch
            fig.canvas.draw()
            fig.canvas.flush_events()

            fig.clf()  # Clear figure after flash is removed

            for i in range(num_channels):
                ax = fig.add_subplot(1, num_channels, i + 1)
                channel_img = batch_act[i]
                channel_img = (channel_img - channel_img.min()) / (channel_img.max() - channel_img.min() + 1e-5)
                ax.imshow(channel_img, cmap='viridis')
                ax.axis('off')
                ax.set_title(f'Ch {i}')

            fig.suptitle(f'Layer: {layer_name}')
            fig.tight_layout()
            fig.canvas.draw()
            fig.canvas.flush_events()

            time.sleep(delay)
    except (tkinter.TclError, RuntimeError) as e:
        print(f"❌ Error in activations loop: {e}")
        traceback.print_exc()
        plt.close('all')
        raise SystemExit()

def main_loop():
    model = YOLO('yolov8n.pt')
    shared_buffer = SharedFrameBuffer(name="frame_buffer", shape=(480, 640, 3), create=False)

    print("🎯 Activations viewer running... Press Ctrl+C to stop.")
    fig = plt.figure(figsize=(16, 3))
    plt.ion()
    fig.show()

    while True:
        delay = load_throttle_delay()
        frame = shared_buffer.read()
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (640, 640))
        input_tensor = torch.from_numpy(img_resized).permute(2, 0, 1).unsqueeze(0).float() / 255.0

        layers_to_hook = ['Conv', 'Conv2d']
        activations = get_activations(model, input_tensor, layer_names=layers_to_hook)
        visualize_activations(activations, max_channels=8, fig=fig, delay=delay)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("🛑 Activations viewer closed.")
    except Exception as e:
        print(f"❌ Fatal error in activations viewer: {e}")
        traceback.print_exc()
