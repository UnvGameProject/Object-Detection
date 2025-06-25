# app/core/memory_buffer.py

import numpy as np
import cv2
from multiprocessing import shared_memory, Lock

class SharedFrameBuffer:
    def __init__(self, name=None, shape=(480, 640, 3), create=False):
        self.name = name
        self.shape = shape
        self.dtype = np.uint8
        self.nbytes = int(np.prod(self.shape) * np.dtype(self.dtype).itemsize)
        self.lock = Lock()

        if create:
            try:
                self.shm = shared_memory.SharedMemory(create=True, size=self.nbytes, name=name)
            except FileExistsError:
                print(f"⚠️ Shared memory '{name}' exists. Attempting to unlink and recreate...")
                existing = shared_memory.SharedMemory(name=name)
                existing.close()
                existing.unlink()
                self.shm = shared_memory.SharedMemory(create=True, size=self.nbytes, name=name)
        else:
            self.shm = shared_memory.SharedMemory(name=name)

        self.buffer = np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)

    def write(self, frame):
        with self.lock:
            if frame.shape != self.shape:
                frame = cv2.resize(frame, (self.shape[1], self.shape[0]))
            np.copyto(self.buffer, frame)

    def read(self):
        with self.lock:
            return self.buffer.copy()

    def close(self):
        self.shm.close()
        try:
            self.shm.unlink()  # Only the creator should call this
        except FileNotFoundError:
            pass
