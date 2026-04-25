import os
import requests
import calendar
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from zhdate import ZhDate
import datetime as dt

# =====================================================================
# 🌟 第一部分：用户自定义区
# =====================================================================
ENABLED_PAGES = "1,2,3,4"
HOTLIST_SOURCE = "bilibili"
WEATHERAPI_LOCATION = "haining"            
CITY_DISPLAY_NAME = "海宁 | 平安顺遂"      

# =====================================================================
# 🔒 第二部分：核心密钥区
# =====================================================================
API_KEY = os.environ.get("ZECTRIX_API_KEY")
MAC_ADDRESS = os.environ.get("ZECTRIX_MAC")
WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY")

PUSH_URL = f"https://cloud.zectrix.com/open/v1/devices/{MAC_ADDRESS}/display/image"

# =====================================================================
# ⚙️ 第三部分：底层运行逻辑
# =====================================================================
FONT_PATH = "font.ttf"
try:
    font_huge = ImageFont.truetype(FONT_PATH, 65)
    font_title = ImageFont.truetype(FONT_PATH, 24)
    font_item = ImageFont.truetype(FONT_PATH, 18)
    font_small = ImageFont.truetype(FONT_PATH, 14)
    font_tiny = ImageFont.truetype(FONT_PATH, 11)
    font_48 = ImageFont.truetype(FONT_PATH, 48)
    font_36 = ImageFont.truetype(FONT_PATH, 36)
except:
    print("❌ 错误: 找不到 font.ttf")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- 工具函数 ---
def get_wrapped_lines(text, max_chars=18):
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines

def get_clothing_advice(temp):
    try:
        t = int(temp)
        if t >= 28: return "建议穿短袖、短裤，注意防晒补水。"
        elif t >= 22: return "体感舒适，建议穿 T 恤配薄长裤。"
        elif t >= 16: return "建议穿长袖衬衫、卫衣或单层薄外套。"
        elif t >= 10: return "气温微凉，建议穿夹克、风衣或毛衣。"
        elif t >= 5: return "建议穿大衣、厚毛衣或薄款羽绒服。"
        else: return "天气寒冷，建议穿厚羽绒服，注意防寒。"
    except:
        return "请根据实际体感气温调整着装。"

def push_image(img, page_id):
    if str(page_id) not in ENABLED_PAGES:
        print(f"⏩ Page {page_id} 未启用，跳过推送。")
        return
        
    img.save(f"page_{page_id}.png")
    api_headers = {"X-API-Key": API_KEY}
    files = {"images": (f"page_{page_id}.png", open(f"page_{page_id}.png", "rb"), "image/png")}
    data = {"dither": "true", "pageId": str(page_id)}
    try:
        res = requests.post(PUSH_URL, headers=api_headers, files=files, data=data)
        print(f"✅ Page {page_id} 推送成功: {res.status_code}")
    except Exception as e:
        print(f"❌ Page {page_id} 推送失败: {e}")

# --- 节气与农历 ---
def get_solar_term(year, month, day):
    term_table = {
        (2024,2,4):"立春", (2024,2,19):"雨水", (2024,3,5):"惊蛰", (2024,3,20):"春分",
        (2024,4,4):"清明", (2024,4,19):"谷雨", (2024,5,5):"立夏", (2024,5,20):"小满",
        (2024,6,5):"芒种", (2024,6,21):"夏至", (2024,7,6):"小暑", (2024,7,22):"大暑",
        (2024,8,7):"立秋", (2024,8,22):"处暑", (2024,9,7):"白露", (2024,9,22):"秋分",
        (2024,10,8):"寒露", (2024,10,23):"霜降", (2024,11,7):"立冬", (2024,11,22):"小雪",
        (2024,12,6):"大雪", (2024,12,21):"冬至",
        (2025,1,5):"小寒", (2025,1,20):"大寒", (2025,2,3):"立春", (2025,2,18):"雨水",
        (2025,3,5):"惊蛰", (2025,3,20):"春分", (2025,4,4):"清明", (2025,4,20):"谷雨",
        (2025,5,5):"立夏", (2025,5,21):"小满", (2025,6,5):"芒种", (2025,6,21):"夏至",
        (2025,7,7):"小暑", (2025,7,22):"大暑", (2025,8,7):"立秋", (2025,8,23):"处暑",
        (2025,9,7):"白露", (2025,9,22):"秋分", (2025,10,8):"寒露", (2025,10,23):"霜降",
        (2025,11,7):"立冬", (2025,11,22):"小雪", (2025,12,7):"大雪", (2025,12,21):"冬至",
        (2026,1,5):"小寒", (2026,1,20):"大寒", (2026,2,4):"立春", (2026,2,18):"雨水",
        (2026,3,5):"惊蛰", (2026,3,20):"春分", (2026,4,5):"清明", (2026,4,20):"谷雨",
        (2026,5,5):"立夏", (2026,5,21):"小满", (2026,6,6):"芒种", (2026,6,21):"夏至",
        (2026,7,7):"小暑", (2026,7,23):"大暑", (2026,8,7):"立秋", (2026,8,23):"处暑",
        (2026,9,7):"白露", (2026,9,23):"秋分", (2026,10,8):"寒露", (2026,10,23):"霜降",
        (2026,11,7):"立冬", (2026,11,22):"小雪", (2026,12,7):"大雪", (2026,12,21):"冬至",
        (2027,1,5):"小寒", (2027,1,20):"大寒", (2027,2,4):"立春", (2027,2,19):"雨水",
        (2027,3,6):"惊蛰", (2027,3,21):"春分", (2027,4,5):"清明", (2027,4,20):"谷雨",
    }
    return term_table.get((year, month, day), None)

