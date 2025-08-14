import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LocalWhisperSTTService, AudioRecorder } from "@/lib/whisper-stt";
import { WebSpeechTTSService } from "@/lib/tts-service";
import { useTheme } from "@/lib/theme-context";
import { 
  Mic, 
  MicOff, 
  Send, 
  Settings, 
  MessageSquare, 
  Phone,
  User,
  Bot,
  Volume2,
  VolumeX,
  Loader2,
  Menu,
  X,
  Moon,
  Sun,
  Square,
  Play,
  Pause
} from 'lucide-react';
import { ChatSidebar, Chat as SidebarChat } from './ChatSidebar';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

const TelecomChatBot = () => {
  // Tema yönetimi
  const { theme, toggleTheme } = useTheme();
  
  // Chat management states - localStorage ile senkronize
  const [chats, setChats] = useState<Chat[]>(() => {
    try {
      const savedChats = localStorage.getItem('telekom-chats');
      if (savedChats) {
        // JSON olarak kaydedilen sohbetleri çözümle
        const parsedChats = JSON.parse(savedChats);
        // Date objelerini yeniden oluştur
        const restoredChats = parsedChats.map((chat: any) => ({
          ...chat,
          createdAt: new Date(chat.createdAt),
          messages: chat.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        console.log('LocalStorage\'dan chat geçmişi yüklendi:', restoredChats.length, 'sohbet');
        return restoredChats;
      }
    } catch (error) {
      console.error('Chat geçmişi yüklenirken hata:', error);
    }
    console.log('Yeni başlangıç - localStorage boş');
    return [];
  });
  
  const [activeChat, setActiveChat] = useState<string | null>(() => {
    const savedActiveChat = localStorage.getItem('telekom-active-chat');
    if (savedActiveChat) {
      console.log('Aktif chat localStorage\'dan yüklendi:', savedActiveChat);
    }
    return savedActiveChat || null;
  });
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const [currentMessage, setCurrentMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // TTS mesaj kontrolleri
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const [ttsQueue, setTtsQueue] = useState<string[]>([]);
  
  // Whisper STT servisleri
  const whisperService = useRef<LocalWhisperSTTService | null>(null);
  const audioRecorder = useRef<AudioRecorder>(new AudioRecorder());
  const ttsService = useRef<WebSpeechTTSService | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Chat management functions
  const createNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: 'Yeni Sohbet',
      messages: [{
        id: '1',
        text: 'Merhaba! TürkLogos Telekom Asistanı\'na hoş geldiniz. Size nasıl yardımcı olabilirim?',
        sender: 'assistant',
        timestamp: new Date()
      }],
      createdAt: new Date()
    };
    setChats(prev => [newChat, ...prev]);
    setActiveChat(newChat.id);
    setIsSidebarOpen(false);
  };

  const selectChat = (chatId: string) => {
    setActiveChat(chatId);
    setIsSidebarOpen(false);
  };

  const deleteChat = (chatId: string) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (activeChat === chatId) {
      const remainingChats = chats.filter(chat => chat.id !== chatId);
      if (remainingChats.length > 0) {
        setActiveChat(remainingChats[0].id);
      } else {
        createNewChat();
      }
    }
  };

  const getCurrentChat = () => chats.find(chat => chat.id === activeChat);
  const currentMessages = getCurrentChat()?.messages || [];

  // Sidebar için sohbet verilerini uygun formata dönüştür
  const sidebarChats: SidebarChat[] = chats.map(chat => ({
    id: chat.id,
    title: chat.title,
    lastMessage: chat.messages.length > 1 ? chat.messages[chat.messages.length - 1].text : '',
    timestamp: chat.createdAt,
    messageCount: chat.messages.length
  }));

  const addMessageToChat = (message: Message) => {
    setChats(prev => prev.map(chat => {
      if (chat.id === activeChat) {
        const updatedMessages = [...chat.messages, message];
        return {
          ...chat,
          messages: updatedMessages,
          title: chat.messages.length === 1 ? message.text.slice(0, 30) + '...' : chat.title
        };
      }
      return chat;
    }));
  };

  // LocalStorage'a sohbet geçmişini kaydet
  useEffect(() => {
    try {
      localStorage.setItem('telekom-chats', JSON.stringify(chats));
      console.log('Chat geçmişi localStorage\'a kaydedildi:', chats.length, 'sohbet');
    } catch (error) {
      console.error('Chat geçmişi kaydedilirken hata:', error);
    }
  }, [chats]);

  useEffect(() => {
    if (activeChat) {
      localStorage.setItem('telekom-active-chat', activeChat);
      console.log('Aktif chat kaydedildi:', activeChat);
    } else {
      localStorage.removeItem('telekom-active-chat');
      console.log('Aktif chat temizlendi');
    }
  }, [activeChat]);

  // Yeni sohbet oluşturma - Eğer başlangıçta chat yoksa otomatik yeni sohbet oluştur
  useEffect(() => {
    if (chats.length === 0) {
      createNewChat();
    }
  }, []);

  // Yerel Whisper STT sistemi kurulumu
  useEffect(() => {
    whisperService.current = new LocalWhisperSTTService();
    
    // TTS Service initialize et
    ttsService.current = new WebSpeechTTSService((speaking) => {
      setIsSpeaking(speaking);
      // Eğer konuşma biterse playingMessageId'yi temizle
      if (!speaking) {
        setPlayingMessageId(null);
      }
    });
    
    // Server health check
    whisperService.current.checkHealth().then(isHealthy => {
      if (!isHealthy) {
        console.warn('Whisper server is not running. Please start the Python backend.');
      } else {
        console.log('Whisper server is running successfully!');
      }
    });

    return () => {
      if (isListening) {
        stopListening();
      }
      if (ttsService.current) {
        ttsService.current.stop();
      }
    };
  }, []);

  // Sayfa kapatılmadan önce verileri kaydet
  useEffect(() => {
    const handleBeforeUnload = () => {
      try {
        localStorage.setItem('telekom-chats', JSON.stringify(chats));
        if (activeChat) {
          localStorage.setItem('telekom-active-chat', activeChat);
        }
      } catch (error) {
        console.error('Sayfa kapatılırken veri kaydetme hatası:', error);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [chats, activeChat]);

  // Mesajların en altına kaydırma-otomatik scroll
  useEffect(() => {
    scrollToBottom();
  }, [currentMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Ses kaydetmeyi başlat
  const startListening = async () => {
    if (!whisperService.current || isProcessingAudio) return;
    
    try {
      setIsListening(true);
      setIsProcessingAudio(true);
      await audioRecorder.current.startRecording();
    } catch (error) {
      console.error('Ses kaydı başlatılamadı:', error);
      setIsListening(false);
      setIsProcessingAudio(false);
    }
  };

  // Ses kaydetmeyi durdur ve metne dök
  const stopListening = async () => {
    if (!whisperService.current || !isListening) return;
    
    try {
      const audioBlob = await audioRecorder.current.stopRecording();
      setIsListening(false);
      
      if (audioBlob && audioBlob.size > 0) {
        const transcription = await whisperService.current.transcribeAudio(audioBlob);
        if (transcription.trim()) {
          setCurrentMessage(transcription);
        }
      }
    } catch (error) {
      console.error('Ses işleme hatası:', error);
    } finally {
      setIsProcessingAudio(false);
    }
  };

  // Toggle ses kaydı (başlat/durdur)
  const toggleVoiceRecording = async () => {
    // Eğer processing state'i takılıp kaldıysa zorla reset et
    if (isProcessingAudio && !isListening) {
      setIsProcessingAudio(false);
      return;
    }

    if (isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  };

  // TTS Kontrol Fonksiyonları
  const playMessage = async (messageId: string, text: string) => {
    if (!ttsService.current || !isTTSEnabled) return;
    
    try {
      // Eğer başka bir mesaj çalıyorsa durdur
      if (playingMessageId) {
        ttsService.current.stop();
      }
      
      setPlayingMessageId(messageId);
      await ttsService.current.speak(text);
      setPlayingMessageId(null);
    } catch (error) {
      console.error('TTS oynatma hatası:', error);
      setPlayingMessageId(null);
    }
  };

  const stopMessage = () => {
    if (!ttsService.current) return;
    
    ttsService.current.stop();
    setPlayingMessageId(null);
  };

  // Mesaj gönderme
  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || currentMessage.trim();
    if (!textToSend) return;

    // Kullanıcı mesajını ekle
    const userMessage: Message = {
      id: Date.now().toString(),
      text: textToSend,
      sender: 'user',
      timestamp: new Date()
    };

    addMessageToChat(userMessage);
    setCurrentMessage('');
    setIsTyping(true);

    // Gerçek backend API çağrısı
    try {
  const response = await fetch('/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: textToSend })
      });
      const data = await response.json();
  const botText = data.response || data.reply || data.text || 'Yanıt alınamadı.';
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: botText,
        sender: 'assistant',
        timestamp: new Date()
      };
      addMessageToChat(botResponse);
      setIsTyping(false);
      // Bot cevabını TTS ile okuma
      if (isTTSEnabled && ttsService.current) {
        setPlayingMessageId(botResponse.id);
        ttsService.current.speak(botResponse.text).catch(error => {
          console.error('TTS hatası:', error);
          setPlayingMessageId(null);
        });
      }
    } catch (error) {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sunucuya bağlanılamadı veya hata oluştu.',
        sender: 'assistant',
        timestamp: new Date()
      };
      addMessageToChat(botResponse);
      setIsTyping(false);
    }
  };

  // Klavye eventi
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // JSX render
  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-neutral-800 dark:to-stone-700 transition-colors duration-300">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
        lg:translate-x-0 transition-transform duration-300 ease-in-out
        fixed lg:relative inset-y-0 left-0 z-40 lg:z-auto`}>
        <ChatSidebar
          chats={sidebarChats}
          activeChat={activeChat}
          onChatSelect={selectChat}
          onNewChat={createNewChat}
          onDeleteChat={deleteChat}
        />
      </div>

      {/*Mobilde Sidebar üstü koyu overlay */}
      {isSidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex flex-col flex-1 max-w-4xl mx-auto">
      {/* Header */}
      <Card className="rounded-none border-b border-telecom-primary/20 bg-white/80 backdrop-blur-sm dark:bg-neutral-700/90 dark:border-stone-600/40">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* Menü button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="lg:hidden text-telecom-primary dark:text-amber-200 dark:hover:bg-stone-600"
              >
                <Menu className="w-4 h-4" />
              </Button>
              
              {/* Logo ve ikon */}
              <div className="w-16 h-16 flex items-center justify-center">
                <img 
                  src="/logo.png" 
                  alt="TürkLogos" 
                  className="w-16 h-16 object-contain"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    target.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <MessageSquare className="w-8 h-8 text-telecom-primary hidden" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-telecom-primary dark:text-amber-100">
                  TürkLogos Telekom Asistanı
                </CardTitle>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-telecom-accent text-telecom-primary border border-telecom-primary/20 dark:bg-stone-600/80 dark:text-green-300 dark:border-green-400/30">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse dark:bg-green-400"></div>
                    Çevrimiçi
                  </Badge>
                  <p className="text-sm text-gray-600 dark:text-stone-300">
                    Sesli ve yazılı destek • 7/24 hizmet
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {/* Ses Aktif Göstergesi */}
              {isSpeaking && (
                <div className="flex items-center space-x-1 px-2 py-1 rounded-full bg-telecom-primary/10 dark:bg-amber-300/20">
                  <Volume2 className="w-3 h-3 text-telecom-primary dark:text-amber-300 animate-pulse" />
                  <span className="text-xs font-medium text-telecom-primary dark:text-amber-200">
                    Ses Aktif
                  </span>
                </div>
              )}
              
              {/* Dark Mode Toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleTheme}
                className="text-telecom-primary hover:bg-telecom-primary/10 dark:text-amber-200 dark:hover:bg-stone-600"
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </Button>
              
              {/* Ayarlar butonu */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
                className="text-telecom-primary hover:bg-telecom-primary/10 dark:text-amber-200 dark:hover:bg-stone-600"
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Ayarlar paneli */}
      {showSettings && (
        <Card className="mx-4 mt-2 border-telecom-primary/20 dark:border-stone-600/50 dark:bg-neutral-800/80">
          <CardContent className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Mic className="w-4 h-4 text-telecom-primary dark:text-amber-200" />
                  <span className="text-sm font-medium dark:text-stone-200">Ses Girişi</span>
                </div>
                <Switch
                  checked={isVoiceEnabled}
                  onCheckedChange={setIsVoiceEnabled}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Volume2 className="w-4 h-4 text-telecom-primary dark:text-amber-200" />
                  <span className="text-sm font-medium dark:text-stone-200">Ses Çıkışı</span>
                </div>
                <Switch
                  checked={isTTSEnabled}
                  onCheckedChange={setIsTTSEnabled}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mesajlar Listesi */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-4 py-2">
          <div className="space-y-4">
            {currentMessages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.sender === 'user'
                      ? 'bg-telecom-primary text-white dark:bg-stone-600'
                      : 'bg-white border border-gray-200 text-gray-800 dark:bg-neutral-700/90 dark:border-stone-500/50 dark:text-amber-100'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    <div className="flex-shrink-0">
                      {message.sender === 'user' ? (
                        <User className="w-4 h-4 mt-1" />
                      ) : (
                        <div className="flex items-center space-x-1">
                          <Bot className="w-4 h-4 mt-1 text-telecom-primary dark:text-amber-300" />
                          {isSpeaking && playingMessageId === message.id && (
                            <Volume2 className="w-3 h-3 text-telecom-primary animate-pulse dark:text-amber-300" />
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <p className="text-sm leading-relaxed flex-1">{message.text}</p>
                        
                        {/* TTS Kontrolleri - Sadece bot mesajları için */}
                        {message.sender === 'assistant' && (
                          <div className="flex items-center space-x-1 ml-2 flex-shrink-0">
                            {playingMessageId === message.id ? (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 hover:bg-telecom-primary/10 dark:hover:bg-stone-600"
                                onClick={() => stopMessage()}
                              >
                                <Pause className="w-3 h-3 text-telecom-primary dark:text-amber-300" />
                              </Button>
                            ) : (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 hover:bg-telecom-primary/10 dark:hover:bg-stone-600"
                                onClick={() => playMessage(message.id, message.text)}
                                disabled={!isTTSEnabled}
                              >
                                <Play className="w-3 h-3 text-telecom-primary dark:text-amber-300" />
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <p className={`text-xs mt-1 ${
                        message.sender === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-stone-400'
                      }`}>
                        {message.timestamp.toLocaleTimeString('tr-TR', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Bot yazıyor animasyonu */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg p-3 max-w-[80%] dark:bg-gray-700 dark:border-gray-600">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-4 h-4 text-telecom-primary dark:text-amber-300" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce dark:bg-gray-300"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce dark:bg-gray-300" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce dark:bg-gray-300" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <Card className="rounded-none border-t border-telecom-primary/20 bg-white/80 backdrop-blur-sm dark:bg-neutral-800/80 dark:border-stone-600/50">
        <CardContent className="p-4">
          <div className="flex items-end space-x-2">
            {/* Voice Input Button */}
            {isVoiceEnabled && (
              <Button
                size="lg"
                variant={isListening ? "destructive" : "default"}
                className={`${
                  isListening 
                    ? 'bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700' 
                    : 'bg-telecom-primary hover:bg-telecom-primary/90 dark:bg-stone-600 dark:hover:bg-stone-700'
                } text-white transition-all duration-200`}
                onClick={toggleVoiceRecording}
                disabled={isProcessingAudio && !isListening}
              >
                {isListening ? (
                  <Square className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>
            )}

            {/* Text Input */}
            <div className="flex-1">
              <Input
                ref={inputRef}
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Mesajınızı yazın veya konuşmak için mikrofonu kullanın..."
                className="border-telecom-primary/30 focus:border-telecom-primary focus:ring-telecom-primary/20 bg-white/50 dark:bg-neutral-700/80 dark:border-stone-500/50 dark:focus:border-amber-400 dark:text-amber-100 dark:placeholder-stone-300"
                disabled={isTyping}
              />
            </div>

            {/* Send Button */}
            <Button
              onClick={() => handleSendMessage()}
              disabled={!currentMessage.trim() || isTyping}
              size="lg"
              className="bg-telecom-primary hover:bg-telecom-primary/90 text-white dark:bg-stone-600 dark:hover:bg-stone-700"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
          
          {/* Sesli kayıt durumu mesajı */}
          {isListening && (
            <div className="mt-2 text-center">
              <div className="text-sm text-telecom-primary font-medium dark:text-amber-200 flex items-center justify-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span>🎙️ Kaydediliyor... Durdurmak için ⏹️ butonuna tıklayın</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  );
};

export default TelecomChatBot;
