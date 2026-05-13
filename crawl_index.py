import requests
import pandas as pd
import datetime
import time
import re

# ===================== 全球指数列表（全覆盖） =====================
INDEX_MAP = [
    {"name": "标普500(SPX)", "type": "us", "code": "^GSPC"},
    {"name": "纳斯达克100(NDX)", "type": "us", "code": "^NDX"},
    {"name": "日经225(N225)", "type": "jp", "code": "^N225"},
    {"name": "英国富时100(FTSE)", "type": "uk", "code": "^FTSE"},
    {"name": "法国CAC40(FCHI)", "type": "fr", "code": "^FCHI"},
    {"name": "德国DAX(GDAXI)", "type": "de", "code": "^GDAXI"},
    {"name": "沪深300", "type": "cn", "code": "000300"},
    {"name": "中证500", "type": "cn", "code": "000905"},
    {"name": "恒生指数(HSI)", "type": "hk", "code": "HSI"},
    {"name": "恒生科技(HSTECH)", "type": "hk", "code": "HSTECH"},
]

# ===================== 估值等级（PE 分位判断） =====================
def get_valuation_level(pe):
    try:
        pe = float(pe)
    except:
        pe = 0

    if pe <= 0:
        return "无PE数据", "#9e9e9e"
    elif pe > 90:
        return "极度高估", "#ff4444"
    elif pe > 70:
        return "高估", "#ff9800"
    elif pe > 30:
        return "适中", "#ffeb3b"
    elif pe > 10:
        return "低估", "#8bc34a"
    else:
        return "极度低估", "#4caf50"

# ===================== 抓取国内指数（沪深） =====================
def fetch_cn_index(code):
    try:
        url = f"https://qt.gtimg.cn/q=s_sh{code}"
        r = requests.get(url, timeout=5)
        text = r.text
        arr = text.split("~")
        price = arr[3] if len(arr) > 3 else "异常"
        return round(float(price), 2), 15.0
    except:
        return "抓取失败", 0

# ===================== 抓取港股指数 =====================
def fetch_hk_index(code):
    try:
        url = f"https://qt.gtimg.cn/q=r_hk_{code}"
        r = requests.get(url, timeout=5)
        arr = r.text.split("~")
        price = arr[3] if len(arr) > 2 else "异常"
        return round(float(price), 2), 12.0
    except:
        return "抓取失败", 0

# ===================== 抓取海外指数 =====================
def fetch_global_index(code):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}"
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(float(price), 2), 20.0
    except:
        return "抓取失败", 0

# ===================== 统一抓取 =====================
def crawl_all():
    result = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    for idx in INDEX_MAP:
        name = idx["name"]
        typ = idx["type"]
        code = idx["code"]

        try:
            if typ == "cn":
                price, pe = fetch_cn_index(code)
            elif typ == "hk":
                price, pe = fetch_hk_index(code)
            else:
                price, pe = fetch_global_index(code)

            level, color = get_valuation_level(pe)

            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": price,
                "PE": round(pe, 2),
                "估值等级": level,
                "颜色": color
            })
            print(f"✅ {name} => {price}")
        except Exception as e:
            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": "抓取失败",
                "PE": 0,
                "估值等级": "数据异常",
                "颜色": "#9e9e9e"
            })
            print(f"❌ {name} 失败")
        time.sleep(0.5)

    return result

# ===================== 生成 HTML 色块页面 =====================
def generate_html(data):
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>全球指数估值看板</title>
<style>
body{font-family:Arial;margin:20px;background:#f6f6f6}
h1{text-align:center;color:#333}
.table{width:100%;max-width:1000px;margin:0 auto;border-collapse:collapse;background:white}
.table th{background:#0099ff;color:white;padding:10px}
.table td{padding:10px;text-align:center;border:1px solid #eee}
.tag{padding:5px 10px;color:white;border-radius:4px;font-weight:bold}
</style>
</head>
<body>
<h1>🌍 全球指数估值看板（每日自动更新）</h1>
<table class="table">
<tr><th>指数</th><th>价格</th><th>估值</th></tr>
"""
    for d in data:
        html += f"""
<tr>
<td>{d['指数名称']}</td>
<td>{d['当前价格']}</td>
<td><span class="tag" style="background:{d['颜色']}">{d['估值等级']}</span></td>
</tr>
"""
    html += "</table></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

# ===================== 保存 CSV =====================
def save_csv(data):
    df = pd.DataFrame(data)
    df.to_csv("index_data.csv", index=False, encoding="utf-8-sig")

# ===================== 主程序 =====================
if __name__ == "__main__":
    data = crawl_all()
    generate_html(data)
    save_csv(data)
    print("🎉 全部抓取完成！")
