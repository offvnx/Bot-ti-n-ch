import discord
from discord import app_commands
from discord.ext import commands
import requests
import aiohttp
import tempfile
from urllib.parse import quote
import os
import hashlib
import random
import io
import asyncio
import time
import urllib.parse
import datetime
from datetime import datetime, timedelta
import pytz

intents = discord.Intents.default()
intents.message_content = True  # Cần nếu bot xử lý tin nhắn văn bản
intents.members = True          # Cần nếu dùng lệnh lấy thông tin thành viên

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# Tiện ích phụ trợ
# ---------------------------

def explain_privacy(val):
    return {
        0: "Mọi người",
        1: "Bạn bè",
        2: "Chỉ mình tôi",
        3: "Cấm tải"
    }.get(val, str(val))

def country_flag(locale):
    if locale and "_" in locale:
        country_code = locale.split('_')[1]
        return ''.join([chr(127397 + ord(c.upper())) for c in country_code])
    return ''

def relationship_status_text(status):
    mapping = {
        "Single": "💔 Độc thân",
        "In a relationship": "💑 Đang hẹn hò",
        "Engaged": "💍 Đã đính hôn",
        "Married": "💒 Đã kết hôn",
        "It's complicated": "🤔 Phức tạp",
        "Separated": "💔 Đã ly thân",
        "Divorced": "💔 Đã ly hôn",
        "Widowed": "🖤 Đã góa",
        "In an open relationship": "🔗 Mối quan hệ mở",
        "In a civil union": "👬 Liên minh dân sự",
        "In a domestic partnership": "🏠 Đối tác chung sống",
        "Không công khai": "❓ Không công khai",
        "Chưa thiết lập": "❓ Không công khai",
        "": "❓ Không công khai"
    }
    return mapping.get(status, status if status else "❓ Không công khai")

