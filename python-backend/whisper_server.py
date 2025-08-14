#!/usr/bin/env python3
"""
Yerel Whisper STT Server
Flask tabanlı API server
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import tempfile
import os
import logging

# Flask app setup
app = Flask(__name__)
CORS(app) 

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whisper model yükleme
logger.info("Whisper Large model yükleniyor...")
model = whisper.load_model("large")
logger.info("Whisper Large model başarıyla yüklendi!")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'whisper-large',
        'version': '1.0.0'
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Ses dosyasını transkript eden endpoint
    """
    try:
        # Dosya kontrolü
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400

        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_filename = temp_file.name

        try:
            # Whisper ile transkript
            logger.info(f"Ses dosyası işleniyor: {temp_filename}")
            result = model.transcribe(
                temp_filename,
                language='tr',
                fp16=False,     # CPU uyumluluğu için
                verbose=False   # Log kirliliğini azalt
            )
            
            transcript = result['text'].strip()
            
            logger.info(f"Transkript tamamlandı: '{transcript[:50]}...'")
            
            return jsonify({
                'transcript': transcript,
                'language': result.get('language', 'tr')
            })
            
        finally:
            # Geçici dosyayı temizle
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
                
    except Exception as e:
        logger.error(f"Transkript hatası: {str(e)}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

@app.route('/models', methods=['GET'])
def get_models():
    """Kullanılabilir model bilgisi"""
    return jsonify({
        'current_model': 'large',
        'model_info': {
            'name': 'whisper-large',
            'size': '~1.5GB',
            'languages': ['tr', 'en', 'auto'],
            'accuracy': 'very good'
        }
    })

if __name__ == '__main__':
    print("🎙️  Whisper STT Server başlatılıyor...")
    print("📍 Health Check: http://localhost:5001/health")
    print("🔊 Transcribe API: http://localhost:5001/transcribe")
    print("📋 Models Info: http://localhost:5001/models")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )