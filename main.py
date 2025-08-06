import json
from queue import Queue
from datetime import datetime, timedelta
import time
import os
import sys
import random
import re, unicodedata
from config import *
from zlapi.models import *
from szl import CommandHandler
from zlapi import ZaloAPI
from colorama import Fore, Style, init
import logging
import threading
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pyfiglet

init(autoreset=True)

logger = logging.getLogger("ZaloBot")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

colors = [
    "FF9900", "FFFF33", "33FFFF", "FF99FF", "FF3366",
    "FFFF66", "FF00FF", "66FF99", "00CCFF", "FF0099",
    "FF0066", "0033FF", "FF9999", "00FF66", "00FFFF",
    "CCFFFF", "8F00FF", "FF00CC", "FF0000", "FF1100",
    "FF3300"
]

text = "OFF VNX"
Soizl = pyfiglet.figlet_format(text)
print(Soizl)

def hex_to_ansi(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'\033[38;2;{r};{g};{b}m'

class Client(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies, reset_interval=3600):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        self.command_handler = CommandHandler(self)
        self.group_info_cache = {}
        self.user_info_cache = {}
        self.session = requests.Session()
        self.message_queue = Queue()
        self.is_mute_list = {}
        self.last_sms_times = {}

        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        threading.Thread(target=self._process_command_queue, daemon=True).start()
        self.start_auto_welcome()

    def _get_user_name(self, user_id):
        if user_id in self.user_info_cache:
            return self.user_info_cache[user_id]
        try:
            info = self.fetchUserInfo(user_id).changed_profiles.get(user_id, {})
            name = info.get('zaloName', 'Không xác định')
            self.user_info_cache[user_id] = name
            return name
        except Exception:
            return 'Không xác định'

    def _get_group_name(self, group_id):
        if group_id in self.group_info_cache:
            return self.group_info_cache[group_id]
        try:
            info = self.fetchGroupInfo(group_id).gridInfoMap.get(group_id, {})
            name = info.get('name', 'N/A')
            self.group_info_cache[group_id] = name
            return name
        except Exception:
            return 'N/A'

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            message_text = message.text if isinstance(message, Message) else str(message)
            self.message_queue.put((message_text, author_id, message_object, thread_id, thread_type))
        except Exception as e:
            logger.error(f"Lỗi onMessage: {e}")

    def _process_command_queue(self):
        while True:
            try:
                message_text, author_id, message_object, thread_id, thread_type = self.message_queue.get()

                if str(thread_id) == "1382180422862516628":
                    current_time = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime())
                    colors_selected = random.sample(colors, 8)
                    author_name = self._get_user_name(author_id)
                    group_name = self._get_group_name(thread_id)

                    print(f"{hex_to_ansi(colors_selected[0])}{Style.BRIGHT}------------------------------{Style.RESET_ALL}")
                    print(f"{hex_to_ansi(colors_selected[1])}{Style.BRIGHT}- Message: {message_text}{Style.RESET_ALL}")
                    print(f"{hex_to_ansi(colors_selected[2])}{Style.BRIGHT}- ID NGƯỜI DÙNG: {author_id}{Style.RESET_ALL}")
                    print(f"{hex_to_ansi(colors_selected[6])}{Style.BRIGHT}- TÊN NGƯỜI DÙNG: {author_name}{Style.RESET_ALL}")
                    print(f"{hex_to_ansi(colors_selected[3])}{Style.BRIGHT}- ID NHÓM: {thread_id}{Style.RESET_ALL}")

                if self.is_mute_list.get(thread_id) and author_id in self.is_mute_list[thread_id]:
                    self.deleteGroupMsg(message_object.msgId, message_object.uidFrom, message_object.cliMsgId, thread_id)
                    continue

                self.command_handler.handle_command(message_text, author_id, message_object, thread_id, thread_type)

            except Exception as e:
                logger.error(f"Lỗi xử lý command trong queue: {e}")

    def start_auto_welcome(self):
        try:
            all_group = list(self.fetchAllGroups().gridVerMap.keys())
            self.group_info_cache = {}
            self._initialize_group_info(all_group)

            def loop():
                while True:
                    for tid in all_group:
                        self._handle_group_member(tid, ThreadType.GROUP)
                    time.sleep(3)

            threading.Thread(target=loop, daemon=True).start()
        except Exception as e:
            logger.error(f"Lỗi khởi động auto welcome: {e}")

    def _initialize_group_info(self, thread_ids):
        for tid in thread_ids:
            info = self.fetchGroupInfo(tid).gridInfoMap.get(tid)
            if info:
                self.group_info_cache[tid] = {
                    "name": info['name'],
                    "member_list": info['memVerList'],
                    "total_member": info['totalMember']
                }

    def _check_member_changes(self, tid):
        current = self.fetchGroupInfo(tid).gridInfoMap.get(tid)
        cached = self.group_info_cache.get(tid)
        if not current or not cached:
            return [], []
        old = set(m.split('_')[0] for m in cached['member_list'])
        new = set(m.split('_')[0] for m in current['memVerList'])
        joined = new - old
        left = old - new
        self.group_info_cache[tid] = {
            "name": current['name'],
            "member_list": current['memVerList'],
            "total_member": current['totalMember']
        }
        return joined, left

    def _handle_group_member(self, tid, ttype):
        joined, left = self._check_member_changes(tid)

        for mid in joined:
            try:
                info = self.fetchUserInfo(mid).changed_profiles[mid]
                cover = info.avatar
                filename = cover.rsplit("/", 1)[-1]
                res = requests.get(cover)
                if res.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(res.content)
                    msg = Message(text=f"🥳 Chào mừng {info.displayName} 🎉 đến {self.group_info_cache[tid]['name']}\nBạn là thành viên thứ {self.group_info_cache[tid]['total_member']}.")
                    self.sendLocalImage(filename, tid, ttype, message=msg, width=240, height=240)
                    try:
                        os.remove(filename)
                    except Exception as e:
                        logger.warning(f"Không thể xóa ảnh welcome {filename}: {e}")
                else:
                    self.send(Message(text=f"🥳 Chào mừng {info.displayName} 🎉 đến {self.group_info_cache[tid]['name']}\nBạn là thành viên thứ {self.group_info_cache[tid]['total_member']}."), tid, ttype)
            except Exception as e:
                logger.error(f"Lỗi khi chào mừng {mid}: {e}")

        for mid in left:
            try:
                info = self.fetchUserInfo(mid).changed_profiles[mid]
                cover = info.avatar
                filename = cover.rsplit("/", 1)[-1]
                res = requests.get(cover)
                if res.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(res.content)
                    msg = Message(text=f"💔 Tạm biệt {info.displayName} 🤧")
                    self.sendLocalImage(filename, tid, ttype, message=msg, width=240, height=240)
                    try:
                        os.remove(filename)
                    except Exception as e:
                        logger.warning(f"Không thể xóa ảnh tạm biệt {filename}: {e}")
                else:
                    self.send(Message(text=f"💔 Tạm biệt {info.displayName} 🤧"), tid, ttype)
            except Exception as e:
                logger.error(f"Lỗi khi chia tay {mid}: {e}")

if __name__ == "__main__":
    try:
        client = Client(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
        client.listen(thread=True)
    except Exception as e:
        logger.error(f"Lỗi khởi tạo client: {e}")
        time.sleep(10)