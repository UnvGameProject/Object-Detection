import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np
import time
import os
import tkinter

def plot_loss_landscape():
    print("⛰️ Loss landscape window running... Press Ctrl+C to close.")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    plt.ion()
    fig.show()

    try:
        while True:
            try:
                x = np.linspace(-2, 2, 100)
                y = np.linspace(-2, 2, 100)
                X, Y = np.meshgrid(x, y)
                Z = np.log(1 + X**2 + Y**2)

                ax.clear()
                ax.plot_surface(X, Y, Z, cmap='viridis')
                ax.set_title("Synthetic Saddle Loss Landscape")

                output_path = os.path.join(os.getcwd(), "loss_landscape.png")
                fig.savefig(output_path)
                print(f"✅ Saved loss landscape to {output_path}")

                fig.canvas.draw()
                fig.canvas.flush_events()
                time.sleep(5)
            except (tkinter.TclError, RuntimeError) as e:
                print(f"❌ Error in loss landscape loop: {e}")
                plt.close('all')
                return
    except KeyboardInterrupt:
        print("🛑 Loss landscape viewer closed.")

if __name__ == "__main__":
    plot_loss_landscape()
