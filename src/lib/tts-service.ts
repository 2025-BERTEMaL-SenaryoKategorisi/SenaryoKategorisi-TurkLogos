// Text-to-Speech - Frontend implementation
// backend TTS ile değiştirilecek!!!

export interface TTSService {
  speak(text: string): Promise<void>;
  stop(): void;
  isSupported(): boolean;
  getSpeakingStatus(): boolean;
}

export class WebSpeechTTSService implements TTSService {
  private _isSpeaking = false;
  private onSpeakingChange: (speaking: boolean) => void = () => {};

  constructor(onSpeakingChange?: (speaking: boolean) => void) {
    if (onSpeakingChange) {
      this.onSpeakingChange = onSpeakingChange;
    }
  }

  async speak(text: string): Promise<void> {
    if (!this.isSupported() || this._isSpeaking) {
      return;
    }

    // Mevcut konuşmaları durdur
    window.speechSynthesis.cancel();

    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Türkçe ses ayarları
      utterance.lang = 'tr-TR';
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;

      utterance.onstart = () => {
        this._isSpeaking = true;
        this.onSpeakingChange(true);
      };

      utterance.onend = () => {
        this._isSpeaking = false;
        this.onSpeakingChange(false);
        resolve();
      };

      utterance.onerror = (event) => {
        this._isSpeaking = false;
        this.onSpeakingChange(false);
        reject(new Error(`TTS Error: ${event.error}`));
      };

      // Türkçe ses ayarları(Tarayıcıdaki sesler arasından Türkçeyi seç)
      const voices = window.speechSynthesis.getVoices();
      const turkishVoice = voices.find(voice => 
        voice.lang.includes('tr') || 
        voice.name.includes('Turkish') || 
        voice.name.includes('Türk')
      );

      if (turkishVoice) {
        utterance.voice = turkishVoice;
      }

      window.speechSynthesis.speak(utterance);
    });
  }

  stop(): void {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      this._isSpeaking = false;
      this.onSpeakingChange(false);
    }
  }

  isSupported(): boolean {
    return 'speechSynthesis' in window;
  }

  getSpeakingStatus(): boolean {
    return this._isSpeaking;
  }
}

// Gelecekte backend TTS için hazır interface
export class BackendTTSService implements TTSService {
  private baseURL = 'http://api:8000';
  private _isSpeaking = false;
  private onSpeakingChange: (speaking: boolean) => void = () => {};

  constructor(onSpeakingChange?: (speaking: boolean) => void) {
    if (onSpeakingChange) {
      this.onSpeakingChange = onSpeakingChange;
    }
  }

  async speak(text: string): Promise<void> {
    if (this._isSpeaking) return;

    try {
      this._isSpeaking = true;
      this.onSpeakingChange(true);

      // Backend TTS endpoint'ine POST isteği gönder
      const response = await fetch(`${this.baseURL}/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`Backend TTS error: ${response.status}`);
      }

      // Audio blob'u al ve çal
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      return new Promise((resolve, reject) => {
        audio.onended = () => {
          this._isSpeaking = false;
          this.onSpeakingChange(false);
          URL.revokeObjectURL(audioUrl);
          resolve();
        };

        audio.onerror = () => {
          this._isSpeaking = false;
          this.onSpeakingChange(false);
          URL.revokeObjectURL(audioUrl);
          reject(new Error('Audio playback error'));
        };

        audio.play().catch(reject);
      });
    } catch (error) {
      this._isSpeaking = false;
      this.onSpeakingChange(false);
      throw error;
    }
  }

  stop(): void {
    // Backend TTS durdurmak için endpoint çağrılacak
    this._isSpeaking = false;
    this.onSpeakingChange(false);
  }

  isSupported(): boolean {
    // Backend health check yapılacak
    return true;
  }

  getSpeakingStatus(): boolean {
    return this._isSpeaking;
  }
}
