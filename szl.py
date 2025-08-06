import os
import importlib
import sys
import random
import time
import json
import datetime
import pytz
import logging
from zlapi.models import Message
from config import *

# Cấu hình logger thay cho logging_utils
logger = logging.getLogger("ZaloBot")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

settings = read_settings()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def prf():
    with open('setting.json', 'r') as f:
        return json.load(f).get('prefix', '')

class CommandHandler:
    def __init__(self, client):
        self.client = client
        self.szl = self.load_szl()
        self.noprefix_szl = self.load_noprefix_szl()

        if PREFIX == '':
            logger.info("Prefix hiện tại của bot là 'no prefix'")
        else:
            logger.info(f"Prefix hiện tại của bot là '{PREFIX}'")

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb_color):
        return '{:02x}{:02x}{:02x}'.format(*rgb_color)

    def generate_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def generate_gradient_colors(self, length, num_colors=5):
        random_colors = [self.generate_random_color() for _ in range(num_colors)]
        rgb_colors = [self.hex_to_rgb(color) for color in random_colors]
        colors = []

        for j in range(num_colors - 1):
            start_rgb = rgb_colors[j]
            end_rgb = rgb_colors[j + 1]
            segment_length = length // (num_colors - 1)
            for i in range(segment_length):
                interpolated_color = tuple(
                    int(start_rgb[k] + (end_rgb[k] - start_rgb[k]) * i / (segment_length - 1))
                    for k in range(3)
                )
                colors.append(self.rgb_to_hex(interpolated_color))
        return colors

    def create_rainbow_params(self, text, size=20):
        styles = []
        colors = self.generate_gradient_colors(len(text), num_colors=5)
        for i, color in enumerate(colors):
            styles.append({"start": i, "len": 1, "st": f"c_{color}"})
        return json.dumps({"styles": styles, "ver": 0})

    def sendMessageColor(self, text, thread_id, thread_type):
        style = self.create_rainbow_params(text)
        self.client.send(Message(text=text, style=style), thread_id, thread_type)

    def replyMessageColor(self, text, message_object, thread_id, thread_type):
        style = self.create_rainbow_params(text)
        self.client.replyMessage(Message(text=text, style=style), message_object, thread_id=thread_id, thread_type=thread_type, ttl=5000)

    def load_szl(self):
        szl = {}
        for filename in os.listdir('modules'):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'modules.{module_name}')
                    if hasattr(module, 'get_szl'):
                        szl.update(module.get_szl())
                except Exception as e:
                    logger.error(f"Lỗi tải module {module_name}: {e}")
            elif filename.endswith('.json'):
                try:
                    with open(f'modules/{filename}', 'r') as f:
                        data = json.load(f)
                        for cmd, content in data.items():
                            szl[cmd] = lambda *_: self.sendMessageColor(content, *_[-3], *_[-2])
                except Exception as e:
                    logger.error(f"Lỗi đọc JSON {filename}: {e}")
        return szl

    def load_noprefix_szl(self):
        szl = {}
        for filename in os.listdir('modules/noprefix'):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'modules.noprefix.{module_name}')
                    if hasattr(module, 'get_szl'):
                        szl.update(module.get_szl())
                except Exception as e:
                    logger.error(f"Lỗi tải noprefix {module_name}: {e}")
            elif filename.endswith('.json'):
                try:
                    with open(f'modules/noprefix/{filename}', 'r') as f:
                        data = json.load(f)
                        for cmd, content in data.items():
                            szl[cmd] = lambda *_: self.sendMessageColor(content, *_[-3], *_[-2])
                except Exception as e:
                    logger.error(f"Lỗi đọc JSON noprefix {filename}: {e}")
        return szl

    def handle_command(self, message, author_id, message_object, thread_id, thread_type):
        if message.lower() in ["hello", "hi", "hai", "chào", "xin chào", "chao", "hí", "híí", "hì", "hìì", "lô", "hii", "helo", "hê nhô"]:
            greetings = ["Tốt Lành 🥳", "Vui Vẻ 😄", "Hạnh Phúc ❤", "Yêu Đời 😘", "May Mắn 🍀", "Full Năng Lượng ⚡", "Tuyệt Vời 😁", "Tỉnh Táo 🤓", "Đầy Sức Sống 😽", "Nhiệt Huyết 🔥"]
            tz = pytz.timezone('Asia/Ho_Chi_Minh')
            hours = int(datetime.datetime.now(tz).strftime('%H%M'))

            session = "Đêm"
            if 301 <= hours <= 400: session = "Sáng Tinh Mơ"
            elif 401 <= hours <= 700: session = "Sáng Sớm"
            elif 701 <= hours <= 1000: session = "Sáng"
            elif 1001 <= hours <= 1200: session = "Trưa"
            elif 1201 <= hours <= 1700: session = "Chiều"
            elif 1701 <= hours <= 1800: session = "Chiều Tà"
            elif 1801 <= hours <= 2100: session = "Tối"

            greeting_text = random.choice(greetings)
            response_text = f"Xin chào! Chúc Bạn Một Buổi {session} {greeting_text}"

            self.client.replyMessage(Message(text=response_text), message_object, thread_id, thread_type)
            return

        noprefix_handler = self.noprefix_szl.get(message.lower())
        if noprefix_handler:
            noprefix_handler(message, message_object, thread_id, thread_type, author_id, self.client)
            return

        if not message.startswith(prf()):
            return

        command_name = message[len(prf()):].split(' ')[0].lower()
        handler = self.szl.get(command_name)

        if handler:
            handler(message, message_object, thread_id, thread_type, author_id, self.client)
        else:
            text = f"Không tìm thấy lệnh: '{command_name}'. Hãy dùng {prf()}menu để biết các lệnh có trên hệ thống."
            self.replyMessageColor(text, message_object, thread_id, thread_type)