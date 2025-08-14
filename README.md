# TürkLogos Telecom AI Agent - TEKNOFEST 2025

<p align="center">
  <img src="./images/logo.png" alt="TürkLogos Logo"/>
</p>

**#BilisimVadisi2025** | **Ekip: BERTeMaL** | **@AcikKaynakPlatformu**

Bu proje, TEKNOFEST 2025 **#BilisimVadisi2025** etkinliği kapsamında geliştirilmiş, otonom telecom müşteri hizmetleri ajanı sistemidir. **Apache License 2.0** ile lisanslanmış açık kaynaklı bir projedir.

## 👥 Ekip Bilgisi

| Fotoğraf | İsim | Ünvan | Sosyal Medya |
|---|---|---|---|
| <img src="./images/emre_satir.jpeg" width="100"/> | Emre ŞATIR | Danışman |  |
| <img src="./images/erdem_malkan.jpeg" width="100"/> | Erdem Altuğ MALKAN | Takım Kaptanı | [GitHub](https://github.com/altugmalkan) <br> [LinkedIn](https://www.linkedin.com/in/altuğ-malkan-80b8a4284/) |
| <img src="./images/dilan_basboga.jpeg" width="100"/> | Dilan Elif BAŞBOĞA | Takım Üyesi | [GitHub](https://github.com/elifbasboga) <br> [LinkedIn](https://www.linkedin.com/in/dilan-elif-başboğa-573091276/) |
| <img src="./images/ahmet_ucan.jpeg" width="100"/> | Ahmet Anıl UÇAN | Takım Üyesi | [GitHub](https://github.com/Anilf8) <br> [LinkedIn](https://www.linkedin.com/in/anıl-uçan-785336331/) |


## 🚀 Proje Genel Bakış

TürkLogos Telecom AI Agent, telecom operatörlerinin müşteri hizmetlerini otomatikleştirmek için geliştirilmiş kapsamlı bir yapay zeka sistemidir. Proje, LangChain ve modern AI teknolojileri kullanarak akıllı müşteri destek ajanı sunar.

### 🎯 Ana Özellikler

- **🤖 Otonom AI Agent**: LangChain tabanlı akıllı müşteri hizmetleri ajanı
- **🎤 Ses Tanıma**: OpenAI Whisper ile Türkçe STT (Speech-to-Text)
- **💬 Çok Kanallı İletişim**: Ses ve metin tabanlı etkileşim
- **📊 Gerçek Zamanlı Analytics**: Performans izleme ve raporlama
- **🔐 Güvenli Kimlik Doğrulama**: JWT tabanlı güvenlik sistemi
- **📱 Modern Frontend**: React TypeScript ile responsive arayüz
- **🐳 Containerized**: Docker ile kolay dağıtım

## 🏗️ Sistem Mimarisi

<p align="center">
  <img src="./images/architecture.jpeg" alt="Sistem Mimarisi" width="400"/>
</p>

## 🤖 AI Agent Özellikleri

### **LangChain Tabanlı Ajan**
- **ReAct Pattern**: Reasoning + Acting yaklaşımı
- **Tool Usage**: Dinamik araç kullanımı
- **Memory Management**: Konuşma geçmişi yönetimi
- **Context Awareness**: Bağlam farkındalığı

### **Desteklenen Senaryolar**
- **👤 Müşteri Kimlik Doğrulama**: Telefon numarası ve kişisel bilgi kontrolü
- **📞 Fatura Sorgulama**: Güncel ve geçmiş fatura bilgileri
- **📦 Paket Yönetimi**: Tarife değişiklikleri ve öneriler
- **🔧 Teknik Destek**: Sorun bildirimi ve teknisyen randevusu
- **❓ Genel Bilgilendirme**: Ürün ve hizmet bilgileri

### **AI Tools & Capabilities**
```python
# Kullanılabilir Araçlar
- authenticate_customer()     # Müşteri doğrulama
- get_customer_bills()       # Fatura sorgulama
- get_available_packages()   # Paket listesi
- create_support_ticket()    # Destek talebi
- schedule_technician()      # Teknisyen randevusu
- get_customer_info()        # Müşteri bilgileri
```

## 🛠️ Teknoloji Stack

### **Backend (AI Agent)**
- **FastAPI**: Modern Python web framework
- **LangChain + LangGraph**: AI agent ve LLM orchestration
- **Ollama**: Local LLM inference ve model yönetimi
- **SQLAlchemy**: ORM ve database yönetimi
- **PostgreSQL**: Ana veritabanı (Port: 5433)
- **Redis**: Cache ve session yönetimi
- **WebSockets**: Real-time communication

### **Frontend (Voice Interface)**
- **React 18 + TypeScript**: Modern UI framework
- **Vite**: Development ve build tool
- **OpenAI Whisper**: Speech-to-Text model
- **Tailwind CSS + shadcn/ui**: Styling framework
- **React Query**: State management

### **DevOps & Infrastructure**
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration (PostgreSQL, Redis, Ollama, API, Frontend)
- **Nginx**: Reverse proxy
- **Prometheus**: Monitoring (planned)
- **WebSockets**: Real-time communication


## 🚀 Kurulum ve Çalıştırma

### **Ön Gereksinimler**
```bash
# Sistem gereksinimleri
- Docker & Docker Compose
- Python 3.9+ (manuel kurulum için)
- Node.js 18+ (frontend için)
- Git
```

### **Hızlı Başlangıç (Docker)**
```bash
# 1. Projeyi klonlayın
git clone https://github.com/2025-BERTEMaL-SenaryoKategorisi/SenaryoKategorisi-TurkLogos.git
cd SenaryoKategorisi-TurkLogos

# 2. AI Agent sistemini başlatın
cd SenaryoKategorisi-TurkLogos-demo-altug
docker-compose up -d

# 3. Voice Interface'i başlatın (ayrı terminal)
cd ../demo-elif-frontend
docker build -t turklogos-frontend .
docker run -p 8081:80 turklogos-frontend

# 4. Uygulamalara erişin
# AI Agent API: http://localhost:8000
# Voice Interface: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Database: PostgreSQL on port 5433
# Redis: port 6379
# Ollama: port 11434
```

### **Manuel Kurulum**

#### **AI Agent Backend:**
```bash
cd SenaryoKategorisi-TurkLogos-demo-altug

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Dependencies
pip install -r requirements.txt

# Environment
cp env.example .env
# .env dosyasını düzenleyin

# Database (PostgreSQL otomatik Docker ile başlar)
# Port 5433'te çalışır

# Start agent
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Voice Interface:**
```bash
# Docker ile otomatik çalışır (port 3000)
# Manuel için:
cd demo-elif-frontend

# Backend (Whisper STT)
cd python-backend
python -m venv whisper_env
source whisper_env/bin/activate
pip install -r requirements.txt
python whisper_server.py  # Port 5001

# Frontend (ayrı terminal)
cd ..
npm install
npm run dev  # Port 8081
```

## 🧪 API Testing

### **AI Agent Endpoints**
```bash
# Health Check
curl http://localhost:8000/health

# Chat with Agent
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Merhaba, faturamı öğrenmek istiyorum", "session_id": "test-session"}'

# Analytics
curl http://localhost:8000/analytics/metrics

# Authentication Test
curl -X POST "http://localhost:8000/auth/authenticate" \
  -H "Content-Type: application/json" \
  -d '{"phone": "5551234567", "tc_no": "12345678901"}'
```

### **Voice Interface Test**
```bash
# Whisper STT Health
curl http://localhost:5001/health

# Frontend Access
# http://localhost:3000 - Ana chatbot arayüzü (Docker)
# http://localhost:8081 - Development server (Manuel)
```

## 📊 Monitoring & Analytics

- **Agent Performance**: Response time, accuracy metrics
- **User Interactions**: Conversation analytics
- **System Health**: API uptime, database performance
- **Business Metrics**: Customer satisfaction, resolution rates

## 🔧 Konfigürasyon

### **AI Agent Settings (.env)**
```bash
# Database
DATABASE_URL=postgresql://postgres:4Lt0g@localhost:5433/turklogos_db

# Redis
REDIS_URL=redis://localhost:6379

# LLM Configuration (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# TEKNOFEST 2025 Settings
COMPETITION_MODE=true
DEMO_DATA_ENABLED=true
COLLECT_METRICS=true
```

### **Frontend Settings**
```typescript
// API endpoints (src/lib/whisper-stt.ts)
const API_BASE_URL = 'http://localhost:5001';  // Whisper STT
const AGENT_API_URL = 'http://localhost:8000'; // AI Agent

// Ollama Configuration
const OLLAMA_BASE_URL = 'http://localhost:11434';
const OLLAMA_MODEL = 'llama3.1:8b';
```

## 🛡️ Güvenlik

- **JWT Authentication**: Secure API access
- **Data Privacy**: GDPR compliant data handling
- **Input Validation**: SQL injection prevention
- **Rate Limiting**: API abuse protection
- **Audit Logging**: Complete conversation tracking

## 📜 Lisans

Bu proje **Apache License 2.0** ile lisanslanmıştır.

```
Copyright 2025 TürkLogos Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 🏷️ Etiketler

**#BilisimVadisi2025** | **#TürkLogos** | **#AcikKaynakPlatformu** | **#TEKNOFEST2025** | **#AIAgent** | **#LangChain** | **#TelecomAI** | **#VoiceBot** | **#CustomerService**

## 📞 İletişim

- **GitHub Issues**: [Sorun bildirin](https://github.com/2025-BERTEMaL-SenaryoKategorisi/SenaryoKategorisi-TurkLogos/issues)
- **Email**: 20bertemal24@gmail.com

---

**🇹🇷 Türkiye Açık Kaynak Platformu** desteği ile **#BilisimVadisi2025** için geliştirilmiştir.

**TEKNOFEST 2025 - Yapay Zeka ve Derin Öğrenme Kategorisi**

**Açık Kaynak ❤️ Türkiye**
