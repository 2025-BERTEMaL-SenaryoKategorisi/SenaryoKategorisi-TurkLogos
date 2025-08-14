# TürkLogos Telecom Chatbot

Bu proje, yerel Whisper STT (Speech-to-Text) entegrasyonu ile geliştirilmiş bir telecom chatbot uygulamasıdır.

## 🚀 Özellikler

- **Ses Tanıma**: Yerel Whisper Large model ile offline STT
- **Metin Girişi**: Klasik yazılı sohbet desteği
- **Mock Cevaplar**: Geliştirme aşamasında sahte yanıtlar
- **TürkLogos Branding**: Özel takım logosu entegrasyonu
- **Responsive Design**: Mobil ve masaüstü uyumlu
- **Real-time Interface**: Anlık mesajlaşma deneyimi

## 🛠️ Teknolojiler

### Frontend
- React 18 + TypeScript
- Vite (development server)
- Tailwind CSS + shadcn/ui
- Lucide React (iconlar)

### Backend
- Python Flask
- OpenAI Whisper (local model)
- Flask-CORS

## 📦 Kurulum

### 1. Frontend Kurulumu
```bash
# Repository'yi klonlayın
git clone https://github.com/elifbasboga/voice-buddy-telco-update1.git
cd voice-buddy-telco-update1

# Bağımlılıkları yükleyin
npm install

# Development server'ı başlatın
npm run dev
```

Frontend http://localhost:8080 adresinde çalışacaktır.

### 2. Python Backend Kurulumu
```bash
# Python backend dizinine gidin
cd python-backend

# Virtual environment oluşturun
python3 -m venv whisper_env

# Virtual environment'ı aktifleştirin
# macOS/Linux:
source whisper_env/bin/activate
# Windows:
# whisper_env\Scripts\activate

# Gerekli paketleri yükleyin
pip install openai-whisper flask flask-cors

# Flask server'ı başlatın
python whisper_server.py
```

Backend http://localhost:5001 adresinde çalışacaktır.

## 🎯 Kullanım

1. **Frontend'i başlatın**: `npm run dev` (localhost:8081)
2. **Backend'i başlatın**: `python whisper_server.py` (localhost:5001)
3. **Web tarayıcısında** http://localhost:8081 adresini açın
4. **Ses girişi için** mikrofon butonuna basın (push-to-talk)
5. **Metin girişi için** alt kısımdaki input alanını kullanın

## 📝 Not

- Whisper model ilk çalıştırmada internet bağlantısı gerektirir (model indirme)
- Sonraki kullanımlarda tamamen offline çalışır
- Virtual environment (`whisper_env/`) Git'e dahil edilmemiştir
- Backend kurulumu her geliştirme ortamında tekrarlanmalıdır

## 🔧 Geliştirme

```bash
# Frontend geliştirme
npm run dev

# Python backend geliştirme
cd python-backend
source whisper_env/bin/activate
python whisper_server.py

# Build (production)
npm run build
```

## 📋 TODO

- [ ] Gerçek backend API entegrasyonu
- [ ] Kullanıcı authentication
- [ ] Chat geçmişi kaydetme
- [ ] Ses çıkışı (TTS) ekleme
- [ ] Docker containerization