def get_lunar_or_festival(y, m, d):
    term = get_solar_term(y, m, d)
    if term: return term
    solar_fests = {
        (1,1):"元旦", (2,14):"情人节", (3,8):"妇女节", (4,1):"愚人节",
        (5,1):"劳动节", (6,1):"儿童节", (7,1):"建党节", (8,1):"建军节",
        (9,10):"教师节", (10,1):"国庆节", (12,25):"圣诞节"
    }
    if (m, d) in solar_fests: return solar_fests[(m, d)]
    try:
        lunar = ZhDate.from_datetime(datetime(y, m, d))
        lm, ld = lunar.lunar_month, lunar.lunar_day
        lunar_fests = {
            (1,1):"春节", (1,15):"元宵节", (5,5):"端午节",
            (7,7):"七夕节", (8,15):"中秋节", (9,9):"重阳节", (12,30):"除夕"
        }
        if (lm, ld) in lunar_fests: return lunar_fests[(lm, ld)]
        days = ["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
                "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
                "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"]
        months = ["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","冬月","腊月"]
        if ld == 1: return months[lm-1]
        return days[ld-1]
    except:
        return ""

# --- 热搜 ---
def get_hotlist_data(source):
    titles = []
    print(f"正在从 {source} 获取数据...")
    try:
        if source == "zhihu":
            url = "https://api.zhihu.com/topstory/hot-list"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            titles = [item['target']['title'] for item in res['data']]
        elif source == "bilibili":
            url = "https://api.bilibili.com/x/web-interface/wbi/search/square?limit=20"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            titles = [item['show_name'] for item in res['data']['trending']['list']]
        elif source == "github":
            date_str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"https://api.github.com/search/repositories?q=stars:>50+created:>{date_str}&sort=stars&order=desc"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            titles = [f"{item['full_name']}: {item['description'][:50] if item['description'] else 'No desc'}" for item in res['items']]
        else:
            titles = ["不支持的数据源"]
    except Exception as e:
        print(f"获取失败: {e}")
        titles = ["数据获取失败，请检查配置"] * 10
    return titles[:20]

def task_hotlist():
    source_map = {"zhihu": "知乎热榜", "bilibili": "B站热搜", "github": "GitHub 热门"}
    titles = get_hotlist_data(HOTLIST_SOURCE)
    title_display = source_map.get(HOTLIST_SOURCE, "热门看板")

    def draw_list(draw, page_title, items, start_idx):
        draw.rounded_rectangle([(10, 10), (390, 45)], radius=8, fill=0)
        draw.text((20, 15), page_title, font=font_title, fill=255)
        y, last_idx = 55, start_idx
        item_gap = 12
        line_height = 22
        for i in range(start_idx, len(items)):
            lines = get_wrapped_lines(items[i], 19)
            required_h = len(lines) * line_height
            if y + required_h > 295: break
            current_num = i + 1
            draw.rounded_rectangle([(10, y), (36, y+24)], radius=6, fill=0)
            num_x = 18 if current_num < 10 else 11
            draw.text((num_x, y+2), str(current_num), font=font_small, fill=255)
            curr_y = y + 2
            for line in lines:
                draw.text((45, curr_y), line, font=font_item, fill=0)
                curr_y += line_height
            y += max(24, required_h) + item_gap
            last_idx = i + 1
            if y < 290:
                draw.line([(45, y - item_gap/2), (380, y - item_gap/2)], fill=0, width=1)
        return last_idx

    if "1" in ENABLED_PAGES:
        img1 = Image.new('1', (400, 300), color=255)
        draw_list(ImageDraw.Draw(img1), f"◆ {title_display}", titles, 0)
        push_image(img1, 1)

# ==========================
# ✅ 完整版黄历（来自hl.py，已修复）
# ==========================
def get_huangli_font(size):
    fonts = [
        FONT_PATH,
        "SourceHanSansCN-Regular.ttf",
        "msyh.ttc",
        "simhei.ttf"
    ]
    for f in fonts:
        try:
            return ImageFont.truetype(f, size)
        except:
            continue
    return ImageFont.load_default(size=size)

def text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def render_auto(draw, x, y, text, max_w, max_lines, init_size, line_h):
    one_char = text_w(draw, "一", get_huangli_font(init_size))
    usable_w = max_w - one_char
    font = get_huangli_font(init_size)
    while True:
        lines = []
        current = ""
        ok = True
        for c in text:
            if text_w(draw, current + c, font) <= usable_w:
                current += c
            else:
                lines.append(current)
                current = c
                if len(lines) >= max_lines:
                    ok = False
                    break
        if current:
            lines.append(current)
        if ok and len(lines) <= max_lines:
            break
        font = get_huangli_font(font.size - 1)
    cy = y
    for line in lines:
        draw.text((x, cy), line, font=font, fill=0)
        cy += line_h
    return cy

def task_huangli():
    if "2" not in ENABLED_PAGES:
        return
    print("✅ 生成 Page 2：今日黄历")

    W, H = 400, 300
    img = Image.new("1", (W, H), 1)
    draw = ImageDraw.Draw(img)

    ft_title = get_huangli_font(34)
    ft_date  = get_huangli_font(22)
    ft_info  = get_huangli_font(20)

    now = dt.datetime.now()
    lunar = ZhDate.from_datetime(now)

    week_map = ["一", "二", "三", "四", "五", "六", "日"]
    week = week_map[now.weekday()]
    gongli = f"{now.year}年{now.month}月{now.day}日  周{week}"

    # 农历
    month_cn = ["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","冬月","腊月"]
    day_cn = ["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
              "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
              "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"]
    lunar_month = month_cn[lunar.lunar_month - 1]
    lunar_day = day_cn[lunar.lunar_day - 1]
    nongli = f"{lunar_month}{lunar_day}"

    # 生肖
    sx_list = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]
    sx = sx_list[(lunar.lunar_year - 4) % 12]
    chong = sx_list[(sx_list.index(sx) + 6) % 12]
    chong_str = f"冲{chong}"

    # 宜、忌（固定示例，可对接API）
    yi = "祭祀、祈福、求嗣、开光、出行、解除、拆卸、修造、安葬、开市、交易、立券"
    ji = "作灶、嫁娶、入宅、掘井、栽种"

    # 绘制
    title = "今日黃曆"
    tw = text_w(draw, title, ft_title)
    draw.text(((W - tw)//2, 15), title, font=ft_title, fill=0)
    draw.line([(30, 60), (370, 60)], 0, 1)

    dw = text_w(draw, gongli, ft_date)
    draw.text(((W - dw)//2, 68), gongli, font=ft_date, fill=0)
    draw.line([(25, 100), (375, 100)], 0, 2)

    draw.text((30, 115), f"農曆：{nongli}", font=ft_info, fill=0)
    draw.text((30, 145), f"生肖：{sx}    {chong_str}", font=ft_info, fill=0)

    draw.text((30, 175), "宜：", font=get_huangli_font(19), fill=0)
    render_auto(draw, 65, 175, yi, 315, 2, 19, 28)

    draw.text((30, 230), "忌：", font=get_huangli_font(19), fill=0)
    render_auto(draw, 65, 230, ji, 315, 2, 19, 28)

    push_image(img, 2)

# --- 日历 ---
def task_calendar():
    if "3" not in ENABLED_PAGES: return
    print("生成 Page 3: 日历...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    now_utc = datetime.utcnow()
    now = now_utc + timedelta(hours=8)
    y, m, today = now.year, now.month, now.day
    draw.text((20, 10), str(m), font=font_huge, fill=0)
    draw.text((90, 20), now.strftime("%B"), font=font_title, fill=0)
    draw.text((90, 48), str(y), font=font_item, fill=0)
    draw.line([(20, 78), (380, 78)], fill=0, width=2)
    headers = ["日", "一", "二", "三", "四", "五", "六"]
    col_w = 53
    for i, h in enumerate(headers):
        draw.text((25 + i*col_w, 88), h, font=font_small, fill=0)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(y, m)
    curr_y, row_h = 115, 38
    for week in cal:
        for c, day in enumerate(week):
            if day != 0:
                dx = 25 + c * col_w
                if day == today:
                    draw.rounded_rectangle([(dx-3, curr_y-2), (dx+35, curr_y+32)], radius=5, outline=0)
                draw.text((dx+2, curr_y), str(day), font=font_item, fill=0)
                bottom_text = get_lunar_or_festival(y, m, day)
                if bottom_text:
                    if len(bottom_text) > 3:
                        try:
                            font_smaller = ImageFont.truetype(FONT_PATH, 10)
                            draw.text((dx+2, curr_y+18), bottom_text, font=font_smaller, fill=0)
                        except:
                            draw.text((dx+2, curr_y+18), bottom_text[:3], font=font_tiny, fill=0)
                    else:
                        draw.text((dx+2, curr_y+18), bottom_text, font=font_tiny, fill=0)
        curr_y += row_h
    push_image(img, 3)

# --- 天气 ---
def get_weatherapi_weather():
    result = {
        "city": CITY_DISPLAY_NAME.split("|")[0].strip(), 
        "weather": "未知", 
        "temp_curr": 0, 
        "temp_low": 0, 
        "temp_high": 0, 
        "wind_info": "无数据", 
        "humidity": "0%", 
        "feel_temp": "N/A", 
        "sunrise": "--:--", 
        "sunset": "--:--", 
        "forecasts": []
    }
    
    if not WEATHERAPI_KEY:
        print("⚠️ 未设置 WEATHERAPI_KEY")
        return result

    base_url = "https://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": WEATHERAPI_LOCATION,
        "days": 3,
        "aqi": "no",
        "alerts": "no",
        "lang": "zh"
    }

    try:
        resp = requests.get(base_url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        current = data["current"]
        result["temp_curr"] = int(current["temp_c"])
        result["weather"] = current["condition"]["text"]
        result["humidity"] = f"{current['humidity']}%"
        result["feel_temp"] = f"{current['feelslike_c']}°C"
        wind_kph = current["wind_kph"]
        wind_dir = current["wind_dir"]
        result["wind_info"] = f"{wind_kph}kph {wind_dir}"
        today = data["forecast"]["forecastday"][0]
        result["temp_low"] = int(today["day"]["mintemp_c"])
        result["temp_high"] = int(today["day"]["maxtemp_c"])
        astro = today["astro"]
        result["sunrise"] = astro["sunrise"]
        result["sunset"] = astro["sunset"]
        for i in range(1, 3):
            if i < len(data["forecast"]["forecastday"]):
                d = data["forecast"]["forecastday"][i]
                result["forecasts"].append({
                    "date": d["date"][5:],
                    "weather": d["day"]["condition"]["text"],
                    "temp_low": int(d["day"]["mintemp_c"]),
                    "temp_high": int(d["day"]["maxtemp_c"])
                })
        return result
    except Exception as e:
        print(f"❌ 天气请求失败: {e}")
        return result

def task_weather_dashboard():
    if "4" not in ENABLED_PAGES: return
    print("生成 Page 4: 天气...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    weather = get_weatherapi_weather()
    if weather["temp_curr"] == 0 and not weather["forecasts"]:
        draw.text((20, 50), "天气数据获取失败", font=font_item, fill=0)
        push_image(img, 4)
        return

    draw.text((20, 10), CITY_DISPLAY_NAME, font=font_title, fill=0)
    now_beijing = datetime.utcnow() + timedelta(hours=8)
    update_time = now_beijing.strftime("%H:%M")
    time_text = f"更新: {update_time}"
    try:
        bbox = draw.textbbox((0, 0), time_text, font=font_small)
        time_width = bbox[2] - bbox[0]
    except:
        time_width = len(time_text) * 8
    draw.text((390 - time_width, 12), time_text, font=font_small, fill=0)

    draw.text((25, 40), f"{weather['temp_curr']}°C", font=font_48, fill=0)
    draw.text((25, 100), f"{weather['temp_low']}°/{weather['temp_high']}°", font=font_item, fill=0)
    draw.text((150, 45), f"{weather['weather']}", font=font_36, fill=0)
    draw.text((25, 135), f"日出 {weather['sunrise']}   日落 {weather['sunset']}", font=font_item, fill=0)
    draw.line([(20, 160), (380, 160)], fill=0, width=1)
    x_positions = [30, 200]
    for i, day in enumerate(weather['forecasts'][:2]):
        x = x_positions[i]
        draw.text((x, 175), day["date"], font=font_item, fill=0)
        draw.text((x, 200), day["weather"], font=font_item, fill=0)
        draw.text((x, 220), f"{day['temp_low']}°~{day['temp_high']}°", font=font_item, fill=0)
    advice = get_clothing_advice(weather['temp_curr'])
    draw.line([(20, 250), (380, 250)], fill=0, width=1)
    advice_lines = [advice[i:i+18] for i in range(0, len(advice), 18)]
    for i, line in enumerate(advice_lines[:2]):
        draw.text((20, 262 + i*24), f"[衣] {line}", font=font_item, fill=0)
    push_image(img, 4)

# ================= 主程序 =================
if __name__ == "__main__":
    if not API_KEY or not MAC_ADDRESS:
        print("❌ 请配置 GitHub Secrets")
        exit(1)
        
    print("🚀 开始推送...")
    task_hotlist()
    task_huangli()
    task_calendar()
    task_weather_dashboard()
    print("🎉 全部完成！")
