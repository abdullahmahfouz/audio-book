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
stop_reading = False

def read_pdf_aloud(pdf_path, start_page=0):
    """Function to read PDF aloud in a separate thread"""
    global stop_reading
    stop_reading = False
    
    try:
        pdfreader = PyPDF2.PdfReader(pdf_path)
        pages = len(pdfreader.pages)
        
        # Initialize TTS engine with error handling
        try:
            speaker = pyttsx3.init()
            # Set properties for better compatibility
            voices = speaker.getProperty('voices')
            if voices:
                speaker.setProperty('voice', voices[0].id)
            speaker.setProperty('rate', 150)  # Speed of speech
        except Exception as tts_error:
            print(f"TTS initialization error: {tts_error}")
            return
        
        for num in range(start_page, pages):
            if stop_reading:
                break
                
            page = pdfreader.pages[num]
            text = page.extract_text()
            
            if text.strip():  # Only read if there's actual text
                try:
                    speaker.say(f"Page {num + 1}. {text}")
                    speaker.runAndWait()
                except Exception as speak_error:
                    print(f"Speech error on page {num + 1}: {speak_error}")
                    continue
                
        try:
            speaker.stop()
        except:
            pass  # Ignore stop errors
            
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
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            print(f"File saved to: {filepath}")
            
            # Verify file was saved
            if not os.path.exists(filepath):
                return jsonify({'error': 'Failed to save file'}), 500
            
            # Get start page from form
            start_page = int(request.form.get('start_page', 0))
            
            # Start reading in a separate thread
            global tts_thread
            tts_thread = threading.Thread(target=read_pdf_aloud, args=(filepath, start_page))
            tts_thread.start()
            
            return jsonify({'message': f'Started reading {filename} from page {start_page + 1}'}), 200
        
        return jsonify({'error': 'Please upload a valid PDF file'}), 400
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/stop', methods=['POST'])
def stop_reading():
    """Stop the current reading"""
    global stop_reading
    stop_reading = True
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
        # Test TTS engine
        import pyttsx3
        engine = pyttsx3.init()
        engine.stop()
        tts_status = "OK"
    except Exception as e:
        tts_status = f"Error: {str(e)}"
    
    return jsonify({
        'status': 'healthy',
        'tts_engine': tts_status,
        'flask': 'OK',
        'pdf_reader': 'OK'
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port)

