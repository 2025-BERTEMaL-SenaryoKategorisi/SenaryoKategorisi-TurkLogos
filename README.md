# BERTeMaL — Üretken Yapay Zeka Destekli Otonom Çağrı Merkezi Senaryoları

Bu proje, çağrı merkezlerindeki müşteri etkileşimlerini otomatik olarak anlayan, analiz eden ve yanıtlayan **yapay zeka tabanlı bir ajan sistemi** geliştirmeyi amaçlamaktadır. Sistem; konuşmaları metne çevirme (ASR), niyet ve bilgi çıkarımı (NLU), doğal yanıt üretme (NLG), fonksiyon çağırma (Function Calling) ve ses sentezleme (TTS) bileşenlerinden oluşur.  
Hedef; daha hızlı, doğru ve erişilebilir bir çağrı merkezi deneyimi sunarak hem **kurumsal verimlilik** hem de **toplumsal fayda** sağlamaktır.

---

## 📌 İçindekiler
1. [Ekip Bilgisi](#ekip-bilgisi)
2. [Problem Tanımı](#problem-tanımı)
3. [Proje Kapsamı](#proje-kapsamı)
4. [Teknoloji ve Mimariler](#teknoloji-ve-mimariler)
5. [Veri Setleri](#veri-setleri)
6. [Model Kullanımı ve Değerlendirme](#model-kullanımı-ve-değerlendirme)
7. [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
8. [Lisans](#lisans)

---

## 👥 Ekip Bilgisi

| Fotoğraf | İsim | Ünvan | Sosyal Medya |
|---|---|---|---|
| <img src="./images/emre_satir.jpeg" width="100"/> | Emre ŞATIR | Danışman |  |
| <img src="./images/erdem_malkan.jpeg" width="100"/> | Erdem Altuğ MALKAN | Takım Kaptanı | [GitHub](https://github.com/altugmalkan) <br> [LinkedIn](https://www.linkedin.com/in/altuğ-malkan-80b8a4284/) |
| <img src="./images/dilan_basboga.jpeg" width="100"/> | Dilan Elif BAŞBOĞA | Takım Üyesi | [GitHub](https://github.com/elifbasboga) <br> [LinkedIn](https://www.linkedin.com/in/dilan-elif-başboğa-573091276/) |
| <img src="./images/ahmet_ucan.jpeg" width="100"/> | Ahmet Anıl UÇAN | Takım Üyesi | [GitHub](https://github.com/Anilf8) <br> [LinkedIn](https://www.linkedin.com/in/anıl-uçan-785336331/) |


**Danışman:**  
**Emre ŞATIR** — Dr. Öğr. Üyesi, İzmir Kâtip Çelebi Üniversitesi, Bilgisayar Mühendisliği Bölümü.  
Uzmanlık: Yapay Zeka, Makine Öğrenmesi, Doğal Dil İşleme, Makine Çevirisi.  
Projede teknik danışmanlık ve süreç takibi görevlerini üstlenmektedir.

**Takım Kaptanı:**  
**Erdem Altuğ MALKAN** — Bilgisayar Mühendisliği 4. sınıf öğrencisi.  
Görevler: Proje yol haritası, demo ve sunum senaryoları, LLM tabanlı ajan ve agentic yapı geliştirme.  
Teknolojiler: Express.js, Go, .NET Core, AWS, GCP, Docker.

**Takım Üyesi:**  
**Dilan Elif BAŞBOĞA** — Bilgisayar Mühendisliği 2. sınıf öğrencisi.  
Görevler: Mock fonksiyonlar ve entegrasyon, çağrı merkezi deneyimi simülasyonu.  
Deneyim: Çok sınıflı metin sınıflandırma, BERT tabanlı modelleme.

**Takım Üyesi:**  
**Ahmet Anıl UÇAN** — Bilgisayar Mühendisliği 2. sınıf öğrencisi.  
Görevler: Test seti hazırlama, KPI sistemi geliştirme, donanım entegrasyonu.  
Deneyim: Türkçe metin analizi, BERT tabanlı modeller, protez kol teknolojisi.

---

## ❗ Problem Tanımı
Günümüzde çağrı merkezlerinde;
- Uzun bekleme süreleri
- İnsan hatası riski
- Yüksek maliyetler
- Doğru anlama ve hızlı yönetim zorlukları  
gibi problemler yaşanmaktadır. Bu durum, özellikle yaşlılar, engelliler ve acil bilgiye ihtiyacı olan bireyler gibi hassas grupları olumsuz etkilemektedir.

---

## 🎯 Proje Kapsamı
- **ASR (Speech-to-Text):** OpenAI Whisper tabanlı konuşma tanıma.
- **NLU (Natural Language Understanding):** Intent ve slot çıkarımı.
- **LangChain Agent Mimarisi:** Çok adımlı akıl yürütme, dinamik araç seçimi.
- **Function Calling:** getUserInfo, getAvailablePackages, initiatePackageChange.
- **TTS (Text-to-Speech):** XTTS-V2, Bark, MMS-TTS-Tur, Tacotron.
- **Test Altyapısı:** 100+ senaryo, KPI ölçümleri, SQL tabanlı kayıt.

---

## 🛠 Teknoloji ve Mimariler
- **Backend:** Python, FastAPI
- **Frontend:** React
- **Yapay Zeka:** LangChain + Mistral veya LLaMA
- **Veritabanı:** SQL tabanlı yapı
- **Dağıtım:** Docker + Google Cloud Run
- **Ses İşleme:** OpenAI Whisper, Coqui XTTS, Bark, Tacotron

---

## 📂 Veri Setleri
- **Diyalog Verisi:** Çok adımlı müşteri-agent konuşmaları (intent & slot etiketli).
- **ASR Seti:** Ses-dosya ve transkript eşleşmeleri.
- **TTS Seti:** Metin ve ses çiftleri.
- **Sahte Veritabanı Verisi:** Müşteri bilgileri, paket ve fatura kayıtları.
- **Function Calling Verisi:** Farklı senaryolarda fonksiyon çağrı adımları.
- **Önceliklendirme Veri Seti:** Acil durum sınıflandırması (düşük/orta/yüksek).

---

## 📊 Model Kullanımı ve Değerlendirme
- **ASR Başarısı:** WER ≤ %10, CER ≤ %5
- **Intent & Slot F1-Score:** ≥ %85
- **NLG BERTScore:** ≥ %85
- **TTS Doğruluğu:** Doğal, anlaşılır seslendirme
- **Otomatik Test:** Python scriptleri + SQL tabanlı kayıt

---

## 🚀 Kurulum ve Çalıştırma

```bash
# Depoyu klonla
git clone https://github.com/kullanici/bertemal.git
cd bertemal

# Backend kurulum
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend kurulum
cd frontend
npm install
npm start
