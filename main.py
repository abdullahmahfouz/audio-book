from flask import Flask, request, render_template, jsonify, redirect, url_for
import pyttsx3
import PyPDF2
import os
import threading
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Global variables for TTS control
tts_thread = None
stop_flag = False  # renamed to avoid name clash with route function
_engine = None
_engine_lock = threading.Lock()
current_voice_id = None  # user selected voice

# Helper to determine if voice is English
def _is_english_voice(v):
    try:
        # languages may be like [b'\x05en_US']
        langs = getattr(v, 'languages', []) or []
        for l in langs:
            if isinstance(l, (bytes, bytearray)):
                l = l.decode(errors='ignore')
            if 'en' in l.lower():
                return True
        # fallback: inspect id / name
        meta = f"{getattr(v,'id','')} {getattr(v,'name','')}".lower()
        return any(tag in meta for tag in ['en_', 'english', 'en-us', 'en-gb', 'us_', 'gb_'])
    except Exception:
        return False


def get_engine():
    """Lazily initialize and return a shared pyttsx3 engine (single thread usage)."""
    global _engine, current_voice_id
    with _engine_lock:
        if _engine is None:
            _engine = pyttsx3.init('nsss' if os.uname().sysname == 'Darwin' else None)
        try:
            voices = _engine.getProperty('voices') or []
            english_voices = [v for v in voices if _is_english_voice(v)] or voices
            selected = None
            if current_voice_id:
                for v in english_voices:
                    if v.id == current_voice_id:
                        selected = v
                        break
            if not selected and english_voices:
                selected = english_voices[0]
            if selected:
                _engine.setProperty('voice', selected.id)
            _engine.setProperty('rate', 165)
            _engine.setProperty('volume', 1.0)
        except Exception as e:
            print(f"Engine config error: {e}")
        return _engine


def read_pdf_aloud(pdf_path, start_page=0):
    """Function to read PDF aloud in a separate thread"""
    global stop_flag
    stop_flag = False

    try:
        pdfreader = PyPDF2.PdfReader(pdf_path)
        pages = len(pdfreader.pages)

        if start_page < 0 or start_page >= pages:
            print(f"Start page {start_page} out of range (0..{pages-1})")
            return

        speaker = get_engine()

        for num in range(start_page, pages):
            if stop_flag:
                break

            page = pdfreader.pages[num]
            try:
                text = page.extract_text() or ''
            except Exception as ext_err:
                print(f"Page {num+1} extract error: {ext_err}")
                continue

            cleaned = text.strip()
            if cleaned:
                try:
                    speaker.say(f"Page {num + 1}. {cleaned}")
                    speaker.runAndWait()
                except Exception as speak_error:
                    print(f"Speech error on page {num + 1}: {speak_error}")
                    continue
            else:
                print(f"Page {num+1} has no extractable text (might be scanned image).")

    except Exception as e:
        print(f"Error reading PDF: {e}")


@app.route('/')
def index():
    """Main page with file upload form"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file field sent'}), 400
        # Voice selection (optional)
        global current_voice_id
        vid = request.form.get('voice_id')
        if vid:
            current_voice_id = vid  # store for subsequent speech

        file = request.files['file']

        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved to: {filepath}")

        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return jsonify({'error': 'Saved file is empty or missing'}), 500

        # start_page validation
        raw_page = request.form.get('start_page', '0')
        try:
            start_page = int(raw_page)
        except ValueError:
            return jsonify({'error': 'start_page must be an integer'}), 400
        if start_page < 0:
            start_page = 0

        global tts_thread
        if tts_thread and tts_thread.is_alive():
            return jsonify({'error': 'A reading is already in progress'}), 409
        tts_thread = threading.Thread(target=read_pdf_aloud, args=(filepath, start_page), daemon=True)
        tts_thread.start()

        return jsonify({'message': f'Started reading {filename} from page {start_page + 1}', 'voice': current_voice_id}), 200
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/stop', methods=['POST'])
def stop_route():  # renamed
    """Stop the current reading"""
    global stop_flag
    stop_flag = True
    return jsonify({'message': 'Stopped reading'}), 200


@app.route('/status')
def status():
    """Check if TTS is currently running"""
    global tts_thread
    is_running = tts_thread is not None and tts_thread.is_alive()
    return jsonify({'is_reading': is_running})


@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    try:
        engine = get_engine()
        tts_status = "OK" if engine else "Unavailable"
    except Exception as e:
        tts_status = f"Error: {str(e)}"

    return jsonify({
        'status': 'healthy',
        'tts_engine': tts_status,
        'flask': 'OK',
        'pdf_reader': 'OK'
    })


@app.route('/voices')
def list_voices():
    """Return available English voices only."""
    try:
        engine = get_engine()
        voices = engine.getProperty('voices') or []
        english_voices = [v for v in voices if _is_english_voice(v)]
        out = []
        for v in english_voices:
            label = getattr(v, 'name', None) or v.id.split('.')[-1]
            out.append({
                'id': v.id,
                'name': label,
                'languages': [ (l.decode() if isinstance(l,(bytes,bytearray)) else l) for l in getattr(v,'languages', []) ],
                'gender': getattr(v, 'gender', ''),
            })
        # If previously selected voice not in English list, reset
        global current_voice_id
        if current_voice_id and current_voice_id not in {v['id'] for v in out}:
            current_voice_id = out[0]['id'] if out else None
        return jsonify({'voices': out, 'current': current_voice_id})
    except Exception as e:
        return jsonify({'error': f'Voice enumeration failed: {e}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port)

