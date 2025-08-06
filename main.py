import os
import json
import re
import subprocess
import uuid
import threading
import time
import mimetypes
import requests
from urllib.parse import urlparse, parse_qs, unquote, urlencode
import pytz
import tempfile
import hashlib
import urllib.parse
import string
import random
from datetime import datetime, timedelta, date, timezone
from zlapi import ZaloAPI
from zlapi import *
from zlapi.models import *
from zlapi.models import Message, ThreadType
GPT_API_URL = 'https://gpt-3-5.apis-bj-devs.workers.dev/?prompt='
# Bot chính
class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.admin_ids = ['2198731144905101625', '413478823521301766']  # ID của admin
        self.user_cooldown = {}
        self.start_time = time.time()

    def get_nha_mang(self, phone):
        dau_so = phone[:3]
        return self.carrier_lookup.get(dau_so, "Không xác định")

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            self.markAsDelivered(mid, message_object.cliMsgId, author_id, thread_id, thread_type, message_object.msgType)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n========================= 📩 MESSAGE RECEIVED =========================")
            print(f"🕒 Thời gian: {timestamp}")
            print(f"📨 Thread: [{thread_type.name}] ID: {thread_id}")
            print(f"👤 Tác giả: {author_id}")
            print(f"💬 Nội dung: {message}\n")
            print("====================================================================\n")

            if not isinstance(message, str):
                print("⚠️ Tin nhắn không phải chuỗi, bỏ qua...")
                return

            self.handle_tt(message, message_object, thread_id, thread_type, author_id)
            self.handle_fb(message, message_object, thread_id, thread_type, author_id)
            self.handle_tiktok_download(message, message_object, thread_id, thread_type, author_id)
            self.handle_github(message, message_object, thread_id, thread_type, author_id)
            self.handle_2fa(message, message_object, thread_id, thread_type, author_id)
            self.handle_roblox(message, message_object, thread_id, thread_type, author_id)
            self.handle_kqxs(message_object, thread_id, thread_type, author_id)
            self.handle_qrcode(message, message_object, thread_id, thread_type, author_id)
            self.handle_start(message_object, thread_id, thread_type, author_id)
            self.handle_qrbank(message, message_object, thread_id, thread_type, author_id)
            self.handle_ngl(message, message_object, thread_id, thread_type, author_id)
            self.handle_ask(message, message_object, thread_id, thread_type, author_id)
            self.handle_ip(message, message_object, thread_id, thread_type, author_id)
            self.handle_info(message, message_object, thread_id, thread_type, author_id)
            self.handle_thoitiet(message, message_object, thread_id, thread_type, author_id)
            self.handle_anhgai(message_object, thread_id, thread_type, author_id)
            self.handle_reghotmail(message_object, thread_id, thread_type, author_id)
            self.handle_reggarena(message_object, thread_id, thread_type, author_id)
            self.handle_ytb(message_object, thread_id, thread_type, author_id)
            self.handle_zingmp3(message_object, thread_id, thread_type, author_id)

        except Exception as e:
            print(f"❌ Lỗi trong onMessage: {e}")
          
