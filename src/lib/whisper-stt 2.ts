// Yerel Whisper Large Modeli kullanarak ses transkripsiyonu yapan bir servis
// Bu servis, arka planda çalışan bir Whisper STT sunucusuna HTTP istekleri gönderiyor.
export class LocalWhisperSTTService {
  private baseURL = 'http://api:8000';

  // Ses kaydını metne dönüştürmek için sunucuya gönderiyor.
  async transcribeAudio(audioBlob: Blob): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');

      const response = await fetch(`${this.baseURL}/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.transcript || '';
    } catch (error) {
      console.error('Local Whisper STT Hatası:', error);
      throw error;
    }
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch (error) {
      console.error('Whisper sunucu sağlık kontrolü başarısız:', error);
      return false;
    }
  }

  async getModelInfo(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/models`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Model bilgisi alınamadı:', error);
      return null;
    }
  }
}

// Ses kaydı için MediaRecorder yardımcı sınıfı
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;

  async startRecording(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });

      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this.audioChunks = []; // Ses kayıt parçalarını tutmak için

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

    // Her 100ms'de bir veri toplayacak şekilde başlatıyoruz
      this.mediaRecorder.start(100);
    } catch (error) {
      console.error('Kayıt başlatma hatası:', error);
      throw error;
    }
  }

  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('Aktif bir kayıt yok'));
        return;
      }

      if (this.mediaRecorder.state === 'inactive') {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.cleanup();
        resolve(audioBlob);
        return;
      }

      //Kayıt durunca blob oluştur ve döndür
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.cleanup();
        resolve(audioBlob);
      };

      this.mediaRecorder.stop();
    });
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.mediaRecorder = null;
    this.audioChunks = [];
  }

  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording';
  }
}
