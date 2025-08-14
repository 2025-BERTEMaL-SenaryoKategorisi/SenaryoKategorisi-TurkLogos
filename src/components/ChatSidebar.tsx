import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  MoreHorizontal,
  Clock
} from 'lucide-react';

export interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

interface ChatSidebarProps {
  chats: Chat[];
  activeChat: string | null;
  onChatSelect: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  activeChat,
  onChatSelect,
  onNewChat,
  onDeleteChat
}) => {
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Şimdi';
    if (minutes < 60) return `${minutes}dk önce`;
    if (hours < 24) return `${hours}sa önce`;
    if (days < 7) return `${days}g önce`;
    return date.toLocaleDateString('tr-TR');
  };

  //Başlıkları kısaltmak için yardımcı fonksiyon
  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  return (
    <div className="w-80 h-full bg-white border-r border-gray-200 flex flex-col dark:bg-neutral-900 dark:border-stone-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-stone-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-amber-100">Sohbetler</h2>
          <Button
            onClick={onNewChat}
            size="sm"
            className="bg-telecom-primary hover:bg-telecom-primary/90 text-white dark:bg-stone-600 dark:hover:bg-stone-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Yeni Sohbet
          </Button>
        </div>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1 p-2">
        <div className="space-y-2">
          {chats.length === 0 ? (
            <div className="text-center text-gray-500 py-8 dark:text-stone-300">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-stone-500" />
              <p className="text-sm">Henüz sohbet yok</p>
              <p className="text-xs text-gray-400 mt-1 dark:text-stone-400">Yeni sohbet başlatın</p>
            </div>
          ) : (
            chats.map((chat) => (
              <Card
                key={chat.id}
                className={`cursor-pointer transition-all duration-200 hover:shadow-md dark:bg-neutral-800/80 dark:border-stone-600 ${
                  activeChat === chat.id
                    ? 'ring-2 ring-telecom-primary bg-telecom-primary/5 dark:ring-amber-400 dark:bg-amber-500/10'
                    : 'hover:bg-gray-50 dark:hover:bg-stone-700/50'
                }`}
                onClick={() => onChatSelect(chat.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <MessageSquare className="w-4 h-4 text-telecom-primary dark:text-amber-300 flex-shrink-0" />
                        <h3 className="text-sm font-medium text-gray-900 dark:text-amber-100 truncate">
                          {truncateTitle(chat.title)}
                        </h3>
                      </div>
                      
                      {/* Son mesajın kısa özeti */}
                      <p className="text-xs text-gray-600 dark:text-stone-200 mb-2 line-clamp-2">
                        {chat.lastMessage}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 dark:text-stone-400">
                          <Clock className="w-3 h-3" />
                          <span>{formatTime(chat.timestamp)}</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-400 dark:text-stone-400">
                            {chat.messageCount} mesaj
                          </span>
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            className="w-6 h-6 p-0 text-gray-400 hover:text-red-500 dark:text-stone-400 dark:hover:text-red-400"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteChat(chat.id);
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-stone-700">
        <div className="text-xs text-gray-500 text-center dark:text-stone-400">
          <p>TürkLogos Telekom Asistanı</p>
          <p className="mt-1">7/24 Destek Hizmeti</p>
        </div>
      </div>
    </div>
  );
};
