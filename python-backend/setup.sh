#!/bin/bash
# Whisper Large Model Setup Script

echo "🎙️ Whisper Large Model STT Server Kurulumu"
echo "=================================================="

# Python 3.8+ kontrolü
echo "📋 Python versiyonu kontrol ediliyor..."
python3 --version

# Virtual environment oluştur
echo "🔧 Virtual environment oluşturuluyor..."
python3 -m venv whisper_env

# Virtual environment'ı aktifleştir
echo "⚡ Virtual environment aktifleştiriliyor..."
source whisper_env/bin/activate

# FFmpeg kontrolü (Whisper için gerekli)
echo "🎵 FFmpeg kontrol ediliyor..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg bulunamadı. Yükleme talimatları:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    echo "   Windows: https://ffmpeg.org/download.html"
else
    echo "✅ FFmpeg mevcut"
fi

# Python paketlerini yükle
echo "📦 Python paketleri yükleniyor..."
pip install -r requirements.txt

echo ""
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "🚀 Sunucuyu başlatmak için:"
echo "   cd python-backend"
echo "   source whisper_env/bin/activate"
echo "   python whisper_server.py"
echo ""
echo "📍 Server URL: http://localhost:5001"
echo "🔍 Health Check: http://localhost:5001/health"
