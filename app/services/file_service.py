import logging
import os
from aiogram.types import FSInputFile
from app.config.config import config

logger = logging.getLogger(__name__)

class FileService:
    # Папка для хранения PDF файлов
    PDF_FOLDER = "rewards_pdf"
    
    @staticmethod
    def ensure_pdf_folder():
        """Create PDF folder if it doesn't exist"""
        if not os.path.exists(FileService.PDF_FOLDER):
            os.makedirs(FileService.PDF_FOLDER)
            logger.info(f"✅ Created PDF folder: {FileService.PDF_FOLDER}")
    
    @staticmethod
    def get_pdf_path(file_id: str):
        """Get full path for PDF file"""
        return os.path.join(FileService.PDF_FOLDER, f"{file_id}.pdf")
    
    @staticmethod
    def pdf_exists(file_id: str):
        """Check if PDF file exists"""
        return os.path.exists(FileService.get_pdf_path(file_id))
    
    @staticmethod
    async def send_pdf_to_user(bot, chat_id: int, file_id: str, caption: str = ""):
        """Send PDF file to user"""
        try:
            FileService.ensure_pdf_folder()
            pdf_path = FileService.get_pdf_path(file_id)
            
            if not os.path.exists(pdf_path):
                logger.error(f"❌ PDF file not found: {pdf_path}")
                return False
            
            # Create FSInputFile for sending
            pdf_file = FSInputFile(pdf_path)
            
            # Send document to user
            await bot.send_document(
                chat_id=chat_id,
                document=pdf_file,
                caption=caption
            )
            
            logger.info(f"✅ PDF sent to user {chat_id}: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending PDF to user {chat_id}: {e}")
            return False
    
    @staticmethod
    def create_sample_pdf_files():
        """Create sample PDF files for testing"""
        try:
            FileService.ensure_pdf_folder()
            
            sample_files = {
                'sample_investment_guide': '📚 Основы инвестирования - руководство для начинающих',
                'sample_financial_course': '🎓 Финансовая грамотность - видео-курс материалы',
                'sample_excel_template': '📊 Шаблон Excel для учета финансов',
                'sample_exclusive_reports': '📈 Эксклюзивные аналитические отчеты'
            }
            
            for file_id, content in sample_files.items():
                pdf_path = FileService.get_pdf_path(file_id)
                
                if not os.path.exists(pdf_path):
                    # Create a simple text file as placeholder (in real app would be actual PDF)
                    with open(pdf_path, 'w', encoding='utf-8') as f:
                        f.write(f"=== {content} ===\n\n")
                        f.write("Это демонстрационный файл награды.\n")
                        f.write("В реальном приложении здесь был бы PDF файл с полезными материалами.\n\n")
                        f.write("Спасибо за использование нашего бота! 🎉")
                    
                    logger.info(f"✅ Created sample PDF: {file_id}")
            
            logger.info("✅ Sample PDF files created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating sample PDF files: {e}")
