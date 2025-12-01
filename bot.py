
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import config
from stream import StreamManager
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# تفعيل السجلات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات الحوار
M3U8, KEY = range(2)

stream_manager = StreamManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية الحوار"""
    await update.message.reply_text(
        "👋 مرحباً بك في بوت البث المحسّن!\n\n"
        "🎯 الميزات:\n"
        "• إعادة اتصال تلقائية (50 محاولة)\n"
        "• حماية من الانقطاع\n"
        "• استقرار محسّن\n\n"
        "📋 الأوامر:\n"
        "/stream - بدء البث\n"
        "/stop - إيقاف البث\n"
        "/status - حالة البث\n"
        "/reset - إعادة تعيين (طوارئ)"
    )
    return ConversationHandler.END

async def start_stream_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """أمر بدء البث"""
    if stream_manager.process and stream_manager.process.poll() is None:
        await update.message.reply_text("⚠️ البث يعمل بالفعل! استخدم /stop لإيقافه أولاً.")
        return ConversationHandler.END
    
    stream_manager.is_running = False
    stream_manager.process = None

    await update.message.reply_text(
        "🚀 إعداد البث\n\n"
        "أرسل رابط M3U8 (مثال: https://...stream.m3u8)"
    )
    return M3U8

async def get_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال رابط M3U8"""
    context.user_data['m3u8'] = update.message.text
    await update.message.reply_text(
        "✅ تم استقبال الرابط.\n\n"
        "الآن أرسل مفتاح البث (Stream Key) من فيسبوك\n"
        "(مثال: FB-1234567...)"
    )
    return KEY

async def get_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال مفتاح البث"""
    m3u8 = context.user_data['m3u8']
    key = update.message.text.strip()
    
    if len(key) < 10:
        await update.message.reply_text("❌ Stream Key قصير جداً! تأكد من نسخه بالكامل.")
        return KEY
    
    await update.message.reply_text(
        "⏳ جاري الاتصال بفيسبوك...\n\n"
        "⚠️ تأكد من:\n"
        "• Stream Key جديد وصالح\n"
        "• صفحة البث مفتوحة في فيسبوك\n"
        "• الإنترنت متصل\n\n"
        "⏱️ انتظر 15 ثانية..."
    )
    
    rtmp = config.FACEBOOK_RTMP_URL
    success, msg = stream_manager.start_stream(m3u8, rtmp, key, logo_path="./static/logo.png")
    
    if success:
        await update.message.reply_text(
            f"{msg}\n\n"
            "📺 يمكنك الآن الذهاب لصفحة البث المباشر في فيسبوك.\n"
            "استخدم /stop لإيقاف البث."
        )
    else:
        await update.message.reply_text(msg)
    
    return ConversationHandler.END

async def stop_stream_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """أمر إيقاف البث"""
    success, msg = stream_manager.stop_stream()
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """التحقق من حالة البث"""
    status_msg = stream_manager.get_detailed_status()
    await update.message.reply_text(f"📊 حالة البث:\n\n{status_msg}")
    return ConversationHandler.END

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إعادة تعيين حالة البوت بالكامل"""
    stream_manager.is_running = False
    if stream_manager.process:
        try:
            if stream_manager.process.poll() is None:
                stream_manager.process.kill()
        except:
            pass
    stream_manager.process = None
    stream_manager.reconnect_attempts = 0
    
    await update.message.reply_text(
        "🔄 تم إعادة تعيين البوت بالكامل!\n\n"
        "يمكنك الآن بدء بث جديد باستخدام /stream"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء الحوار"""
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/preview':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            try:
                with open('templates/preview.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write(b'<h1>Preview Not Found</h1>')
        elif self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            import json
            size_value = 150
            if isinstance(config.LOGO_SIZE, str) and ':' in config.LOGO_SIZE:
                try:
                    size_value = int(config.LOGO_SIZE.split(':')[0])
                except:
                    pass
            else:
                try:
                    size_value = int(config.LOGO_SIZE)
                except:
                    pass
            
            opacity_value = 1.0
            try:
                opacity_value = float(config.LOGO_OPACITY)
            except:
                pass
            
            data = {
                'offset_x': config.LOGO_OFFSET_X,
                'offset_y': config.LOGO_OFFSET_Y,
                'size': size_value,
                'opacity': opacity_value
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif self.path.startswith('/static/'):
            file_path = self.path[1:]
            if os.path.exists(file_path):
                self.send_response(200)
                if file_path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    self.send_header('Content-type', 'image/jpeg')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server_daemon(port):
    """تشغيل Health Check Server في خيط منفصل"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.allow_reuse_address = True
        logger.info(f"✅ Health check server running on port {port}")
        logger.info("🎯 Server is ready!")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")

def run_bot_main():
    """تشغيل البوت في الـ Main Thread (العملية الرئيسية)"""
    try:
        application = Application.builder().token(config.BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("stream", start_stream_command)],
            states={
                M3U8: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_m3u8)],
                KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop_stream_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(conv_handler)

        logger.info("✅ Telegram Bot started successfully")
        application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def main() -> None:
    """تشغيل Health Check Server في الخلفية + البوت في Main Thread"""
    logger.info("🚀 Starting application...")
    
    PORT = int(os.getenv('PORT', 8000))
    
    # تشغيل Health Check Server في خيط منفصل (daemon)
    server_thread = threading.Thread(target=run_server_daemon, args=(PORT,), daemon=True)
    server_thread.start()
    logger.info("✅ Health check server thread started")
    
    # تشغيل البوت في الـ Main Thread (حل signal handling issues)
    run_bot_main()

if __name__ == "__main__":
    main()