@bot.tree.command(name="fb", description="Lấy thông tin Facebook từ UID hoặc link")
@app_commands.describe(fb_input="Nhập UID hoặc link Facebook")
async def fb(interaction: discord.Interaction, fb_input: str):
    await interaction.response.defer()

    # Lấy UID
    if fb_input.isdigit():
        fb_id = fb_input
    else:
        if not fb_input.startswith("http"):
            fb_input = "https://" + fb_input
        try:
            res = requests.get(f"https://offvn.x10.mx/php/convertID.php?url={fb_input}")
            if res.status_code == 200:
                fb_id = res.json().get("id", "")
                if not fb_id.isdigit():
                    await interaction.followup.send("❌ Không thể lấy UID từ link Facebook này.")
                    return
            else:
                await interaction.followup.send("❌ Lỗi khi kết nối API lấy UID.")
                return
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: {e}")
            return

    # Lấy dữ liệu
    try:
        res = requests.get(f"https://offvn.x10.mx/php/apiCheck.php?id={fb_id}")
        data = res.json().get("result", {})

        if not isinstance(data, dict):
            await interaction.followup.send("❌ UID không hợp lệ hoặc không tồn tại.")
            return

        # Gán dữ liệu
        name = data.get("name", "Không công khai")
        username = data.get("username", "Chưa thiết lập")
        profile_id = data.get("id", "Chưa thiết lập")
        link = data.get("link", "https://facebook.com/")
        picture = data.get("picture", {}).get("data", {}).get("url", "")
        cover = data.get("cover", {}).get("source", "")
        created_time = data.get("created_time", "Không công khai")
        about = data.get("about", "Không công khai")
        locale = data.get("locale", "Không công khai")
        gender = data.get("gender", "Không công khai").capitalize()
        hometown = data.get("hometown", {}).get("name", "Không công khai")
        location = data.get("location", {}).get("name", "Không công khai")
        updated_time = data.get("updated_time", "Không công khai")
        relationship = data.get("relationship_status", "Không công khai")
        birthday = data.get("birthday", "Không công khai")
        followers = data.get("followers", "Không công khai")
        quotes = data.get("quotes", "Không công khai")
        is_verified = data.get("is_verified", False)
        work = data.get("work", [])
        education = data.get("education", [])
        significant_other = data.get("significant_other", {})
        significant_other_name = significant_other.get("name", "")
        significant_other_id = significant_other.get("id", "")

        # Xử lý hiển thị
        flag = country_flag(locale)
        relationship_text = relationship_status_text(relationship)
        picture_status = "Có ảnh đại diện" if not data.get("picture", {}).get("data", {}).get("is_silhouette", True) else "🚫 Không có ảnh đại diện"
        verified_text = "Đã xác minh ✅" if is_verified else "Chưa xác minh ❌"

        # Tạo nội dung chính
        info_text = f"""
**👤 Name: {name}**
**🆔 UID:** {profile_id}
**🔗 Username:** {username}
**⚥ Giới tính:** {gender}
**🎂 Sinh nhật:** {birthday}
**❤️ Trạng thái:** {relationship_text}"""

        if significant_other_id and significant_other_name:
            info_text += f"\n**💑 Vợ/Chồng:** {significant_other_name}"
            info_text += f"\n**🆔 Vợ/Chồng:** {significant_other_id}"

        info_text += f"""
**📍 Địa điểm:** {location}
**🌍 Quốc gia:** {locale} {flag}
**🏡 Quê quán:** {hometown}
**☑️ Xác minh:** {verified_text}
**🖼️ Ảnh đại diện:** {picture_status}
**⏰ Ngày tạo:** {created_time}
**♻️ Cập nhật:** {updated_time}
**👥 Người theo dõi:** {followers}
**ℹ️ Giới thiệu:** {about or 'Không có'}
**💬 Quotes:** {quotes or 'Không có'}"""

        if education:
            edu_text = "\n**🎓 Học vấn:**"
            for edu in education:
                school = edu.get("school", {}).get("name", "N/A")
                year = edu.get("year", {}).get("name", "")
                concentration = ', '.join([c.get("name") for c in edu.get("concentration", [])]) if edu.get("concentration") else ""
                edu_text += f"\n• {school} ({year}) {'– ' + concentration if concentration else ''}"
            info_text += edu_text

        if work:
            work_text = "\n**💼 Công việc:**"
            for job in work:
                employer = job.get("employer", {}).get("name", "N/A")
                position = job.get("position", {}).get("name", "")
                job_location = job.get("location", {}).get("name", "")
                start_date = job.get("start_date", "")
                desc = job.get("description", "")
                work_text += f"\n• {employer} {'– ' + position if position else ''} ({start_date})"
                if job_location:
                    work_text += f"\n   > Địa điểm: {job_location}"
                if desc:
                    work_text += f"\n   > Mô tả: {desc}"
            info_text += work_text

        # Tải ảnh đại diện
        avatar_file = None
        if picture:
            try:
                avatar_res = requests.get(picture)
                if avatar_res.status_code == 200:
                    avatar_bytes = io.BytesIO(avatar_res.content)
                    avatar_file = discord.File(avatar_bytes, filename="avatar.jpg")
            except:
                pass

        # Gửi ảnh bìa riêng
        if cover:
            try:
                cover_res = requests.get(cover)
                if cover_res.status_code == 200:
                    cover_bytes = io.BytesIO(cover_res.content)
                    cover_file = discord.File(cover_bytes, filename="cover.jpg")
                    await interaction.followup.send(content="🖼️ Ảnh bìa:", file=cover_file)
            except:
                await interaction.followup.send(f"📎 Ảnh bìa: {cover}")
        else:
            await interaction.followup.send("🚫 Không có ảnh bìa.")

        # Gửi thông tin + ảnh đại diện
        if avatar_file:
            await interaction.followup.send(content=info_text.strip(), file=avatar_file)
        else:
            await interaction.followup.send(content=info_text.strip())

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi xử lý: {str(e)}")
# ---------------------------
# Slash Command: /tt (TikTok Full Info)
# ---------------------------
@bot.tree.command(name="tt", description="Lấy thông tin TikTok từ username hoặc link")
@app_commands.describe(username="Nhập username TikTok")
async def tt(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    if "tiktok.com" in username:
        username = username.strip().split("@")[-1].split("/")[0]

    url = f"https://offvn.x10.mx/php/tt.php?input={username}&key=offvnx"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(f"❌ Không thể kết nối API (mã lỗi {response.status})")
                    return
                data = await response.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi API: {e}")
        return

    if not data.get("success") or "userInfo" not in data["data"]:
        await interaction.followup.send("❌ Không tìm thấy thông tin TikTok.")
        return

    user = data["data"]["userInfo"]["user"]
    stats = data["data"]["userInfo"]["stats"]
    profile_tab = user.get("profileTab", {})

    def bool_icon(value):
        return "Có ✅" if value else "Không ❌"

    def explain_privacy(val):
        return {
            0: "🌐 Mọi người",
            1: "👥 Bạn bè",
            2: "🔒 Chỉ mình tôi",
            3: "🚫 Cấm tải"
        }.get(val, "Không rõ")

    # Tạo Embed
    embed = discord.Embed(
        title=f"Thông tin TikTok của @{user.get('uniqueId')}",
        url=f"https://www.tiktok.com/@{user.get('uniqueId')}",
        description=f"{user.get('signature') or '_Không có tiểu sử_'}",
        color=0xFF0050
    )
    embed.set_author(name="TikTok Profile", icon_url="https://cdn-icons-png.flaticon.com/512/3046/3046122.png")

    # Lấy avatar
    avatar = user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb")
    embed.set_thumbnail(url=avatar)  # Thumbnail nhỏ góc phải
    embed.set_image(url=avatar)      # Ảnh lớn phía dưới embed

    info = (
        f"**Tên:** {user.get('nickname') or 'Không rõ'}\n"
        f"**User ID:** {user.get('id')}\n"
        f"**Short ID:** {user.get('shortId') or 'Không có'}\n"
        f"**Khu vực:** {user.get('region_flag') or 'Không rõ'}\n"
        f"**Ngôn ngữ:** {user.get('language') or 'Không rõ'}\n"
        f"**Tài khoản:** {'Riêng tư' if user.get('privateAccount') else 'Công khai'}\n"
        f"**Xác minh:** {bool_icon(user.get('verified'))}\n"
        f"**Cho phép tải:** {explain_privacy(user.get('downloadSetting'))}\n"
        f"**Bình luận:** {explain_privacy(user.get('commentSetting'))}"
    )

    stats_info = (
        f"**👥 Đang theo dõi:** {stats.get('followingCount')}\n"
        f"**👤 Người theo dõi:** {stats.get('followerCount'):,}\n"
        f"**❤️ Lượt thích:** {stats.get('heartCount'):,}\n"
        f"**🎞️ Số video:** {stats.get('videoCount')}"
    )

    other_info = (
        f"**⭐ Tab nhạc:** {bool_icon(profile_tab.get('showMusicTab'))}\n"
        f"**📁 Playlist:** {bool_icon(profile_tab.get('showPlayListTab'))}\n"
        f"**❓ Hỏi đáp:** {bool_icon(profile_tab.get('showQuestionTab'))}\n"
        f"**🛒 Shop:** {bool_icon(user.get('ttSeller'))}\n"
        f"**🏢 Tổ chức:** {bool_icon(user.get('isOrganization'))}"
    )

    embed.add_field(name="• Thông tin cơ bản", value=info, inline=False)
    embed.add_field(name="• Thống kê", value=stats_info, inline=False)
    embed.add_field(name="• Khác", value=other_info, inline=False)

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Xem trên TikTok", url=f"https://www.tiktok.com/@{user.get('uniqueId')}"))

    await interaction.followup.send(embed=embed, view=view)
# ---------------------------
# tải video tiktok
# ---------------------------

# Hàm định dạng an toàn
def safe_number(val):
    try:
        return f"{int(val):,}"
    except:
        return "Không rõ"

@bot.tree.command(name="tiktok", description="Lấy thông tin đầy đủ từ video TikTok")
@app_commands.describe(link="Dán liên kết video TikTok")
async def tiktok(interaction: discord.Interaction, link: str):
    await interaction.response.defer()

    url = f"https://offvn.x10.mx/php/video.php?url={link}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(f"❌ Không thể kết nối API (mã lỗi {response.status})")
                    return
                res = await response.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi gọi API: {e}")
        return

    if res.get("code") != 0 or "data" not in res:
        await interaction.followup.send("❌ Không tìm thấy video hoặc API trả về lỗi.")
        return

    data = res["data"]
    author = data.get("author", {})
    music = data.get("music_info", {})

    embed = discord.Embed(
        title=data.get("title", "Không có tiêu đề"),
        url=link,
        color=0xFF0050,
        description=(
            f"**ID Video:** {data.get('id')}\n"
            f"**Khu vực:** {data.get('region')}\n"
            f"**Thời lượng:** {safe_number(data.get('duration'))} giây\n"
            f"**Dung lượng:** {data.get('size')} MB\n"
            f"**Dung lượng có logo:** {data.get('wm_size')} MB\n"
            f"**Lượt xem:** {safe_number(data.get('play_count'))}\n"
            f"**Lượt thích:** {safe_number(data.get('digg_count'))}\n"
            f"**Bình luận:** {safe_number(data.get('comment_count'))}\n"
            f"**Chia sẻ:** {safe_number(data.get('share_count'))}\n"
            f"**Tải xuống:** {safe_number(data.get('download_count'))}\n"
            f"**Đã lưu:** {safe_number(data.get('collect_count'))}\n"
            f"**Ngày đăng:** {data.get('create_time')}\n"
            f"**Quảng cáo:** {'Có' if data.get('is_ad') else 'Không'}\n"
            f"**Cho phép bình luận:** {'Có' if data.get('item_comment_settings') == 0 else 'Không'}\n\n"
            f"**Tác giả:** {author.get('nickname')} (@{author.get('unique_id')})\n"
            f"**ID tác giả:** {author.get('id')}\n\n"
            f"**Nhạc:** {music.get('title')} - {music.get('author')}\n"
            f"**ID nhạc:** {music.get('id')}\n"
            f"**Nhạc gốc:** {'Có' if music.get('original') else 'Không'}\n"
            f"**Thời lượng nhạc:** {safe_number(music.get('duration'))} giây"
        )
    )
    embed.set_thumbnail(url=data.get("cover"))
    embed.set_image(url=data.get("ai_dynamic_cover") or data.get("origin_cover"))
    embed.set_author(name=f"@{author.get('unique_id')}", icon_url=author.get("avatar"))

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Tải video (Không logo)", url=data.get("play")))
    view.add_item(discord.ui.Button(label="Tải video (Có logo)", url=data.get("wmplay")))
    view.add_item(discord.ui.Button(label="Tải nhạc", url=data.get("music")))

    await interaction.followup.send(embed=embed, view=view)
# ---------------------------
# qr nội dung
# ---------------------------
@bot.tree.command(name="qrnd", description="Tạo mã QR chuyển khoản ngân hàng")
@app_commands.describe(
    acc="Số tài khoản",
    bank="Mã ngân hàng (ví dụ: mbbank, bidv...)",
    amount="Số tiền cần chuyển",
    description="Nội dung chuyển khoản"
)
async def qrnd(interaction: discord.Interaction, acc: str, bank: str, amount: int, description: str):
    await interaction.response.defer()

    BANK_LIST = [
        "mbbank", "dongabank", "viettinbank", "vietcombank", "techcombank",
        "bidv", "acb", "sacombank", "vpbank", "agribank",
        "hdbank", "tpbank", "shb", "eximbank", "ocb",
        "seabank", "bacabank", "pvcombank", "scb", "vib",
        "namabank", "abbank", "lpbank", "vietabank", "msb",
        "nvbank", "pgbank", "publicbank", "cimbbank", "uob"
    ]

    if bank.lower() not in BANK_LIST:
        await interaction.followup.send("❌ Mã ngân hàng không hợp lệ. Vui lòng kiểm tra lại.")
        return

    qr_url = f"https://img.vietqr.io/image/{bank.lower()}-{acc}-compact.png?amount={amount}&addInfo={description}&download=true"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(qr_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Không thể tạo mã QR. Vui lòng thử lại.")
                    return
                image_bytes = await resp.read()

        file = discord.File(io.BytesIO(image_bytes), filename="qr.png")
        embed = discord.Embed(
            title="MÃ QR CHUYỂN KHOẢN",
            color=0x00B2FF,
            description=(
                f"🏦 Ngân hàng: **{bank.upper()}**\n"
                f"💳 Số tài khoản: `{acc}`\n"
                f"💵 Số tiền: `{amount:,} VNĐ`\n"
                f"📝 Nội dung: `{description}`"
            )
        )
        embed.set_image(url="attachment://qr.png")

        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi tạo mã QR: `{e}`")
# ---------------------------
# thông tin
# ---------------------------
@bot.tree.command(name="thongtin", description="Lấy thông tin đầy đủ của một người dùng Discord")
@app_commands.describe(user="Chọn người dùng cần kiểm tra (bỏ trống để lấy thông tin của bạn)")
async def thongtin(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()

    user = user or interaction.user
    member = interaction.guild.get_member(user.id) if interaction.guild else None

    embed = discord.Embed(
        title=f"Thông tin người dùng: {user.display_name}",
        color=discord.Color.blurple(),
        description=(
            f"**ID:** `{user.id}`\n"
            f"**Tên người dùng:** `{user}`\n"
            f"**Bot:** {'✅' if user.bot else '❌'}\n"
            f"**Tạo tài khoản:** <t:{int(user.created_at.timestamp())}:F>"
        )
    )

    if member:
        embed.add_field(
            name="Trong máy chủ:",
            value=(
                f"**Biệt danh:** {member.nick or 'Không có'}\n"
                f"**Tham gia server:** <t:{int(member.joined_at.timestamp())}:F>\n"
                f"**Trạng thái:** `{member.status.name.capitalize()}`\n"
                f"**Top Role:** {member.top_role.mention}\n"
                f"**Số lượng Role:** {len(member.roles)-1} (không tính @everyone)"
            ),
            inline=False
        )

        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name="Danh sách Role", value=", ".join(roles), inline=False)

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.display_avatar.url)

    await interaction.followup.send(embed=embed)
# ---------------------------
# ins
# ---------------------------
async def get_instagram_data(username):
    url = f"https://ducamod.info/ins/?username={username}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.json()
    except Exception as e:
        print(f"Lỗi API: {e}")
        return None

@bot.tree.command(name="ins", description="Lấy thông tin tài khoản Instagram từ username")
@app_commands.describe(username="Tên người dùng Instagram (không cần @)")
async def ins(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    data = await get_instagram_data(username)
    if not data or "username" not in data:
        await interaction.followup.send("❌ Không lấy được dữ liệu hoặc username không hợp lệ.")
        return

    verified = "✅ Đã xác minh" if data['is_verified'] else "❌ Chưa xác minh"
    privacy = "🔒 Riêng tư" if data['is_private'] else "🌐 Công khai"
    business = "🏢 Doanh nghiệp" if data['is_business'] else "🙋 Cá nhân"
    category = data.get('category') or "Không rõ"
    biography = data.get('biography') or "*Không có tiểu sử*"
    email = data.get('public_email') or "Không có"
    phone = data.get('public_phone_number') or "Không có"
    website = data.get('external_url') or "Không có"
    profile_url = f"https://instagram.com/{data['username']}"

    # Gộp thông tin vào description
    description = (
        f"**ID Tài khoản:** {data.get('id', 'Không rõ')}\n"
        f"**Họ tên:** {data.get('full_name') or 'Không rõ'}\n"
        f"**Username:** @{data['username']}\n"
        f"**Xác minh:** {verified}\n"
        f"**Quyền riêng tư:** {privacy}\n"
        f"**Loại tài khoản:** {business}\n"
        f"**Danh mục:** {category}\n\n"
        f"**📸 Bài viết:** {data['media_count']}\n"
        f"**👥 Người theo dõi:** {data['follower_count']}\n"
        f"**➡️ Đang theo dõi:** {data['following_count']}\n\n"
        f"**📧 Email:** {email}\n"
        f"**📞 Số điện thoại:** {phone}\n"
        f"**🔗 Website:** {website}\n\n"
        f"**📄 Tiểu sử:**\n{biography}"
    )

    embed = discord.Embed(
        title=f"Instagram: @{data['username']}",
        url=profile_url,
        description=description,
        color=discord.Color.purple()
    )

    embed.set_author(name="Instagram Profile", icon_url="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png")
    embed.set_image(url=data['profile_pic_url'])  # Ảnh đại diện to

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Xem trên Instagram", url=profile_url))

    await interaction.followup.send(embed=embed, view=view)

# ---------------------------
# qrbank
# ---------------------------
def get_qr_url(bank, stk):
    return f"https://img.vietqr.io/image/{bank}-{stk}-compact.png"

def get_vietnam_time():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")

@bot.tree.command(name="qrbank", description="Tạo mã QR chuyển khoản từ STK và tên ngân hàng")
@app_commands.describe(
    stk="Số tài khoản ngân hàng",
    bank="Mã ngân hàng viết liền không dấu (ví dụ: MBbank, ACB, VCB)"
)
async def qrbank_command(interaction: discord.Interaction, stk: str, bank: str):
    await interaction.response.defer()

    qr_url = get_qr_url(bank, stk)

    try:
        resp = requests.head(qr_url, timeout=10)
        if resp.status_code != 200:
            await interaction.followup.send("⚠️ Không thể tạo mã QR. Có thể bạn đã nhập sai số tài khoản hoặc mã ngân hàng.")
            return
    except Exception:
        await interaction.followup.send("⚠️ Không thể kiểm tra mã QR, vui lòng thử lại sau.")
        return

    current_date = get_vietnam_time()
    caption = (
        f"**Mã QR Bank Đã Được Tạo**\n"
        f"`💳 STK:` **{stk}**\n"
        f"`🏦 Ngân hàng:` **{bank.upper()}**\n"
        f"`📅 Ngày tạo QR:` **{current_date}**"
    )

    embed = discord.Embed(description=caption)
    embed.set_image(url=qr_url)

    await interaction.followup.send(embed=embed)
# ---------------------------
# 2fa
# ---------------------------
@bot.tree.command(name="2fa", description="Tạo mã 2FA từ secret key")
@app_commands.describe(secret="Nhập mã secret 2FA (VD: 242RIHRGMWYHZ76GDDEZSP3XKK5TUJSQ)")
async def twofa_command(interaction: discord.Interaction, secret: str):
    await interaction.response.defer()

    url = f"https://2fa.live/tok/{secret.strip().upper()}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        token = data.get("token")
        if not token or not token.isdigit() or len(token) != 6:
            result_text = "❌ Mã không hợp lệ hoặc không thể tạo mã 2FA."
        else:
            result_text = f"✅ Mã 2FA là: `{token}`"
    except Exception:
        result_text = "⚠️ Đã xảy ra lỗi khi lấy mã 2FA. Vui lòng thử lại sau."

    current_time = get_vietnam_time()
    await interaction.followup.send(
        f"**{current_time}**\n──────────────\n{result_text}"
    )

# ---------------------------
# qrcode
# ---------------------------
@bot.tree.command(name="qrcode", description="Tạo mã QR từ văn bản bất kỳ")
@app_commands.describe(content="Nội dung cần tạo QR Code (VD: Hello world)")
async def qrcode_command(interaction: discord.Interaction, content: str):
    await interaction.response.defer()

    encoded = urllib.parse.quote(content)
    qr_code_url = f"https://offvn.x10.mx/php/qr.php?text={encoded}"
    current_time = get_vietnam_time()

    embed = discord.Embed(
        title="Mã QR đã được tạo",
        description=f"**Nội dung:** `{content}`\n**Thời gian:** {current_time}",
        color=discord.Color.blue()
    )
    embed.set_image(url=qr_code_url)
    embed.set_footer(text=f"User ID: {interaction.user.id}\nMessage ID: {interaction.id}")

    await interaction.followup.send(embed=embed)

# ---------------------------
# idfb
# ---------------------------
def get_facebook_info(url):
    api_url = "https://offvn.x10.mx/php/convertID.php?url=" + requests.utils.quote(url)
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        return {
            'id': data.get('id'),
            'name': data.get('name')
        }
    except Exception:
        return None

@bot.tree.command(name="idfb", description="Lấy UID Facebook từ link hoặc ID")
@app_commands.describe(link_or_id="Link hoặc UID Facebook")
async def idfb_command(interaction: discord.Interaction, link_or_id: str):
    await interaction.response.defer()

    current_date = get_vietnam_time()

    parameter = link_or_id.strip()
    facebook_id = parameter if parameter.isdigit() else None
    facebook_name = None

    if not facebook_id:
        if "facebook.com" not in parameter:
            await interaction.followup.send("❌ Liên kết không hợp lệ.")
            return

        fb_info = get_facebook_info(parameter)
        if not fb_info or not fb_info.get('id'):
            await interaction.followup.send("❌ Không thể lấy ID từ liên kết Facebook.")
            return
        facebook_id = fb_info.get('id')
        facebook_name = fb_info.get('name')
    else:
        facebook_name = "Không lấy được"

    avatar_url = f"https://graph.facebook.com/{facebook_id}/picture?width=1500&height=1500&access_token=2712477385668128|b429aeb53369951d411e1cae8e810640"

    embed = discord.Embed(
        title="Thông tin Facebook",
        description=f"**UID:** `{facebook_id}`\n"
                    f"**Tên:** `{facebook_name}`\n"
                    f"**Link:** [Xem Facebook](https://www.facebook.com/profile.php?id={facebook_id})\n"
                    f"**Thời gian:** {current_date} (GMT+7)",
        color=discord.Color.blue()
    )

    # Gửi ảnh đại diện nếu tải thành công
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status == 200:
                image_bytes = await resp.read()
                file = discord.File(io.BytesIO(image_bytes), filename="avatar.jpg")
                embed.set_image(url="attachment://avatar.jpg")
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send("Không thể tải ảnh đại diện.")
# ---------------------------
# ask
# ---------------------------
def get_reaction():
    reactions = ['✨', '⚡', '🔥', '✅', '💡', '🔍', '🤖']
    return reactions[int(time.time()) % len(reactions)]

@bot.tree.command(name="ask", description="Đặt câu hỏi và nhận câu trả lời từ AI")
@app_commands.describe(question="Câu hỏi bạn muốn hỏi (ví dụ: Python là gì?)")
async def ask_command(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://blackbox-pro.bjcoderx.workers.dev/?q={question}'
            async with session.get(url, timeout=20) as resp:
                data = await resp.json()

        elapsed = time.time() - start_time

        if data.get("status") == "success":
            result = data["data"].get("result", "").strip()

            if not result or len(result) < 3:
                result = "_Không tìm thấy câu trả lời phù hợp._"

            reply_text = (
                f"{get_reaction()} **Trả lời cho câu hỏi của bạn:**\n"
                f"```❓ Câu hỏi: {question}```\n"
                f"💬 **Trả lời:** {result}\n"
                f"> ⏱ Thời gian phản hồi: {elapsed:.2f} giây"
            )
        else:
            reply_text = "❌ API không trả về kết quả thành công."

    except asyncio.TimeoutError:
        reply_text = "⏳ Máy chủ mất quá nhiều thời gian để phản hồi. Vui lòng thử lại sau!"
    except Exception as e:
        reply_text = f"⚠️ Đã xảy ra lỗi: `{str(e)}`"

    await interaction.followup.send(reply_text)

# ---------------------------
# Khởi động bot & đồng bộ lệnh
# ---------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot đã online: {bot.user}")

TOKEN = "MTM3NzEyODgxMjA4MDI3MTQwMA.GItxcI.qxSpJ1eCoVjP8-E5krdyi01uCswsfQyqmlRMjc"
bot.run(TOKEN)