# zing mp3
    def handle_zingmp3(self, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return
        if not message_object.content.startswith("/zingmp3"):
            return

        try:
            keyword = message_object.content.split(" ", 1)[1].strip()
        except IndexError:
            self.send(
                Message(text="❌ Vui lòng nhập tên bài hát hoặc album để tìm kiếm. Ví dụ:\n/zingmp3 cơn mưa ngang qua"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        api_url = f"https://keyherlyswar.x10.mx/Apidocs/searchzing.php?q={keyword}"

        try:
            res = requests.get(api_url, timeout=15)
            data = res.json()

            items = data.get("featured", {}).get("data", {}).get("items", [])
            if not items or not items[0]["items"]:
                self.send(
                    Message(text=f"❌ Không tìm thấy kết quả cho: {keyword}"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            result = items[0]["items"][0]

            title = result.get("title", "Không rõ")
            artist = result.get("artists", [{}])[0].get("name", "Không rõ")
            release = result.get("releaseDate", "Không rõ")
            link = result.get("link", "")
            thumb = result.get("thumb", "")

            reply = (
                f"🎵 Kết quả tìm kiếm Zing MP3:\n\n"
                f"🔹 Bài hát/Album: {title}\n"
                f"🎤 Ca sĩ: {artist}\n"
                f"📅 Phát hành: {release}\n"
                f"🔗 Link nghe: {link}"
            )

            if thumb:
                image_response = requests.get(thumb, stream=True)
                image_path = f"temp_zingmp3_{author_id}.jpg"
                with open(image_path, 'wb') as f:
                    for chunk in image_response.iter_content(1024):
                        f.write(chunk)

                self.sendLocalImage(
                    image_path,
                    message=Message(text=reply),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                os.remove(image_path)
            else:
                self.send(
                    Message(text=reply),
                    thread_id=thread_id,
                    thread_type=thread_type
                )

        except Exception as e:
            self.send(
                Message(text=f"❌ Đã xảy ra lỗi khi tìm kiếm ZingMP3:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
# youtube
    def handle_ytb(self, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return
        if not message_object.content.startswith("/ytb"):
            return

        try:
            username = message_object.content.split(" ", 1)[1].strip()
        except IndexError:
            self.send(
                Message(text="❌ Vui lòng nhập username kênh YouTube. Ví dụ:\n/ytb duonghungduonghoang"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        api_url = f"https://keyherlyswar.x10.mx/Apidocs/getinfoyt.php?username={username}"

        try:
            res = requests.get(api_url, timeout=15)
            data = res.json()

            if "channelInfo" not in data:
                self.send(
                    Message(text="❌ Không thể lấy thông tin kênh. Username sai hoặc lỗi API."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            info = data["channelInfo"]
            title = info.get("title", "Không rõ")
            channel_id = info.get("channelId", "Không rõ")
            description = info.get("description", "Không có mô tả").strip()
            subs = info.get("subscriberCountText", "Không rõ")
            videos = info.get("videosCountText", "Không rõ")
            views = info.get("viewCountText", "Không rõ")
            country = info.get("country", "Không rõ")
            joined = info.get("joinedDate", None)
            avatar_url = info.get("avatar", [{}])[-1].get("url", "")

            if joined:
                dt = datetime.strptime(joined, "%Y-%m-%d")
                joined_text = f"{dt.strftime('%d/%m/%Y')}"
            else:
                joined_text = "Không rõ thời gian tham gia"

            reply = (
                f"📺 Thông tin kênh YouTube:\n\n"
                f"👤 Tên kênh: {title}\n"
                f"🆔 ID kênh: {channel_id}\n"
                f"🌏 Quốc gia: {country}\n"
                f"📅 Ngày tạo: {joined_text}\n"
                f"👥 Số người theo dõi: {subs}\n"
                f"🎥 Số video: {videos}\n"
                f"👁️ Tổng lượt xem: {views}\n"
                f"📖 Mô tả: {description[:500]}{'...' if len(description) > 500 else ''}"
            )

            if avatar_url:
                image_response = requests.get(avatar_url, stream=True)
                image_path = f"temp_avatar_{author_id}.jpg"
                with open(image_path, 'wb') as f:
                    for chunk in image_response.iter_content(1024):
                        f.write(chunk)

                self.sendLocalImage(
                    image_path,
                    message=Message(text=reply),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                os.remove(image_path)
            else:
                self.send(
                    Message(text=reply),
                    thread_id=thread_id,
                    thread_type=thread_type
                )

        except Exception as e:
            self.send(
                Message(text=f"❌ Đã xảy ra lỗi khi lấy thông tin kênh:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
#reg garena
    def handle_reggarena(self, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return
        if not message_object.content.startswith("/reggarena"):
            return

        try:
            res = requests.get("https://keyherlyswar.x10.mx/Apidocs/reglq.php", timeout=15)
            data = res.json()

            if res.status_code != 200 or not data.get("status") or not data.get("result"):
                self.send(
                    Message(text="❌ Không thể tạo tài khoản Garena. Vui lòng thử lại sau."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            account_info = data["result"][0]
            username = account_info["account"]
            password = account_info["password"]

            reply = (
                "🎮 Tài khoản Garena đã được tạo:\n\n"
                f"👤 Tên đăng nhập: {username}\n"
                f"🔑 Mật khẩu: {password}\n"
                "⚠️ Hãy đổi mật khẩu sau khi đăng nhập!"
            )

            self.send(
                Message(text=reply),
                thread_id=thread_id,
                thread_type=thread_type
            )

        except requests.exceptions.RequestException as e:
            self.send(
                Message(text=f"❌ Lỗi kết nối API Garena:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
        except Exception as e:
            self.send(
                Message(text=f"❌ Lỗi không xác định khi tạo tài khoản Garena:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
#reg hotmail
    def handle_reghotmail(self, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return
        if not message_object.content.startswith("/reghotmail"):
            return

        try:
            res = requests.get("https://keyherlyswar.x10.mx/Apidocs/reghotmail.php", timeout=15)
            data = res.json()

            if res.status_code != 200 or not data.get("status") or "result" not in data:
                self.send(
                    Message(text="❌ Không thể tạo tài khoản Hotmail. Vui lòng thử lại sau."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            email = data["result"]["email"]
            password = data["result"]["password"]

            reply = (
                "📧 Tài khoản Hotmail mới đã được tạo:\n\n"
                f"🔹 Email: {email}\n"
                f"🔑 Mật khẩu: {password}\n"
                "⚠️ Vui lòng lưu lại thông tin này!"
            )

            self.send(
                Message(text=reply),
                thread_id=thread_id,
                thread_type=thread_type
            )

        except requests.exceptions.RequestException as e:
            self.send(
                Message(text=f"❌ Lỗi kết nối API Hotmail:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
        except Exception as e:
            self.send(
                Message(text=f"❌ Lỗi không xác định khi tạo Hotmail:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
#anhgai
    def handle_anhgai(self, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return
        if not message_object.content.startswith("/anhgai"):
            return

        try:
            res = requests.get("https://nguyenmanh.name.vn/api/world/vietnam", timeout=10)
            data = res.json()

            if res.status_code != 200 or "url" not in data:
                self.send(
                    Message(text="❌ Không thể lấy ảnh. Vui lòng thử lại sau."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            image_url = data["url"]
            # Tải ảnh về
            image_response = requests.get(image_url, stream=True)
            image_path = "temp_anhgai.jpg"
            with open(image_path, 'wb') as f:
                for chunk in image_response.iter_content(1024):
                    f.write(chunk)

            if os.path.exists(image_path):
                self.sendLocalImage(
                    image_path,
                    message=Message(text=f"📸 Ảnh gái xinh 🇻🇳"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                os.remove(image_path)
            else:
                self.send(
                    Message(text="❌ Lỗi khi tải ảnh về."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )

        except requests.exceptions.RequestException as e:
            self.send(
                Message(text=f"❌ Lỗi khi kết nối API ảnh gái:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
        except Exception as e:
            self.send(
                Message(text=f"❌ Lỗi không xác định khi xử lý ảnh gái:\n{str(e)}"),
                thread_id=thread_id,
                thread_type=thread_type
            )

#thoitiet
    def format_weather(self, data):
        try:
            msg = f"🌦 {data['city_display']} | {data['description']}\n"
            msg += f"🌡 Nhiệt độ: {data['temperature']}°C (cảm giác như {data['feels_like']}°C)\n"
            msg += f"⬆️ Max: {data['temp_max']}°C\n"
            msg += f"⬇️ Min: {data['temp_min']}°C\n"
            msg += f"💧 Độ ẩm: {data['humidity']}%\n"
            msg += f"🍃 Áp suất: {data['pressure']} hPa\n"
            msg += f"☁️ Mây: {data['clouds']}%\n"
            msg += f"💨 Gió: {data['wind_speed']} m/s, hướng {data['wind_deg']}°\n"
            msg += f"👁️ Tầm nhìn: {data['visibility_km']} km\n"
            if data.get('rain_1h'):
                msg += f"🌧️ Mưa (1h): {data['rain_1h']} mm\n"
            if data.get('snow_1h'):
                msg += f"❄️ Tuyết (1h): {data['snow_1h']} mm\n"
            if data.get('aqi'):
                msg += f"☄️ Chất lượng không khí (AQI): {data['aqi']}/5\n"
            if data.get('uv_index'):
                msg += f"☀️ Chỉ số UV: {data['uv_index']} ({data['uv_level']})\n"
            msg += f"🌅 Mặt trời mọc: {data['sunrise']}\n"
            msg += f"🌇 Mặt trời lặn: {data['sunset']}\n"
            msg += f"🗺 Vị trí bản đồ: {data['location_url']}"
            return msg
        except Exception as e:
            return f"❌ Lỗi định dạng dữ liệu: {e}"

    def handle_thoitiet(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/thoitiet'):
            return

        args = message.strip().split(maxsplit=1)
        if len(args) < 2:
            self.send(
                Message(text="📝 Dùng: /thoitiet [tên thành phố]"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        city = args[1].strip()
        try:
            url = f"https://offvnx.x10.bz/api/thoitiet.php?city={city}"
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                self.send(
                    Message(text="❌ Không thể truy cập API thời tiết."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            data = res.json()
            if not data or "city" not in data:
                self.send(
                    Message(text=f"❌ Không tìm thấy thông tin thời tiết cho '{city}'."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            msg = self.format_weather(data)
            self.send(
                Message(text=msg.strip()),
                thread_id=thread_id,
                thread_type=thread_type
            )

        except Exception as e:
            self.send(
                Message(text=f"❌ Lỗi khi xử lý dữ liệu: {e}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
#info
    def get_user_data(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {'balance': 0, 'wins': 0, 'losses': 0}
        return self.user_data[user_id]

    def fetchUserInfo(self, userId):
        try:
            user_info = super().fetchUserInfo(userId)
            if 'changed_profiles' in user_info and userId in user_info['changed_profiles']:
                return user_info['changed_profiles'][userId]
            return {}
        except Exception as e:
            print(f"{Fore.RED}Error fetching user info: {e}")
            return {}

    def calculate_age(self, birthdate_str):
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
        for fmt in formats:
            try:
                birthdate = datetime.strptime(birthdate_str, fmt)
                today = date.today()
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                return age
            except:
                continue
        return "Chưa rõ tuổi"

    def format_timestamp(self, ts):
        try:
            return datetime.fromtimestamp(ts, timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
        except:
            return "Không rõ"

    def mask_phone(self, phone):
        if not phone or len(phone) < 6:
            return "Ẩn"
        return phone[:3] + '******' + phone[-2:]

    def format_usage_duration(self, created_ts):
        try:
            days_total = (date.today() - datetime.fromtimestamp(created_ts, timezone.utc).date()).days
            years = days_total // 365
            days = days_total % 365
            if years > 0:
                return f"{years} năm {days} ngày"
            else:
                return f"{days} ngày"
        except:
            return "Không rõ"

    def handle_info(self, message, message_object, thread_id, thread_type, author_id):
        if hasattr(message_object, 'content') and isinstance(message_object.content, str):
            if message_object.content.startswith('/info'):
                try:
                    target_user_id = (
                        message_object.mentions[0]['uid']
                        if 'mentions' in message_object and message_object.mentions
                        else author_id
                    )

                    profile = self.fetchUserInfo(target_user_id)
                    if not profile:
                        self.send(
                            Message(text="❌ Không tìm thấy thông tin người dùng."),
                            thread_id=thread_id,
                            thread_type=ThreadType.GROUP
                        )
                        return

                    zalo_name = profile.get('zaloName', 'Không rõ')
                    phone = self.mask_phone(profile.get('phoneNumber', 'Ẩn'))
                    dob = profile.get('sdob', '')
                    created_ts = profile.get('createdTs', 0)
                    user_id = profile.get('userId', target_user_id)
                    avatar_url = profile.get('avatar', '')
                    cover_url = profile.get('cover', '')
                    username = profile.get('username', 'Không có')
                    status = profile.get('status', 'Không có')

                    age_text = self.calculate_age(dob) if dob else "Chưa rõ tuổi"
                    usage_duration = (
                        self.format_usage_duration(created_ts)
                        if created_ts else "Không rõ"
                    )
                    created_date = self.format_timestamp(created_ts) if created_ts else "Không rõ"

                    info_text = (
                        f"👤 Thông tin người dùng:\n"
                        f"🔑 User ID: {user_id}\n"
                        f"👥 Tên Zalo: {zalo_name}\n"
                        f"🆔 Username: {username}\n"
                        f"📞 SĐT: {phone}\n"
                        f"📅 Ngày sinh: {dob} (Tuổi: {age_text})\n"
                        f"📝 Status: {status}\n"
                        f"📈 Thời gian sử dụng: {usage_duration}\n"
                        f"🗓️ Ngày tạo tài khoản: {created_date}"
                    )

                    # Gửi thông tin + avatar nếu có
                    if avatar_url and avatar_url.startswith("http"):
                        avatar_path = 'temp_avatar.jpg'
                        try:
                            res = requests.get(avatar_url, timeout=5)
                            with open(avatar_path, 'wb') as f:
                                f.write(res.content)
                            self.sendLocalImage(
                                avatar_path,
                                message=Message(text=info_text),
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP
                            )
                            os.remove(avatar_path)
                        except Exception as e:
                            print(f"[ẢNH] Lỗi tải avatar: {e}")
                            self.send(
                                Message(text=info_text + f"\n🖼️ Avatar: {avatar_url}"),
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP
                            )
                    else:
                        self.send(
                            Message(text=info_text + "\n🖼️ Avatar: Không có"),
                            thread_id=thread_id,
                            thread_type=ThreadType.GROUP
                        )

                    # Gửi ảnh bìa (cover) riêng nếu có
                    if cover_url and cover_url.startswith("http"):
                        cover_path = 'temp_cover.jpg'
                        try:
                            res = requests.get(cover_url, timeout=5)
                            with open(cover_path, 'wb') as f:
                                f.write(res.content)
                            self.sendLocalImage(
                                cover_path,
                                message=Message(text="🌄 Ảnh bìa:"),
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP
                            )
                            os.remove(cover_path)
                        except Exception as e:
                            print(f"[ẢNH] Lỗi tải cover: {e}")
                            self.send(
                                Message(text=f"🌄 Cover: {cover_url}"),
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP
                            )
                    else:
                        self.send(
                            Message(text="🌄 Cover: Không có"),
                            thread_id=thread_id,
                            thread_type=ThreadType.GROUP
                        )

                except Exception as e:
                    print(f"[ERROR] /info command: {e}")
#ip
    def get_ip_info(self, ip):
        url = f"https://ip-info.bjcoderx.workers.dev/?ip={requests.utils.quote(ip)}"
        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception:
            return None

    def handle_ip(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/ip'):
            return

        args = message.strip().split(' ', 1)
        if len(args) < 2:
            self.send(
                Message(text="❌ Vui lòng nhập địa chỉ IP.\nVí dụ: /ip 14.191.136.129"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        ip = args[1].strip()
        data = self.get_ip_info(ip)

        if not data or "ip" not in data:
            self.send(
                Message(text="⚠️ Không thể lấy thông tin IP. Vui lòng thử lại sau."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        def get_val(obj, key, default=""):
            return obj.get(key, default) if obj else default

        tz = get_val(data, 'time_zone')
        currency = get_val(data, 'currency')

        info = f"""
📡 THÔNG TIN IP
──────────────
🌐 IP: {get_val(data, 'ip')}
🗺 Châu lục: {get_val(data, 'continent_name')} ({get_val(data, 'continent_code')})
🏳 Quốc gia: {get_val(data, 'country_name')} ({get_val(data, 'country_code2')}) {get_val(data, 'country_emoji')}
🏙 Thành phố: {get_val(data, 'city')}
📍 Bang/Tỉnh: {get_val(data, 'state_prov')}
🏞 Quận/Huyện: {get_val(data, 'district')}
🧭 Vĩ độ: {get_val(data, 'latitude')}
🧭 Kinh độ: {get_val(data, 'longitude')}
🕐 Múi giờ: {get_val(tz, 'name')} (UTC{get_val(tz, 'offset')})
🕓 Giờ hiện tại: {get_val(tz, 'current_time')}
💰 Tiền tệ: {get_val(currency, 'name')} ({get_val(currency, 'symbol')})
📡 ISP: {get_val(data, 'isp')}
🏢 Tổ chức: {get_val(data, 'organization')}
🏴‍☠️ Quốc kỳ: {get_val(data, 'country_flag')}
📌 Geo Name ID: {get_val(data, 'geoname_id')}
🔤 Ngôn ngữ: {get_val(data, 'languages')}
🏛 Thủ đô: {get_val(data, 'country_capital')}
🏷 Mã ZIP: {get_val(data, 'zipcode')}
📞 Mã gọi quốc gia: +{get_val(data, 'calling_code')}
📝 Quốc gia chính thức: {get_val(data, 'country_name_official')}
──────────────
""".strip()

        self.send(
            Message(text=info),
            thread_id=thread_id,
            thread_type=thread_type
        ) 

    def handle_ask(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/ask'):
            return

        query = message_object.content[len('/ask'):].strip()

        if not query:
            self.send(
                Message(text="⚠️ Vui lòng nhập nội dung sau lệnh /ask."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        try:
            res = requests.get(GPT_API_URL + requests.utils.quote(query), timeout=10)
            if res.status_code == 200:
                data = res.json()
                reply = data.get('reply', '🤖 Không có phản hồi từ GPT.')
                response_text = f"🤖 GPT trả lời:\n\n💬 {reply}"
            else:
                response_text = "🚫 API không phản hồi hợp lệ."

        except Exception as e:
            response_text = f"❌ Lỗi khi xử lý: {str(e)}"

        self.send(
            Message(text=response_text),
            thread_id=thread_id,
            thread_type=thread_type
        )
#ngl
    def generate_device_id():
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=26))

    def handle_ngl(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/ngl'):
            return

        args = message.strip().split(" ", 3)
        if len(args) < 4:
            self.send(Message(
                text="❌ Cú pháp sai!\n\nDùng đúng: /ngl username số_lượng \"nội_dung\""
            ), thread_id, thread_type)
            return

        username = args[1].strip()
        try:
            sl = int(args[2])
            if sl < 1 or sl > 20:
                self.send(Message(text="⚠️ Số lượng chỉ từ 1 đến 20!"), thread_id, thread_type)
                return
        except:
            self.send(Message(text="⚠️ Số lượng phải là số nguyên!"), thread_id, thread_type)
            return

        question = args[3].strip()

        now = datetime.now()
        if author_id in self.user_cooldown and now < self.user_cooldown[author_id]:
            remaining = (self.user_cooldown[author_id] - now).seconds
            self.send(Message(text=f"⏳ Vui lòng chờ {remaining} giây để dùng lại /ngl"), thread_id, thread_type)
            return

        self.user_cooldown[author_id] = now + timedelta(seconds=30)

        url = "https://ngl.link/api/submit"
        self.send(Message(text=f"🚀 Đang gửi {sl} câu hỏi đến @{username}..."), thread_id, thread_type)

        success, failed = 0, 0
        details = ""

        for i in range(1, sl + 1):
            device_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=26))
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://ngl.link',
                'referer': f'https://ngl.link/{username}',
                'x-requested-with': 'XMLHttpRequest'
            }
            payload = {
                "username": username,
                "question": question,
                "deviceId": device_id,
                "gameSlug": "",
                "referrer": ""
            }
            try:
                response = requests.post(url, headers=headers, data=urlencode(payload, encoding='utf-8'))
                if response.status_code == 200:
                    success += 1
                    details += f"✅ [{i}/{sl}] Thành công\n"
                else:
                    failed += 1
                    details += f"❌ [{i}/{sl}] Lỗi {response.status_code}\n"
            except:
                failed += 1
                details += f"❌ [{i}/{sl}] Gửi thất bại!\n"

            time.sleep(random.uniform(0.6, 1.5))

        self.send(Message(
            text=(
                f"🎯 Gửi đến @{username} hoàn tất\n"
                f"📬 Tổng cộng: {sl} câu hỏi\n"
                f"✅ Thành công: {success}\n"
                f"❌ Thất bại: {failed}\n\n"
                f"📄 Chi tiết:\n{details}"
            )
        ), thread_id, thread_type)
#qrbank
    BANK_LIST = [
        "mbbank", "dongabank", "vietinbank", "vietcombank", "techcombank",
        "bidv", "acb", "sacombank", "vpbank", "agribank",
        "hdbank", "tpbank", "shb", "eximbank", "ocb",
        "seabank", "bacabank", "pvcombank", "scb", "vib",
        "namabank", "abbank", "lpbank", "vietabank", "msb",
        "nvbank", "pgbank", "publicbank", "cimbbank", "uob"
    ]
    def handle_qrbank(self, message_text, message_object, thread_id, thread_type, author_id):
        if not message_text.startswith("/qrbank"):
            return

        args = message_text.strip().split(maxsplit=5)
        if len(args) < 3:
            self.send(
                Message(text=(
                    "❌ Cú pháp sai!\n"
                    "📌 Dùng: /qrbank [STK] [BANK] [Số tiền] [Tên người nhận] [Nội dung CK]\n"
                    "💡 Ví dụ:\n"
                    "/qrbank 123456789 mbbank 50000 NguyenVanA Thanh toan don hang"
                )),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        stk = args[1].strip()
        bank = args[2].lower().strip()
        amount = args[3].strip() if len(args) > 3 else ""
        account_name = args[4].strip() if len(args) > 4 else ""
        add_info = args[5].strip() if len(args) > 5 else ""

        if not stk.isdigit():
            self.send(Message(text="🔢 Số tài khoản phải là số!"), thread_id=thread_id, thread_type=thread_type)
            return

        if bank not in self.BANK_LIST:
            suggestions = [b for b in self.BANK_LIST if bank in b]
            suggest_text = "\n🔎 Có phải bạn muốn:\n" + "\n".join(f"👉 `{s}`" for s in suggestions[:3]) if suggestions else ""
            self.send(Message(text=f"❌ Mã ngân hàng `{bank}` không hợp lệ.{suggest_text}"), thread_id=thread_id, thread_type=thread_type)
            return

        params = {
            "amount": amount,
            "addInfo": add_info,
            "accountName": account_name
        }
        query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        qr_url = f"https://img.vietqr.io/image/{bank}-{stk}-RegCr8p.png"
        if query_string:
            qr_url += f"?{query_string}"

        try:
            resp = requests.get(qr_url, timeout=10)
            if resp.status_code != 200 or not resp.content.startswith(b"\x89PNG"):
                self.send(Message(text="⚠️ Không thể tạo QR. Kiểm tra lại thông tin nhập vào!"), thread_id=thread_id, thread_type=thread_type)
                return

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(resp.content)
                file_path = tmp.name

            info = (
                "✅ QR ĐÃ TẠO THÀNH CÔNG\n\n"
                f"🏦 Ngân hàng: {bank.upper()}\n"
                f"🔢 STK: {stk}\n"
                f"👤 Người nhận: {account_name or 'Không rõ'}\n"
                f"💵 Số tiền: {amount or 'Không có'}\n"
                f"📝 Nội dung: {add_info or 'Không có'}\n\n"
                "📲 Dùng app ngân hàng để quét mã QR và chuyển tiền!"
            )
            self.sendLocalImage(file_path, message=Message(text=info), thread_id=thread_id, thread_type=thread_type)
            os.remove(file_path)

        except Exception as e:
            self.send(Message(text=f"🚫 Lỗi tạo QR:\n```{e}```"), thread_id=thread_id, thread_type=thread_type)

#qrcode
    def handle_qrcode(self, message, message_object, thread_id, thread_type, author_id):
        if hasattr(message_object, 'content') and isinstance(message_object.content, str):
            if message_object.content.startswith('/qrcode'):
                parts = message.split(maxsplit=1)

                if len(parts) < 2 or not parts[1].strip():
                    self.send(
                        Message(text="⚠️ Vui lòng nhập nội dung để tạo mã QR.\n\n📌 Ví dụ: /qrcode Hello Zalo!"),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return

                content = parts[1].strip()
                encoded_text = urllib.parse.quote(content, safe='')

                # Tạo màu ngẫu nhiên
                r = random.randint(50, 200)
                g = random.randint(50, 200)
                b = random.randint(50, 200)
                color_param = f"{r}-{g}-{b}"

                try:
                    api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=1600x1600&data={encoded_text}&color={color_param}"
                    image_response = requests.get(api_url)
                    image_path = 'temp_qrcode.jpg'

                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)

                    if os.path.exists(image_path):
                        self.sendLocalImage(
                            image_path,
                            message=Message(text=f"✅ Mã QR đã tạo\n\n📄 Nội Dung: {content}"),
                            thread_id=thread_id,
                            thread_type=thread_type,
                            width=1600,
                            height=1600
                        )
                        os.remove(image_path)

                except requests.exceptions.RequestException as e:
                    self.send(Message(text=f"❌ Lỗi khi gọi API QR: {str(e)}"), thread_id=thread_id, thread_type=thread_type)
                except Exception as e:
                    self.send(Message(text=f"❌ Lỗi không xác định: {str(e)}"), thread_id=thread_id, thread_type=thread_type)

#start
    def format_timestamp(self, ts):
        try:
            vn_tz = timezone(timedelta(hours=7))
            dt = datetime.fromtimestamp(ts, vn_tz)
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            return "Không rõ"

    def handle_start(self, message_object, thread_id, thread_type, author_id):
        if hasattr(message_object, 'content') and message_object.content.startswith('/start'):
            now = self.format_timestamp(time.time())
            started_at = self.format_timestamp(self.start_time)

            uptime_sec = int(time.time() - self.start_time)
            days, rem = divmod(uptime_sec, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)

            uptime_parts = []
            if days > 0:
                uptime_parts.append(f"{days} ngày")
            if hours > 0:
                uptime_parts.append(f"{hours} giờ")
            if minutes > 0:
                uptime_parts.append(f"{minutes} phút")
            uptime_parts.append(f"{seconds} giây")
            uptime_str = ' '.join(uptime_parts)

            instructions = f"""
📑 DANH SÁCH LỆNH HỖ TRỢ
━━━━━━━━━━━━━━━━━━
📅 Ngày giờ: {now}
🚀 Bot khởi động từ: {started_at}
⏱️ Uptime: {uptime_str}
━━━━━━━━━━━━━━━━━━
➜ 🏠 /start - Hiển thị bảng điều khiển
➜ 🎧 /zingmp3 - Tìm kiếm nhạc Zing Mp3
➜ 🎬 /ytb - Check Info Kênh Youtube
➜ 📧 /reghotmail - Reg Tài khoản Hotmail
➜ 🎮 /reggarena - Reg Tài khoản Garena
➜ 👧 /anhgai - Random ảnh gái xinh
➜ 🎰 /kqxs - Xổ số
➜ 🙋 /info - Thông tin người dùng
➜ 🎵 /tiktok - Tải video không logo
➜ 🔍 /tt <username> - Info TikTok
➜ 📘 /fb <uid/link> - Info Facebook
➜ 🔐 /2fa - Mã 2FA
➜ 📩 /ngl - Spam NGL
➜ 🎮 /roblox - Info Roblox
➜ 🤖 /ask - ChatGPT
➜ 🌦️ /thoitiet <tỉnh/thành>
➜ 💻 /github - Info GitHub
➜ 🏦 /qrbank - QR Chuyển khoản
➜ 📷 /qrcode <text> - QR văn bản
━━━━━━━━━━━━━━━━━━
"""
            self.send(Message(text=instructions), thread_id=thread_id, thread_type=thread_type)

            # Gửi reaction emoji (không gửi ảnh)
            reactions = [
        "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀",
        "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀",
        "🎉", "🦁", "🌈", "🍎", "⚡", "🔔", "🎸", "🍕",
        "🏆", "📚", "🦋", "🌍", "⛄", "🎁", "💡", "🐾",
        "😺", "🐶", "🐳", "🦄", "🌸", "🍉", "🍔", "🎄",
        "🎃", "👻", "☃️", "🌴", "🏀", "⚽", "🎾", "🏈",
        "🚗", "✈️", "🚢", "🌙", "☀️", "⭐", "⛅", "☔",
        "⌛", "⏰", "💎", "💸", "📷", "🎥", "🎤", "🎧",
        "🍫", "🍰", "🍩", "☕", "🍵", "🍷", "🍹", "🥐",
        "🐘", "🦒", "🐍", "🦜", "🐢", "🦀", "🐙", "🦈",
        "🍓", "🍋", "🍑", "🥥", "🥐", "🥪", "🍝", "🍣",
        "🎲", "🎯", "🎱", "🎮", "🎰", "🧩", "🧸", "🎡",
        "🏰", "🗽", "🗼", "🏔️", "🏝️", "🏜️", "🌋", "⛲",
        "📱", "💻", "🖥️", "🖨️", "⌨️", "🖱️", "📡", "🔋",
        "🔍", "🔎", "🔑", "🔒", "🔓", "📩", "📬", "📮",
        "💢", "💥", "💫", "💦", "💤", "🚬", "💣", "🔫",
        "🩺", "💉", "🩹", "🧬", "🔬", "🔭", "🧪", "🧫",
        "🧳", "🎒", "👓", "🕶️", "👔", "👗", "👠", "🧢",
        "🦷", "🦴", "👀", "👅", "👄", "👶", "👩", "👨",
        "🚶", "🏃", "💃", "🕺", "🧘", "🏄", "🏊", "🚴",
        "🍄", "🌾", "🌻", "🌵", "🌿", "🍂", "🍁", "🌊",
        "🛠️", "🔧", "🔨", "⚙️", "🪚", "🪓", "🧰", "⚖️",
        "🧲", "🪞", "🪑", "🛋️", "🛏️", "🪟", "🚪", "🧹"
            ]
            self.sendReaction(message_object, random.choice(reactions), thread_id, thread_type)

#github
    def handle_github(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/github'):
            return

        parts = message.strip().split(maxsplit=1)
        if len(parts) < 2:
            self.send(
                Message(text="❌ Vui lòng cung cấp tên người dùng GitHub sau lệnh /github."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        username = parts[1]
        url = f"https://api.github.com/users/{username}"
        headers = {'User-Agent': 'request'}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                info = (
                    f"🔍 Thông tin GitHub của {username}:\n\n"
                    f"👤 Tên đăng nhập: {data.get('login', 'Không có')}\n"
                    f"🆔 ID: {data.get('id', 'Không rõ')}\n"
                    f"📝 Tên đầy đủ: {data.get('name', 'Không có tên')}\n"
                    f"🔗 URL hồ sơ: {data.get('html_url', 'Không có')}\n"
                    f"🏢 Công ty: {data.get('company', 'Không có thông tin')}\n"
                    f"📍 Vị trí: {data.get('location', 'Không có thông tin')}\n"
                    f"📧 Email: {data.get('email', 'Không công khai')}\n"
                    f"💼 Hireable: {'Có thể thuê' if data.get('hireable') else 'Không thể thuê hoặc không công khai'}\n"
                    f"💬 Bio: {data.get('bio', 'Không có thông tin')}\n"
                    f"🌐 Blog: {data.get('blog', 'Không có URL blog')}\n"
                    f"🔦 Twitter: {data.get('twitter_username', 'Không có Twitter')}\n"
                    f"🕒 Ngày tạo tài khoản: {data.get('created_at', 'Không rõ')}\n"
                    f"🕒 Ngày cập nhật: {data.get('updated_at', 'Không rõ')}\n"
                    f"📂 Repositories công khai: {data.get('public_repos', 0)}\n"
                    f"📂 Gists công khai: {data.get('public_gists', 0)}\n"
                    f"⭐ Follower: {data.get('followers', 0)} | Đang follow: {data.get('following', 0)}\n"
                    f"🏷️ Loại tài khoản: {data.get('type', 'Không rõ')}\n"
                    f"🔗 Site admin: {'✅' if data.get('site_admin') else '❌'}\n"
                )

                avatar_url = data.get('avatar_url', None)
                if avatar_url and avatar_url.startswith("http"):
                    try:
                        img = requests.get(avatar_url, timeout=5).content
                        with open("github_avatar.jpg", "wb") as f:
                            f.write(img)
                        self.sendLocalImage(
                            "github_avatar.jpg",
                            message=Message(text=info),
                            thread_id=thread_id,
                            thread_type=thread_type
                        )
                        os.remove("github_avatar.jpg")
                    except:
                        self.send(Message(text=info), thread_id=thread_id, thread_type=thread_type)
                else:
                    self.send(Message(text=info), thread_id=thread_id, thread_type=thread_type)

            elif resp.status_code == 404:
                self.send(Message(text="❌ Không tìm thấy người dùng GitHub này."), thread_id, thread_type)
            elif resp.status_code == 403:
                self.send(Message(text="❌ Đã vượt giới hạn truy vấn API GitHub. Vui lòng thử lại sau."), thread_id, thread_type)
            else:
                self.send(Message(text=f"❌ Lỗi không xác định từ GitHub (mã {resp.status_code})."), thread_id, thread_type)

        except requests.exceptions.Timeout:
            self.send(Message(text="❌ Quá thời gian chờ phản hồi từ GitHub."), thread_id, thread_type)
        except Exception as e:
            self.send(Message(text=f"❌ Đã xảy ra lỗi khi lấy thông tin GitHub: {e}"), thread_id, thread_type)
#2fa
    def handle_2fa(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/2fa'):
            return

        parts = message.strip().split()
        if len(parts) < 2:
            self.send(
                Message(text="⚠️ Vui lòng nhập mã sau lệnh /2fa\n\nVí dụ:\n/2fa 242RIHRGMWYHZ76GDDEZSP3XKK5TUJSQ"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        ma2fa = parts[1].strip().upper()

        # Kiểm tra mã hợp lệ theo chuẩn Base32 (chỉ A-Z và 2-7), 32 ký tự
        if not re.fullmatch(r'[A-Z2-7]{32}', ma2fa):
            self.send(
                Message(text="❌ Mã 2FA không hợp lệ!\n\nMã phải gồm 32 ký tự chữ in hoa và số, không dấu cách hoặc ký tự đặc biệt.\n\nVí dụ hợp lệ:\n/2fa 242RIHRGMWYHZ76GDDEZSP3XKK5TUJSQ"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        try:
            response = requests.get(f"https://2fa.live/tok/{ma2fa}", timeout=5)
            response.raise_for_status()
            res = response.json()
            code = res.get("token")

            if code and code.isdigit() and len(code) == 6:
                msg = (
                    f"🔐 Bạn Đã Nhập Là:  {ma2fa}\n\n🔑 Mã Là: {code}\n✅ Mã hợp lệ!\n\n🕒 Mỗi mã có hiệu lực khoảng 30 giây."
                )
            else:
                msg = (
                    f"❌ Không thể tạo mã 2FA từ chuỗi bạn cung cấp.\n"
                    f"Vui lòng kiểm tra lại chuỗi: {ma2fa}"
                )
        except requests.exceptions.Timeout:
            msg = "⏰ Máy chủ quá tải hoặc mất kết nối, vui lòng thử lại sau vài giây."
        except requests.exceptions.RequestException:
            msg = "❌ Có lỗi khi kết nối đến máy chủ 2FA. Vui lòng thử lại sau."

        self.send(
            Message(text=msg),
            thread_id=thread_id,
            thread_type=thread_type
        )

#roblox
    def handle_roblox(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/roblox'):
            return

        parts = message.strip().split()
        if len(parts) != 2:
            self.send(Message(text="❗ Sử dụng đúng cú pháp: /roblox mygame43"), thread_id, thread_type)
            return

        username = parts[1]
        info, avatar_url, profile_url = self.get_roblox_full_info(username)

        if info.startswith("❌"):
            self.send(Message(text=info), thread_id, thread_type)
            return

        roblox_text = info + f"\n🔗 Hồ sơ: {profile_url}"

        if avatar_url:
            try:
                img = requests.get(avatar_url, timeout=5).content
                with open("rbx.jpg", "wb") as f:
                    f.write(img)
                self.sendLocalImage("rbx.jpg", message=Message(text=roblox_text), thread_id=thread_id, thread_type=thread_type)
                os.remove("rbx.jpg")
            except:
                self.send(Message(text=roblox_text), thread_id, thread_type)
        else:
            self.send(Message(text=roblox_text), thread_id, thread_type)

    def get_roblox_full_info(self, username):
        try:
            resp = requests.get(f"https://offvnx.x10.bz/api/roblox.php?username={username}")
            if resp.status_code != 200:
                return f"❌ Không thể truy cập API cho người dùng: {username}", None, None

            data = resp.json()
            if 'username' not in data:
                return f"❌ Không tìm thấy người dùng: {username}", None, None

            display_name = data.get('display_name', username)
            user_id = data.get('user_id', 'Không rõ')
            created = data.get('created', 'Không rõ')
            description = data.get('description', 'Không có mô tả.')
            presence = data.get('presence', 'Không rõ')
            friends_count = data.get('friends', 'Không rõ')
            followers_count = data.get('followers', 'Không rõ')
            group_names = data.get('groups', [])
            group_count = data.get('group_count', 0)
            avatar_url = data.get('avatar_url', None)
            profile_url = data.get('profile_url', f"https://www.roblox.com/users/{user_id}/profile")

            group_text = "\n".join(f"- {name}" for name in group_names[:5]) if group_names else "Không tham gia nhóm nào"

            result = f"""
👤 Thông tin ROBLOX
🧑 Tên: {username} ({display_name})
🆔 ID: {user_id}
📅 Ngày tạo: {created}
📝 Mô tả: {description or "Không có mô tả."}
🌐 Trạng thái: {presence}
👥 Số bạn bè: {friends_count}
👀 Người theo dõi: {followers_count}
🏘️ Nhóm đang tham gia ({group_count}):
{group_text}
"""
            return result.strip(), avatar_url, profile_url

        except Exception as e:
            return f"❌ Đã xảy ra lỗi: {e}", None, None
#downig

    def get_kqxs_mien_bac(self):
        try:
            url = "https://nguyenmanh.name.vn/api/xsmb?apikey=OUEaxPOl"
            response = requests.get(url)
            data = response.json()

            if data.get("status") == 200:
                result = data.get("result", "Không có dữ liệu.")
                return f"""🎰 KẾT QUẢ XỔ SỐ MIỀN BẮC 🔢
━━━━━━━━━━━━━━━━━━
{result}
━━━━━━━━━━━━━━━━━━
💡 Gõ /kqxs để xem lại kết quả hôm nay.
"""
            else:
                return "⚠️ Không thể lấy dữ liệu xổ số Miền Bắc."
        except Exception as e:
            return f"❌ Lỗi khi gọi API: {e}"

    def handle_kqxs(self, message_object, thread_id, thread_type, author_id):
        if hasattr(message_object, 'content') and message_object.content.startswith("/kqxs"):
            msg = self.get_kqxs_mien_bac()
            self.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
#tiktok
    def sendLocalVideo(self, video_url, caption, thread_id, thread_type):
        try:
            if video_url.endswith(".mp4"):
                self.sendLocalFile(
                    file_url=video_url,
                    file_type="video",
                    caption=caption,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            else:
                self.send(
                    Message(text=caption + f"\n📎 Link video: {video_url}"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
        except Exception as e:
            print(f"[ERROR] sendLocalVideo: {e}")
            self.send(
                Message(text="❌ Lỗi khi gửi video. Vui lòng thử lại."),
                thread_id=thread_id,
                thread_type=thread_type
            )

    def handle_tiktok_download(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/tiktok'):
            return

        parts = message.strip().split(maxsplit=1)
        if len(parts) < 2:
            self.send(
                Message(text="⚠️ Vui lòng nhập link video TikTok sau lệnh /tiktok.\n\nVí dụ: /tiktok https://vt.tiktok.com/ZShG3E9V4/"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        url = parts[1].strip()
        api_url = f"https://offvnx.x10.bz/api/video.php?url={requests.utils.quote(url)}"

        try:
            res = requests.get(api_url, timeout=15)
            data = res.json()
        except Exception as e:
            self.send(
                Message(text="❌ Lỗi khi truy cập API video."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        if data.get("msg") != "success" or "data" not in data:
            self.send(
                Message(text="❌ Không thể tải video từ URL đã cung cấp."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        d = data['data']
        title = d.get("title", "Không rõ tiêu đề")
        author_name = d['author']['nickname']
        author_id = d['author']['unique_id']
        region = d.get("region", "Không rõ")
        create_time = d.get('create_time', 'N/A')
        duration = d.get("duration") or d.get("music_info", {}).get("duration", "Không rõ")
        is_ad = d.get("is_ad", False)
        size = d.get("size", 0)
        play_count = d.get("play_count", 0)
        digg_count = d.get("digg_count", 0)
        comment_count = d.get("comment_count", 0)
        share_count = d.get("share_count", 0)
        download_count = d.get("download_count", 0)
        collect_count = d.get("collect_count", 0)

        caption = f"""
🎥 {title}
👤 Tác giả: {author_name} (@{author_id})
🌍 Khu vực: {region}
🎮 Độ dài video: {duration} giây
🗓️ Ngày đăng: {create_time}
📢 Quảng cáo: {'Có' if is_ad else 'Không'}
🗂️ Dung lượng: {size} MB
---------------------------------------
▶️ Lượt xem: {play_count}
❤️ Lượt thích: {digg_count}
💬 Bình luận: {comment_count}
🔄 Chia sẻ: {share_count}
⬇️ Tải xuống: {download_count}
📥 Lượt lưu: {collect_count}
""".strip()

        video_url = d.get("play") or ""
        video_download = d.get("video_url") or ""
        images = d.get("images", [])

        # Gửi ảnh nếu là dạng slideshow
        if images:
            for img_url in images[:10]:
                self.sendLocalImage(
                    img_url,
                    message=Message(text=caption),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            return

        # Gửi video ưu tiên dạng .mp4, kèm caption nếu Zalo hỗ trợ
        if video_download.endswith(".mp4"):
            self.sendLocalVideo(video_download, caption, thread_id, thread_type)
        elif video_url:
            self.sendLocalVideo(video_url, caption, thread_id, thread_type)
        else:
            self.send(
                Message(text="⚠️ Không tìm thấy video hoặc ảnh để gửi."),
                thread_id=thread_id,
                thread_type=thread_type
            )

# 🟢 Hàm xử lý lệnh /fb
    def handle_fb(self, message, message_object, thread_id, thread_type, author_id):
        if not hasattr(message_object, 'content') or not isinstance(message_object.content, str):
            return

        if not message_object.content.startswith('/fb'):
            return

        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            self.send(
                Message(text="❌ Vui lòng nhập UID hoặc Link Facebook. Ví dụ: /fb 61574395204757 hoặc /fb facebook.com/zuck"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        fb_input = parts[1].strip()

        if fb_input.isdigit():
            fb_id = fb_input
        else:
            if not fb_input.startswith("http"):
                fb_input = "https://" + fb_input
            try:
                convert_api = f"https://offvnx.x10.bz/api/convertID.php?url={fb_input}"
                res = requests.get(convert_api, timeout=10)
                fb_id = str(res.json().get("id", ""))
                if not fb_id.isdigit():
                    self.send(
                        Message(text="❌ Không thể lấy UID từ link Facebook này."),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return
            except Exception:
                self.send(
                    Message(text="🚫 Đã xảy ra lỗi khi lấy UID từ link."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

        try:
            api_url = f"https://offvnx.x10.bz/fb.php?id={fb_id}&key=offvnx"
            res = requests.get(api_url)
            data = res.json().get("result", {})

            if not isinstance(data, dict) or not data:
                self.send(
                    Message(text="❌ Không tìm thấy thông tin người dùng."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            name = data.get("name", "Không công khai")
            username = data.get("username", "Chưa thiết lập")
            profile_id = data.get("id", "Chưa thiết lập")
            link = data.get("link", f"https://facebook.com/{username}")
            picture = data.get("picture", {}).get("data", {}).get("url", "")
            is_silhouette = data.get("picture", {}).get("data", {}).get("is_silhouette", True)
            cover_url = data.get("cover", {}).get("source", "")
            created_time = data.get("created_time", "Không công khai")
            about = data.get("about", "Không công khai")
            gender = data.get("gender", "Không công khai").capitalize()
            hometown = data.get("hometown", {}).get("name", "Không công khai")
            location = data.get("location", {}).get("name", "Không công khai")
            updated_time = data.get("updated_time", "Không công khai")
            followers = data.get("followers", "Không công khai")
            following = data.get("following", "Không rõ")
            birthday = data.get("birthday", "Không hiển thị ngày sinh")
            quotes = data.get("quotes", "Không có trích dẫn")
            relationship = data.get("relationship_status", "Không công khai")
            is_verified = "Đã Xác Minh ✅" if data.get("is_verified") else "Chưa xác minh ❌"
            flag = data.get("country_flag", "Không rõ")

            significant = data.get("significant_other", {})
            significant_line = ""
            if significant.get("id"):
                significant_line = f"""│ -> 💍 Đã kết hôn với: {significant.get('name', '')}
│ -> 🔗 Link UID: https://facebook.com/{significant['id']}"""

            work_info = ""
            for job in data.get("work", []):
                position = job.get("position", {}).get("name", "")
                employer = job.get("employer", {}).get("name", "")
                work_info += f"\n│ -> Làm việc tại {position} ở {employer}"
            if not work_info:
                work_info = "Không công khai"

            edu_info = ""
            for edu in data.get("education", []):
                school = edu.get("school", {}).get("name", "")
                concentration = edu.get("concentration", [{}])[0].get("name", "")
                edu_info += f"\n│ -> Học {concentration} tại {school}"
            if not edu_info:
                edu_info = "Không công khai"

            result = f"""
╭─────────────⭓
│ 𝗡𝗮𝗺𝗲: {name}
│ 𝗨𝗜𝗗: {profile_id}
│ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {username}
│ 𝗟𝗶𝗻𝗸: {link}
│ 𝗕𝗶𝗿𝘁𝗵𝗱𝗮𝘆: {birthday}
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀: {followers}
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗶𝗻𝗴: {following}
│ 𝗖𝗿𝗲𝗮𝘁𝗲𝗱: {created_time}
│ 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱: {is_verified}
│ 𝗧𝗶̀𝗻𝗵 𝘁𝗿𝗮̣𝗻𝗴: {relationship}
{significant_line}
│ 𝗕𝗶𝗼: {about}
│ 𝗚𝗲𝗻𝗱𝗲𝗿: {gender}
│ 𝗛𝗼𝗺𝗲𝘁𝗼𝘄𝗻: {hometown}
│ 𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻: {location}
│ 𝗪𝗼𝗿𝗸: {work_info}
│ 𝗘𝗱𝘂: {edu_info}
│ 𝗤𝘂𝗼𝘁𝗲: {quotes}
├─────────────⭔
│ 𝗟𝗮𝗻𝗴𝘂𝗮𝗴𝗲: {flag}
│ 𝗧𝗶𝗺𝗲 𝗨𝗽𝗱𝗮𝘁𝗲: {updated_time}
╰─────────────⭓
"""

            if picture and not is_silhouette and picture.startswith("http"):
                try:
                    img = requests.get(picture, timeout=5).content
                    with open("fb_avatar.jpg", "wb") as f:
                        f.write(img)
                    self.sendLocalImage(
                        "fb_avatar.jpg",
                        message=Message(text=result),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    os.remove("fb_avatar.jpg")
                    return
                except:
                    pass

            self.send(
                Message(text=result),
                thread_id=thread_id,
                thread_type=thread_type
            )

        except Exception as e:
            print(f"[ERROR] handle_fb: {e}")
            self.send(
                Message(text="🚫 Đã xảy ra lỗi khi lấy thông tin Facebook."),
                thread_id=thread_id,
                thread_type=thread_type
            )
#lệnh tt
    def handle_tt(self, message, message_object, thread_id, thread_type, author_id):
        if hasattr(message_object, 'content') and isinstance(message_object.content, str):
            if message_object.content.startswith('/tt'):
                parts = message.split()
                if len(parts) < 2:
                    self.send(Message(text="⚠️ Vui lòng nhập username TikTok. Ví dụ: /tt duonghungcasi"), thread_id=thread_id, thread_type=thread_type)
                    return

                username = parts[1]
                api_url = f"https://offvnx.x10.bz/api/tt.php?input={username}&key=offvnx"

                try:
                    res = requests.get(api_url, timeout=10)
                    data = res.json()

                    if not data.get("success"):
                        self.send(Message(text="❌ Không thể lấy thông tin người dùng. Vui lòng kiểm tra lại username."), thread_id=thread_id, thread_type=thread_type)
                        return

                    user_info = data['data']['userInfo']['user']
                    stats = data['data']['userInfo']['statsV2']
                    is_verified = "Đã xác minh ✅" if user_info.get('verified') else "Chưa xác minh ❌"
                    account_status = "Công Khai ✅" if not user_info.get('privateAccount') else "Riêng Tư ❌"
                    has_playlist = "Có danh sách phát ✅" if user_info.get('profileTab', {}).get('showPlayListTab') else "Không có danh sách phát ❌"
                    following_visibility = "Danh sách following đã bị ẩn ❌" if user_info.get('followingVisibility') == 2 else "Danh sách following hiển thị ✅"
                    commerce_status = f"Người dùng thương mại 🛒 ({user_info.get('commerceUserInfo', {}).get('category', 'Chưa rõ')})" if user_info.get('commerceUserInfo', {}).get('commerceUser') else "Không phải tài khoản thương mại ❌"
                    download_status = "Cho phép tải video ✅" if user_info.get('downloadSetting') == 0 else "Không cho tải video ❌"
                    seller_status = "Người bán TikTok Shop 🛍️" if user_info.get('ttSeller') else "Không phải người bán ❌"
                    org_status = "Tổ chức 🏢" if user_info.get('isOrganization') else "Cá nhân 👤"
                    live_status = "Đang Livestream 🔴" if user_info.get('roomId') else "Không livestream ❌"
                    comment_setting = ["Mọi người", "Bạn bè", "Không ai"][user_info.get('commentSetting', 0)]
                    duet_setting = ["Mọi người", "Bạn bè", "Không ai"][user_info.get('duetSetting', 0)]
                    stitch_setting = ["Mọi người", "Bạn bè", "Không ai"][user_info.get('stitchSetting', 0)]

                    result = f"""
╭─────────────⭓
│ ‎𝗡𝗮𝗺𝗲: {user_info['nickname']}
│ 𝗜𝗗: {user_info['id']}
│ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {user_info['uniqueId']}
│ 𝗟𝗶𝗻𝗸: https://www.tiktok.com/@{user_info['uniqueId']}
│ 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱: {is_verified}
│ 𝗦𝘁𝗮𝘁𝘂𝘀:
│ | -> {account_status}
│ | -> {has_playlist}
│ | -> {following_visibility}
│ | -> {live_status}
│ | -> {download_status}
│ | -> Bình luận: {comment_setting} 💬
│ | -> Duet: {duet_setting} 🎤
│ | -> Stitch: {stitch_setting} ✂️
│ 𝗖𝗼𝗺𝗺𝗲𝗿𝗰𝗲: {commerce_status}
│ 𝗦𝗲𝗹𝗹: {seller_status}
│ 𝗔𝗰𝗰𝗼𝘂𝗻𝘁: {org_status}
│ 𝗕𝗶𝗼: {user_info.get('signature', 'Không có')}
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀: {int(stats.get('followerCount', 0)):,} Follower
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗶𝗻𝗴: {int(stats.get('followingCount', 0)):,} Đang Follow
│ 𝗙𝗿𝗶𝗲𝗻𝗱𝘀: {int(stats.get('friendCount', 0)):,} Bạn Bè
│ 𝗟𝗶𝗸𝗲𝘀: {int(stats.get('heartCount', 0)):,} Thích
│ 𝗩𝗶𝗱𝗲𝗼𝘀: {int(stats.get('videoCount', 0)):,} Video
├─────────────⭔
│ 𝗡𝗮𝗺𝗲 𝗨𝗽𝗱𝗮𝘁𝗲: {user_info.get('nickNameModifyTime', 'Không rõ')}
│ 𝗖𝗿𝗲𝗮𝘁𝗲𝗱 𝗧𝗶𝗺𝗲: {user_info.get('createTime', 'Không rõ')}
│ 𝗟𝗮𝗻𝗴𝘂𝗮𝗴𝗲: {user_info.get('language', 'Không rõ')}
╰─────────────⭓
"""

                    avatar_url = user_info.get("avatarLarger")
                    if avatar_url and avatar_url.startswith("http"):
                        img_data = requests.get(avatar_url, timeout=5).content
                        path = "tt_avatar.jpg"
                        with open(path, 'wb') as f:
                            f.write(img_data)
                        self.sendLocalImage(path, message=Message(text=result), thread_id=thread_id, thread_type=thread_type)
                        os.remove(path)
                    else:
                        self.send(Message(text=result), thread_id=thread_id, thread_type=thread_type)

                except Exception as e:
                    print(f"[ERROR] handle_tt: {e}")
                    self.send(Message(text="🚫 Đã xảy ra lỗi khi lấy thông tin TikTok."), thread_id=thread_id, thread_type=thread_type)

# === CẤU HÌNH ===
imei = '741d9fe8-4de7-4308-acaf-22ec65b77545-cd5d5f3ff8f374827248e13d2f7d64ca'
session_cookies = {"_ga_1J0YGQPT22":"GS1.1.1736134473.1.1.1736134489.44.0.0","ZConsent":"timestamp=1750753531846&location=https://zalo.me/pc","_ga_RYD7END4JE":"GS2.2.s1750753529$o1$g1$t1750753532$j57$l0$h0","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8uyd--YdKrPXtMRwwxHIbQBVPZgeZat.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8uyd--YdKrPXtMRwwxHIbQBVPZgeZat.1","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8yvdkcgbKXSXZYPfQkRIn21DvMjg9f74OC.1","_gcl_au":"1.1.1346585653.1750810140","_fbp":"fb.1.1750810148372.504829801388556238","_ga_NVN38N77J3":"GS2.2.s1750815388$o1$g1$t1750818760$j58$l0$h0","_ga_E63JS7SPBL":"GS2.1.s1750921525$o3$g0$t1750921525$j60$l0$h0","_ga":"GA1.2.1937952902.1736134474","zpsid":"JIzQ.226205539.10.KlieIMryC3OEuqixONmmDXWFGWHVIW86M4a33qSsraEcJ8gBR7qVkWLyC3O","zpw_sek":"Gdmc.226205539.a0.GZGwFeFStehWGwM7ejpUYlZ-k-6Xvloyuhlru-cbbUtwjudQwPE9tENigSl2uUEe_lQKRFONxZ0-tTgb3xJUYW","app.event.zalo.me":"6903828000121994566","_zlang":"vn"}
client = Bot("api_key", "secret_key", imei=imei, session_cookies=session_cookies)
client.listen()