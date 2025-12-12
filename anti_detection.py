import random
import time
import logging

logger = logging.getLogger(__name__)

# قائمة شاملة من User-Agents الحقيقية
USER_AGENTS = [
    # Chrome على Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    
    # Firefox على Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Safari على Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    
    # Chrome على Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]

class AntiDetection:
    """تقنيات لتجنب اكتشاف البث على فيسبوك"""
    
    @staticmethod
    def get_random_user_agent():
        """الحصول على User-Agent عشوائي"""
        return random.choice(USER_AGENTS)
    
    @staticmethod
    def get_random_delay(min_seconds=2, max_seconds=8):
        """تأخير عشوائي قبل البث (محاكاة السلوك البشري)"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"⏳ تأخير عشوائي: {delay:.1f} ثانية (لتجنب الكشف)")
        time.sleep(delay)
    
    @staticmethod
    def get_obfuscated_bitrate():
        """معدل بت عشوائي لتجنب البصمة - مطابق للبث الناجح"""
        bitrates = ['3800k', '3900k', '4000k', '4100k', '4200k']
        return random.choice(bitrates)
    
    @staticmethod
    def get_random_buffer_size():
        """حجم التخزين المؤقت العشوائي - مطابق للبث الناجح"""
        sizes = ['6000k', '7000k', '8000k', '9000k']
        return random.choice(sizes)
    
    @staticmethod
    def get_random_gop():
        """حجم GOP عشوائي (Group of Pictures)"""
        gops = ['25', '30', '35']
        return random.choice(gops)
    
    @staticmethod
    def randomize_ffmpeg_params():
        """إرجاع معاملات FFmpeg عشوائية لتجنب البصمة"""
        return {
            'bitrate': AntiDetection.get_obfuscated_bitrate(),
            'bufsize': AntiDetection.get_random_buffer_size(),
            'gop': AntiDetection.get_random_gop(),
            'preset': random.choice(['ultrafast', 'superfast']),
            'user_agent': AntiDetection.get_random_user_agent()
        }

    @staticmethod
    def obfuscate_stream_headers():
        """رؤوس HTTP معدّلة لتجنب الكشف"""
        return {
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    @staticmethod
    def apply_stream_spacing():
        """إضافة فاصل زمني بين الحزم (تجنب البصمة)"""
        logger.info("🔄 تطبيق تقنيات تجنب الكشف المتقدمة...")
        time.sleep(random.uniform(1, 3))
