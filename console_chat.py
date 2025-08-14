#!/usr/bin/env python3
"""
Interactive Console Chat Application for Turkish Telecom Call Center Agent
"""

import os
import sys
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.graph import create_telecom_workflow
from graph.state import GraphState
from graph.memory.redis_client import redis_memory


# Colors for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TelecomChatConsole:
    """Interactive console chat application"""

    def __init__(self):
        load_dotenv()
        self.workflow = None
        self.conversation_id = None
        self.user_name = None
        self.session_start_time = datetime.now()
        self.message_count = 0

        # Initialize workflow
        try:
            self.workflow = create_telecom_workflow()
            print(f"{Colors.OKGREEN}✅ Telecom agent workflow loaded successfully{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to load workflow: {e}{Colors.ENDC}")
            sys.exit(1)

        # Check Redis connection
        if redis_memory.health_check():
            print(f"{Colors.OKGREEN}✅ Redis memory system connected{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️  Redis not available - memory will not persist{Colors.ENDC}")

    def print_banner(self):
        """Print welcome banner"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    🏢 TELECOM CALL CENTER                    ║
║                     AI Customer Service                      ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}

{Colors.OKCYAN}Merhaba! Türk Telekom müşteri hizmetlerine hoş geldiniz.{Colors.ENDC}
{Colors.OKBLUE}Size nasıl yardımcı olabilirim?{Colors.ENDC}

{Colors.WARNING}💡 Kişisel sorularınız için telefon numaranızı belirtmeyi unutmayın!{Colors.ENDC}
{Colors.WARNING}   Örnek: "Benim paketim nedir? 0555 123 45 67"{Colors.ENDC}

{Colors.HEADER}Komutlar:{Colors.ENDC}
• {Colors.OKGREEN}/help{Colors.ENDC}     - Yardım menüsü
• {Colors.OKGREEN}/status{Colors.ENDC}   - Oturum durumu
• {Colors.OKGREEN}/clear{Colors.ENDC}    - Konuşma geçmişini temizle
• {Colors.OKGREEN}/quit{Colors.ENDC}     - Uygulamadan çık
• {Colors.OKGREEN}/examples{Colors.ENDC} - Örnek sorular

{Colors.OKCYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}
"""
        print(banner)

    def print_help(self):
        """Print help menu"""
        help_text = f"""
{Colors.HEADER}{Colors.BOLD}📖 YARDIM MENÜSÜ{Colors.ENDC}

{Colors.OKBLUE}Paket Bilgileri:{Colors.ENDC}
• "Benim paketim nedir? 0555 123 45 67"
• "Hangi paketleriniz var?"
• "Paket değiştirebilir miyim?"

{Colors.OKBLUE}Fatura İşlemleri:{Colors.ENDC}
• "Faturamı görebilir miyim? 0555 123 45 67"
• "Son fatura tutarım ne kadar?"
• "Fatura ödeme nasıl yapılır?"

{Colors.OKBLUE}Kullanım Bilgileri:{Colors.ENDC}
• "Kalan internetim kaç GB? 0555 123 45 67"
• "Bu ay kaç dakika konuştum?"
• "SMS kotam ne kadar?"

{Colors.OKBLUE}Destek ve Şikayetler:{Colors.ENDC}
• "İnternet yavaş, ne yapabilirim?"
• "Destek talebim var"
• "Şikayet oluşturmak istiyorum"

{Colors.OKBLUE}Genel Bilgiler:{Colors.ENDC}
• "Müşteri hizmetleri saatleri?"
• "Mağaza adresleri nelerdir?"
• "Roaming ücretleri nasıl?"

{Colors.WARNING}💡 İpucu: Kişisel bilgileriniz için mutlaka telefon numaranızı belirtin!{Colors.ENDC}
"""
        print(help_text)

    def print_examples(self):
        """Print example conversations"""
        examples = f"""
{Colors.HEADER}{Colors.BOLD}💬 ÖRNEK KONUŞMALAR{Colors.ENDC}

{Colors.OKGREEN}1. Paket Sorgulama:{Colors.ENDC}
   👤 "Merhaba, benim paketim nedir? 0555 123 45 67"
   🤖 "Merhaba! Paket bilgilerinizi getiriyorum..."

{Colors.OKGREEN}2. Fatura Sorgulama:{Colors.ENDC}
   👤 "Faturamı görebilir miyim?"
   🤖 "Telefon numaranızı belirtir misiniz?"
   👤 "0555 123 45 67"
   🤖 "Fatura bilgileriniz..."

{Colors.OKGREEN}3. Genel Bilgi:{Colors.ENDC}
   👤 "Hangi paketleriniz var?"
   🤖 "Şirketimizde Bronze, Silver, Gold..."

{Colors.OKGREEN}4. Teknik Destek:{Colors.ENDC}
   👤 "İnternetim çok yavaş, yardım edebilir misiniz?"
   🤖 "Teknik destek için size yardımcı olayım..."

{Colors.WARNING}💡 Konuşma sırasında agent sizi hatırlayacak ve telefon numaranızı tekrar sormayacaktır!{Colors.ENDC}
"""
        print(examples)

    def print_status(self):
        """Print session status"""
        uptime = datetime.now() - self.session_start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        # Get memory stats
        conversation_history = []
        user_context = {}
        phone_number = "Belirtilmedi"

        if self.conversation_id and redis_memory.health_check():
            conversation_history = redis_memory.get_conversation_history(self.conversation_id)
            phone_number = redis_memory.get_phone_from_conversation(self.conversation_id) or "Belirtilmedi"
            if phone_number != "Belirtilmedi":
                user_context = redis_memory.get_user_context(phone_number)

        status = f"""
{Colors.HEADER}{Colors.BOLD}📊 OTURUM DURUMU{Colors.ENDC}

{Colors.OKBLUE}Oturum Bilgileri:{Colors.ENDC}
• Oturum ID: {self.conversation_id or 'Henüz başlatılmadı'}
• Başlama Zamanı: {self.session_start_time.strftime('%H:%M:%S')}
• Süre: {hours:02d}:{minutes:02d}:{seconds:02d}
• Mesaj Sayısı: {self.message_count}

{Colors.OKBLUE}Hafıza Durumu:{Colors.ENDC}
• Redis Bağlantısı: {'✅ Aktif' if redis_memory.health_check() else '❌ Pasif'}
• Konuşma Geçmişi: {len(conversation_history)} mesaj
• Telefon Numarası: {phone_number}
• Kullanıcı Bağlamı: {len(user_context)} alan

{Colors.OKBLUE}Sistem Durumu:{Colors.ENDC}
• AI Agent: ✅ Aktif
• Workflow: ✅ Yüklü
• Araçlar: ✅ Hazır
"""
        print(status)

    def create_initial_state(self, question: str) -> GraphState:
        """Create initial state for workflow"""
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())

        return {
            "question": question,
            "conversation_id": self.conversation_id,
            "generation": "",
            "documents": [],
            "relevant_documents": [],
            "tool_results": None,
            "datasource": "",
            "needs_function_call": False,
            "question_grade": False,
            "retrieval_grade": False,
            "answer_grade": False,
            "retry_count": 0,
            "conversation_history": [],
            "user_context": {}
        }

    def process_user_input(self, user_input: str) -> str:
        """Process user input through the AI workflow"""
        try:
            # Create state
            initial_state = self.create_initial_state(user_input)

            # Show processing indicator
            print(f"{Colors.OKCYAN}🤖 İşleniyor...{Colors.ENDC}")

            # Run workflow
            start_time = time.time()
            result = self.workflow.invoke(initial_state)
            processing_time = time.time() - start_time

            # Extract response
            response = result.get('generation', 'Üzgünüm, bir yanıt oluşturamadım.')

            # Show processing info in debug mode
            if os.getenv('DEBUG', '').lower() == 'true':
                route = result.get('datasource', 'Unknown')
                tools_used = result.get('user_context', {}).get('last_tools_used', [])
                print(
                    f"{Colors.WARNING}[DEBUG] Route: {route}, Tools: {tools_used}, Time: {processing_time:.2f}s{Colors.ENDC}")

            return response

        except Exception as e:
            error_msg = f"Üzgünüm, bir hata oluştu: {str(e)}"
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return error_msg

    def handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True if should continue, False if should quit"""
        command = command.lower().strip()

        if command == '/help':
            self.print_help()
        elif command == '/status':
            self.print_status()
        elif command == '/examples':
            self.print_examples()
        elif command == '/clear':
            if self.conversation_id and redis_memory.health_check():
                redis_memory.clear_conversation(self.conversation_id)
                print(f"{Colors.OKGREEN}✅ Konuşma geçmişi temizlendi{Colors.ENDC}")
            self.conversation_id = None
            self.message_count = 0
            print(f"{Colors.OKGREEN}🆕 Yeni oturum başlatıldı{Colors.ENDC}")
        elif command in ['/quit', '/exit', '/q']:
            return False
        else:
            print(f"{Colors.WARNING}❓ Bilinmeyen komut: {command}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}💡 Yardım için /help yazın{Colors.ENDC}")

        return True

    def run(self):
        """Main chat loop"""
        self.print_banner()

        print(f"{Colors.OKGREEN}🚀 Chat başlatıldı! Sorunuzu yazın...{Colors.ENDC}\n")

        try:
            while True:
                # Get user input
                try:
                    user_input = input(f"{Colors.BOLD}👤 Siz: {Colors.ENDC}").strip()
                except (KeyboardInterrupt, EOFError):
                    print(f"\n{Colors.OKCYAN}👋 Görüşmek üzere!{Colors.ENDC}")
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        print(f"{Colors.OKCYAN}👋 İyi günler dileriz!{Colors.ENDC}")
                        break
                    continue

                # Process user question
                self.message_count += 1

                # Get AI response
                response = self.process_user_input(user_input)

                # Display response
                print(f"{Colors.OKGREEN}🤖 Agent: {Colors.ENDC}{response}\n")

                # Show conversation tips periodically
                if self.message_count % 5 == 0:
                    print(f"{Colors.WARNING}💡 İpucu: /help komutu ile daha fazla örnek görebilirsiniz{Colors.ENDC}\n")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Kritik hata: {e}{Colors.ENDC}")

        finally:
            # Cleanup
            print(f"{Colors.OKCYAN}📊 Toplam {self.message_count} mesaj işlendi{Colors.ENDC}")
            if self.conversation_id:
                print(f"{Colors.OKCYAN}💾 Konuşma geçmişi kaydedildi (ID: {self.conversation_id[:8]}...){Colors.ENDC}")


def main():
    """Entry point for the console chat application"""

    # Check environment
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('GROQ_API_KEY'):
        print(f"{Colors.FAIL}❌ OPENAI_API_KEY veya GROQ_API_KEY environment variable'ı gerekli{Colors.ENDC}")
        sys.exit(1)

    # Start chat application
    try:
        chat_app = TelecomChatConsole()
        chat_app.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.OKCYAN}👋 Uygulama kapatıldı{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Uygulama hatası: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()