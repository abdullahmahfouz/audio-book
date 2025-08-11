from flask import Flask, request, render_template, jsonify
import pyttsx3
import PyPDF2
import os
import threading
from werkzeug.utils import secure_filename
import tempfile
import re
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# --- Global state ---
tts_thread = None
stop_flag = False
pause_flag = False
_engine = None
_engine_lock = threading.Lock()

# --- Engine setup (single fixed voice) ---
def get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            # On macOS specify 'nsss' driver for better quality; others auto-detect
            driver = 'nsss' if os.uname().sysname == 'Darwin' else None
            _engine = pyttsx3.init(driver)
            try:
                voices = _engine.getProperty('voices') or []
                # pick first English-ish voice
                def is_en(v):
                    meta = f"{getattr(v,'id','')} {getattr(v,'name','')} {getattr(v,'languages',[])}".lower()
                    return 'en' in meta
                chosen = next((v for v in voices if is_en(v)), voices[0] if voices else None)
                if chosen:
                    _engine.setProperty('voice', chosen.id)
                _engine.setProperty('rate', 165)
                _engine.setProperty('volume', 1.0)
            except Exception as e:
                print(f"Engine configuration error: {e}")
        return _engine

# --- Reading worker ---
def read_pdf_aloud(pdf_path, start_page=0):
    global stop_flag, pause_flag
    stop_flag = False
    pause_flag = False
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        pages = len(reader.pages)
        if start_page < 0 or start_page >= pages:
            print(f"Start page {start_page} out of range")
            return
        engine = get_engine()
        sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        for idx in range(start_page, pages):
            if stop_flag: break
            page = reader.pages[idx]
            try:
                raw_text = page.extract_text() or ''
            except Exception as ex:
                print(f"Page {idx+1} extraction error: {ex}")
                continue
            text = raw_text.strip()
            if not text:
                print(f"Page {idx+1} empty / non-extractable")
                continue
            # Split into sentences for responsive pause
            sentences = sentence_pattern.split(text)
            for s in sentences:
                if stop_flag: break
                # Handle pause (wait between sentences)
                while pause_flag and not stop_flag:
                    time.sleep(0.2)
                if not s.strip():
                    continue
                try:
                    engine.say(s.strip())
                    engine.runAndWait()  # blocking until sentence finished
                except Exception as speak_err:
                    print(f"Speech error: {speak_err}")
                    continue
    except Exception as e:
        print(f"Reader error: {e}")

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file field sent'}), 400
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return jsonify({'error': 'Saved file is empty or missing'}), 500
        raw_page = request.form.get('start_page', '0')
        try:
            start_page = int(raw_page)
        except ValueError:
            return jsonify({'error': 'start_page must be integer'}), 400
        if start_page < 0: start_page = 0
        global tts_thread
        if tts_thread and tts_thread.is_alive():
            return jsonify({'error': 'Reading already in progress'}), 409
        tts_thread = threading.Thread(target=read_pdf_aloud, args=(path, start_page), daemon=True)
        tts_thread.start()
        return jsonify({'message': f'Started reading {filename} from page {start_page + 1}'}), 200
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {e}'}), 500

@app.route('/pause', methods=['POST'])
def pause():
    global pause_flag
    pause_flag = True
    return jsonify({'message': 'Paused'}), 200

@app.route('/resume', methods=['POST'])
def resume():
    global pause_flag
    pause_flag = False
    return jsonify({'message': 'Resumed'}), 200

@app.route('/stop', methods=['POST'])
def stop_route():
    global stop_flag, pause_flag
    stop_flag = True
    pause_flag = False
    return jsonify({'message': 'Stopped'}), 200

@app.route('/status')
def status():
    global tts_thread, pause_flag
    is_running = tts_thread is not None and tts_thread.is_alive()
    return jsonify({'is_reading': is_running, 'paused': pause_flag})

@app.route('/health')
def health():
    try:
        _ = get_engine()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port)

