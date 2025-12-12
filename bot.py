import logging
import os
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import config
from stream import StreamManager
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

M3U8, KEY = range(2)
stream_manager = StreamManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 مرحباً!\n\n"
        "📋 الأوامر:\n"
        "/stream - بدء البث\n"
        "/stop - إيقاف البث\n"
        "/status - حالة البث\n"
        "/reset - إعادة تعيين"
    )
    return ConversationHandler.END

async def start_stream_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if stream_manager.is_running:
        await update.message.reply_text("⚠️ البث يعمل! استخدم /stop أولاً.")
        return ConversationHandler.END
    
    await update.message.reply_text("🚀 أرسل رابط البث (M3U8 أو TS)")
    return M3U8

async def get_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['m3u8'] = update.message.text.strip()
    await update.message.reply_text("✅ تم.\n\nالآن أرسل Stream Key من فيسبوك")
    return KEY

async def get_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    m3u8 = context.user_data['m3u8']
    key = update.message.text.strip()
    
    if len(key) < 10:
        await update.message.reply_text("❌ Stream Key قصير! تأكد منه.")
        return KEY
    
    await update.message.reply_text("⏳ جاري الاتصال...")
    
    best_m3u8 = stream_manager.parse_m3u8_for_best_quality(m3u8)
    success, msg = stream_manager.start_stream(best_m3u8, key)
    
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def stop_stream_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _, msg = stream_manager.stop_stream()
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = stream_manager.get_detailed_status()
    await update.message.reply_text(f"📊 {msg}")
    return ConversationHandler.END

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    stream_manager.stop_stream()
    stream_manager.is_running = False
    await update.message.reply_text("🔄 تم إعادة التعيين!\n\nاستخدم /stream للبدء")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/' or self.path == '/preview':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                with open('templates/preview.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write(b'<h1>Bot Running</h1>')
        elif self.path.startswith('/static/'):
            file_path = self.path[1:]
            if os.path.exists(file_path):
                self.send_response(200)
                ct = 'image/png' if file_path.endswith('.png') else 'application/octet-stream'
                self.send_header('Content-type', ct)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server(port):
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        server.allow_reuse_address = True
        logger.info(f"✅ Server on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")

def run_bot():
    try:
        app = Application.builder().token(config.BOT_TOKEN).build()
        
        conv = ConversationHandler(
            entry_points=[CommandHandler("stream", start_stream_command)],
            states={
                M3U8: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_m3u8)],
                KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stop", stop_stream_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("reset", reset_command))
        app.add_handler(conv)
        
        logger.info("✅ Bot started")
        app.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def keep_alive():
    """منع Render من إيقاف الخدمة - ping كل 5 دقائق"""
    url = os.getenv('RENDER_EXTERNAL_URL', '')
    while True:
        time.sleep(300)
        if url:
            try:
                requests.get(f"{url}/health", timeout=10)
                logger.info("🔄 Keep-alive ping sent")
            except:
                pass

def main():
    logger.info("🚀 Starting...")
    PORT = int(os.getenv('PORT', 8000))
    
    t = threading.Thread(target=run_server, args=(PORT,), daemon=True)
    t.start()
    
    ka = threading.Thread(target=keep_alive, daemon=True)
    ka.start()
    
    run_bot()

if __name__ == "__main__":
    main()
