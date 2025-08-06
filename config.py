IMEI = "741d9fe8-4de7-4308-acaf-22ec65b77545-cd5d5f3ff8f374827248e13d2f7d64ca"
SESSION_COOKIES = {"_ga_1J0YGQPT22":"GS1.1.1736134473.1.1.1736134489.44.0.0","ZConsent":"timestamp=1750753531846&location=https://zalo.me/pc","_ga_RYD7END4JE":"GS2.2.s1750753529$o1$g1$t1750753532$j57$l0$h0","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8uyd--YdKrPXtMRwwxHIbQBVPZgeZat.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8uyd--YdKrPXtMRwwxHIbQBVPZgeZat.1","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8yvdkcgbKXSXZYPfQkRIn21DvMjg9f74OC.1","_gcl_au":"1.1.1346585653.1750810140","_fbp":"fb.1.1750810148372.504829801388556238","_ga_NVN38N77J3":"GS2.2.s1750815388$o1$g1$t1750818760$j58$l0$h0","_ga_E63JS7SPBL":"GS2.1.s1750921525$o3$g0$t1750921525$j60$l0$h0","_ga":"GA1.2.1937952902.1736134474","_zlang":"vn","_gid":"GA1.2.1707334653.1753946869","zpsid":"JIzQ.226205539.10.KlieIMryC3OEuqixONmmDXWFGWHVIW86M4a33qSsraEcJ8gBR7qVkWLyC3O","zpw_sek":"Gdmc.226205539.a0.GZGwFeFStehWGwM7ejpUYlZ-k-6Xvloyuhlru-cbbUtwjudQwPE9tENigSl2uUEe_lQKRFONxZ0-tTgb3xJUYW","app.event.zalo.me":"6903828000121994566"}
API_KEY = "api_key"
SECRET_KEY = "secret_key"
PREFIX = "/"






import re
import os
import json
SETTING_FILE= "setting.json"
#Không chỉnh sửa nếu bạn không có kinh nghiệm
def read_settings():
    """Đọc toàn bộ nội dung từ file JSON."""
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_settings(settings):
    """Ghi toàn bộ nội dung vào file JSON."""
    with open(SETTING_FILE, 'w', encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)


def is_admin(author_id):
    settings = read_settings()
    admin_bot = settings.get("admin_bot", [])
    if author_id in admin_bot:
        return True
    else:
        return False
def get_user_name_by_id(bot,author_id):
    try:
        user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
        return user
    except:
        return "Unknown User"

def handle_bot_admin(bot):
    settings = read_settings()
    admin_bot = settings.get("admin_bot", [])
    if bot.uid not in admin_bot:
        admin_bot.append(bot.uid)
        settings['admin_bot'] = admin_bot
        write_settings(settings)
        print(f"Đã thêm 👑{get_user_name_by_id(bot, bot.uid)} 🆔 {bot.uid} cho lần đầu tiên khởi động vào danh sách Admin 🤖BOT ✅")

settings= read_settings()
ADMIN = [settings.get("admin_bot", [])]