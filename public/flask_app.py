# public/flask_app.py

import os
import logging
from flask import Flask, Response, stream_with_context
from app.core.stream_generator import generate_stream
from app.core.memory_buffer import SharedFrameBuffer

LOG_FILE = os.path.join(os.path.dirname(__file__), '../logs/flask_app.log')

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure logger
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

def create_app(shared_buffer: SharedFrameBuffer, stop_event):
    app = Flask(__name__)

    @app.route('/')
    def video_feed():
        try:
            logging.info("🔌 Client connected to video feed.")
            return Response(
                stream_with_context(generate_stream(shared_buffer, stop_event)),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        except Exception as e:
            logging.exception("❌ Error in video_feed route")
            return "Internal Server Error", 500

    @app.route('/health')
    def health_check():
        return "✅ Flask server running", 200

    return app
