
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import os
import queue
import threading
import time
from automation_logic import run_automation

import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory session storage
# Structure: { session_id: { 'queue': Queue, 'stop_event': Event, 'thread': Thread } }
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_automation():
    uid = request.form.get('uid')
    password = request.form.get('password')
    doctor_name = request.form.get('doctor_name')
    file = request.files.get('file')

    if not uid or not password or not doctor_name or not file:
        return jsonify({'error': 'Missing fields'}), 400

    # Generate Session ID
    session_id = str(uuid.uuid4())
    
    # Unique filename to prevent overwrites
    filename = f"{session_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Initialize Session State
    session_queue = queue.Queue()
    session_stop_event = threading.Event()
    
    sessions[session_id] = {
        'queue': session_queue,
        'stop_event': session_stop_event
    }

    # Define session-specific callback
    def session_logger(message):
        print(f"[{session_id}] {message}")
        session_queue.put(message)

    # Run automation in a separate thread
    thread = threading.Thread(
        target=run_automation, 
        args=(filepath, uid, password, doctor_name, session_logger, session_stop_event)
    )
    sessions[session_id]['thread'] = thread
    thread.start()

    return jsonify({
        'status': 'Automation started', 
        'message': 'Check logs for progress.',
        'session_id': session_id
    })

@app.route('/stop', methods=['POST'])
def stop_automation():
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
        
    sessions[session_id]['stop_event'].set()
    return jsonify({'status': 'Stopping', 'message': 'Stop signal sent.'})

@app.route('/stream_logs')
def stream_logs():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404

    session_queue = sessions[session_id]['queue']

    def generate():
        while True:
            try:
                # Wait for log with a timeout
                message = session_queue.get(timeout=1)
                yield f"data: {message}\n\n"
            except queue.Empty:
                # Send a keep-alive comment
                yield ": keep-alive\n\n"
            except Exception as e:
                yield f"data: Error: {e}\n\n"
                break
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
