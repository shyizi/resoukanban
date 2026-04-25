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
# ⚙️ 第三部分：字体 & 工具
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

def get_wrapped_lines(text, max_chars=18):
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines

def get_clothing_advice(temp):
    try:
        t = int(temp)
        if t >= 28: return "短袖、短裤，防晒补水。"
        elif t >= 22: return "T恤、薄长裤。"
        elif t >= 16: return "长袖、卫衣、薄外套。"
        elif t >= 10: return "夹克、风衣。"
        elif t >= 5: return "大衣、薄羽绒服。"
        else: return "厚羽绒服，防寒保暖。"
    except:
        return "根据体感调整着装。"

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

# =====================================================================
# 📅 以下是 **完整复制 hl.py 的全部黄历代码**（100% 原版）
# =====================================================================

def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def get_huangli_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        fonts = ["SourceHanSansCN-Regular.ttf", "msyh.ttc", "simhei.ttf"]
        for f in fonts:
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
        return ImageFont.load_default(size=size)

def render_auto_text(draw, x, y, text, max_w, max_lines, init_size, line_h):
    one_char = text_width(draw, "一", get_huangli_font(init_size))
    usable_w = max_w - one_char
    font = get_huangli_font(init_size)
    while True:
        lines = []
        current = ""
        ok = True
        for c in text:
            if text_width(draw, current + c, font) <= usable_w:
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

def get_huangli_data():
    from lunar_python import Lunar, Solar
    now = dt.datetime.now()
    solar = Solar(now.year, now.month, now.day, now.hour, now.minute, now.second)
    lunar = Lunar.fromSolar(solar)
    gongli = f"{now.year}年{now.month:02d}月{now.day:02d}日 周{['一','二','三','四','五','六','日'][now.weekday()]}"
    nongli = lunar.toFullString().split(" ")[0]
    sx = lunar.getShengXiao()
    chong = lunar.getChong()
    chong_str = f"冲{chong}"
    yi = lunar.getYi()
    ji = lunar.getJi()
    return {
        "gongli": gongli,
        "nongli": nongli,
        "sx": sx,
        "chong_str": chong_str,
        "yi": "、".join(yi),
        "ji": "、".join(ji)
    }

# 直接生成黄历图片（hl.py 原版）
def generate_huangli_image():
    W, H = 400, 300
    img = Image.new("1", (W, H), 1)
    draw = ImageDraw.Draw(img)
    data = get_huangli_data()
    ft_title = get_huangli_font(34)
    ft_date = get_huangli_font(22)
    ft_info = get_huangli_font(20)
    title = "今日黃曆"
    tw = text_width(draw, title, ft_title)
    draw.text(((W - tw)//2, 15), title, font=ft_title, fill=0)
    draw.line([(30, 60), (370, 60)], 0, 1)
    dw = text_width(draw, data["gongli"], ft_date)
    draw.text(((W - dw)//2, 68), data["gongli"], font=ft_date, fill=0)
    draw.line([(25, 100), (375, 100)], 0, 2)
    draw.text((30, 115), f"農曆：{data['nongli']}", font=ft_info, fill=0)
    draw.text((30, 145), f"生肖：{data['sx']}    {data['chong_str']}", font=ft_info, fill=0)
    draw.text((30, 175), "宜：", font=get_huangli_font(19), fill=0)
    render_auto_text(draw, 65, 175, data["yi"], 315, 2, 19, 28)
    draw.text((30, 230), "忌：", font=get_huangli_font(19), fill=0)
    render_auto_text(draw, 65, 230, data["ji"], 315, 2, 19, 28)
    return img

# =====================================================================
# 🚀 任务：黄历第2屏（直接用 hl.py 生成的图）
# =====================================================================
def task_huangli():
    if "2" not in ENABLED_PAGES:
        return
    print("📅 生成黄历图片（来自 hl.py 原版逻辑）")
    img = generate_huangli_image()
    push_image(img, 2)

# =====================================================================
# 热搜、日历、天气（完全保持你原来的逻辑不变）
# =====================================================================

def get_solar_term(year, month, day):
    term_table = {
        (2024,2,4):"立春", (2024,2,19):"雨水", (2024,3,5):"惊蛰", (2024,3,20):"春分",
        (2024,4,4):"清明", (2024,4,19):"谷雨", (2024,5,5):"立夏", (2024,5,20):"小满",
        (2024,6,5):"芒种", (2024,6,21):"夏至", (2024,7,6):"小暑", (2024,7,22):"大暑",
        (2024,8,7):"立秋", (2024,8,22):"处暑", (2024,9,7):"白露", (2024,9,22):"秋分",
        (2024,10,8):"寒露", (2024,10,23):"霜降", (2024,11,7):"立冬", (2024,11,22):"小雪",
        (2024,12,6):"大雪", (2024,12,21):"冬至", (2025,1,5):"小寒", (2025,1,20):"大寒"
    }
    return term_table.get((year, month, day), None)

def get_lunar_or_festival(y, m, d):
    term = get_solar_term(y, m, d)
    if term: return term
    solar_fests = {(1,1):"元旦",(2,14):"情人节",(3,8):"妇女节",(4,1):"愚人节",(5,1):"劳动节",(6,1):"儿童节",(7,1):"建党节",(8,1):"建军节",(9,10):"教师节",(10,1):"国庆节",(12,25):"圣诞节"}
    if (m,d) in solar_fests: return solar_fests[(m,d)]
    try:
        lunar = ZhDate.from_datetime(datetime(y,m,d))
        lm,ld = lunar.lunar_month, lunar.lunar_day
        lunar_fests = {(1,1):"春节",(1,15):"元宵节",(5,5):"端午节",(7,7):"七夕",(8,15):"中秋",(9,9):"重阳",(12,30):"除夕"}
        if (lm,ld) in lunar_fests: return lunar_fests[(lm,ld)]
        days = ["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十","十一","十二","十三","十四","十五","十六","十七","十八","十九","二十","廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"]
        months = ["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","冬月","腊月"]
        if ld ==1: return months[lm-1]
        return days[ld-1]
    except:
        return ""

def get_hotlist_data(source):
    titles = []
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
            titles = [f"{item['full_name']}: {item['description'][:50] if item['description'] else ''}" for item in res['items']]
    except Exception as e:
        titles = ["数据获取失败"]*10
    return titles[:20]

def task_hotlist():
    source_map = {"zhihu": "知乎热榜", "bilibili": "B站热搜", "github": "GitHub热门"}
    titles = get_hotlist_data(HOTLIST_SOURCE)
    title_display = source_map.get(HOTLIST_SOURCE, "热搜")
    if "1" in ENABLED_PAGES:
        img1 = Image.new('1', (400,300), 255)
        draw = ImageDraw.Draw(img1)
        draw.rounded_rectangle([(10,10),(390,45)], radius=8, fill=0)
        draw.text((20,15), f"◆ {title_display}", font=font_title, fill=255)
        y = 55
        for i in range(min(12, len(titles))):
            if y > 280: break
            draw.text((15, y), f"{i+1:02d}", font=font_item, fill=0)
            line = titles[i]
            if len(line) > 22:
                line = line[:22] + "…"
            draw.text((50, y), line, font=font_item, fill=0)
            y += 20
        push_image(img1, 1)

def task_calendar():
    if "3" not in ENABLED_PAGES: return
    img = Image.new('1', (400,300), 255)
    draw = ImageDraw.Draw(img)
    now = datetime.utcnow() + timedelta(hours=8)
    y,m,today = now.year, now.month, now.day
    draw.text((20,10), str(m), font=font_huge, fill=0)
    draw.text((90,20), now.strftime("%B"), font=font_title, fill=0)
    draw.text((90,48), str(y), font=font_item, fill=0)
    draw.line([(20,78),(380,78)], width=2, fill=0)
    headers = ["日","一","二","三","四","五","六"]
    col_w = 53
    for i,h in enumerate(headers):
        draw.text((25+i*col_w,88), h, font=font_small, fill=0)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(y,m)
    curr_y = 115
    for week in cal:
        for c,day in enumerate(week):
            if day !=0:
                dx = 25 + c*col_w
                if day == today:
                    draw.rounded_rectangle([(dx-3,curr_y-2),(dx+35,curr_y+32)], radius=5, outline=0)
                draw.text((dx+2,curr_y), str(day), font=font_item, fill=0)
                txt = get_lunar_or_festival(y,m,day)
                if txt:
                    draw.text((dx+2,curr_y+18), txt[:3], font=font_tiny, fill=0)
        curr_y +=38
    push_image(img,3)

def get_weatherapi_weather():
    result = {"city":"未知","weather":"未知","temp_curr":0,"temp_low":0,"temp_high":0,"wind_info":"-","humidity":"-","feel_temp":"-","sunrise":"--:--","sunset":"--:--","forecasts":[]}
    if not WEATHERAPI_KEY: return result
    try:
        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {"key":WEATHERAPI_KEY,"q":WEATHERAPI_LOCATION,"days":3,"lang":"zh"}
        res = requests.get(url,params=params,timeout=15).json()
        curr = res["current"]
        result["temp_curr"] = int(curr["temp_c"])
        result["weather"] = curr["condition"]["text"]
        result["humidity"] = f"{curr['humidity']}%"
        result["feel_temp"] = f"{curr['feelslike_c']}°C"
        result["wind_info"] = f"{curr['wind_kph']}kph"
        day = res["forecast"]["forecastday"][0]
        result["temp_low"] = int(day["day"]["mintemp_c"])
        result["temp_high"] = int(day["day"]["maxtemp_c"])
        result["sunrise"] = day["astro"]["sunrise"]
        result["sunset"] = day["astro"]["sunset"]
        for i in range(1,3):
            d = res["forecast"]["forecastday"][i]
            result["forecasts"].append({
                "date":d["date"][5:],
                "weather":d["day"]["condition"]["text"],
                "temp_low":int(d["day"]["mintemp_c"]),
                "temp_high":int(d["day"]["maxtemp_c"])
            })
    except:
        pass
    return result

def task_weather_dashboard():
    if "4" not in ENABLED_PAGES: return
    img = Image.new('1',(400,300),255)
    draw = ImageDraw.Draw(img)
    w = get_weatherapi_weather()
    draw.text((20,10), CITY_DISPLAY_NAME, font=font_title, fill=0)
    draw.text((25,40), f"{w['temp_curr']}°C", font=font_48, fill=0)
    draw.text((25,100), f"{w['temp_low']}°~{w['temp_high']}°", font=font_item, fill=0)
    draw.text((150,45), w["weather"], font=font_36, fill=0)
    draw.text((25,135), f"日出 {w['sunrise']} 日落 {w['sunset']}", font=font_item, fill=0)
    push_image(img,4)

# =====================================================================
# 主程序
# =====================================================================
if __name__ == "__main__":
    if not API_KEY or not MAC_ADDRESS:
        print("❌ 请配置 API_KEY 和 MAC_ADDRESS")
        exit(1)
    print("🚀 开始推送墨水屏")
    task_hotlist()       # 第1屏：热搜
    task_huangli()       # 第2屏：黄历（hl.py原版）
    task_calendar()      # 第3屏：日历
    task_weather_dashboard() # 第4屏：天气
    print("🎉 全部推送完成")
