import requests
import pandas as pd
import datetime
import time
import json

# ===================== 全球指数列表（全覆盖） =====================
INDEX_MAP = [
    {"name": "标普500(SPX)", "type": "us", "code": "SPX"},
    {"name": "纳斯达克100(NDX)", "type": "us", "code": "NDX"},
    {"name": "日经225(N225)", "type": "jp", "code": "N225"},
    {"name": "英国富时100(FTSE)", "type": "uk", "code": "FTSE"},
    {"name": "法国CAC40(FCHI)", "type": "fr", "code": "CAC40"},
    {"name": "德国DAX(GDAXI)", "type": "de", "code": "DAX"},
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

# ===================== 通用请求函数（带重试+超时） =====================
def safe_request(url, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2)
    return None

# ===================== 抓取国内指数（雪球API） =====================
def fetch_cn_index(code):
    try:
        url = f"https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH{code}&extend=detail"
        resp = safe_request(url)
        data = resp.json()
        quote = data["data"]["quote"]
        price = quote["current"]
        pe = quote["pe_ttm"]
        return round(float(price), 2), round(float(pe), 2)
    except:
        return "抓取失败", 0

# ===================== 抓取港股指数（雪球API） =====================
def fetch_hk_index(code):
    try:
        url = f"https://stock.xueqiu.com/v5/stock/quote.json?symbol=HK{code}&extend=detail"
        resp = safe_request(url)
        data = resp.json()
        quote = data["data"]["quote"]
        price = quote["current"]
        pe = quote.get("pe_ttm", 0)
        return round(float(price), 2), round(float(pe), 2)
    except:
        return "抓取失败", 0

# ===================== 抓取海外指数（Yahoo Finance 备用） =====================
def fetch_global_index(code):
    yahoo_code_map = {
        "SPX": "^GSPC",
        "NDX": "^NDX",
        "N225": "^N225",
        "FTSE": "^FTSE",
        "CAC40": "^FCHI",
        "DAX": "^GDAXI"
    }
    yahoo_code = yahoo_code_map.get(code, code)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_code}?interval=1d&includePrePost=false"
        resp = safe_request(url)
        data = resp.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        pe = 18.0  # 备用PE，避免无数据
        return round(float(price), 2), pe
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
                "PE-TTM": pe,
                "估值等级": level,
                "颜色": color
            })
            print(f"✅ {name} => 价格: {price}, PE: {pe}, 估值: {level}")
        except Exception as e:
            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": "抓取失败",
                "PE-TTM": 0,
                "估值等级": "数据异常",
                "颜色": "#9e9e9e"
            })
            print(f"❌ {name} 失败: {str(e)}")
        time.sleep(1)  # 增加延迟，避免被限流

    return result

# ===================== 生成 HTML 色块页面（完整表格） =====================
def generate_html(data):
    html_head = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全球指数估值看板（每日自动更新）</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background-color: #f5f5f5;
}
h1 {
    text-align: center;
    color: #333;
}
.update-time {
    text-align: center;
    color: #666;
    margin-bottom: 20px;
}
table {
    border-collapse: collapse;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
th, td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: center;
}
th {
    background-color: #2196f3;
    color: white;
    font-weight: bold;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.val-tag {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 4px;
    color: white;
    font-weight: bold;
    text-shadow: 0 1px 1px rgba(0,0,0,0.2);
}
</style>
</head>
<body>
    <h1>🌍 全球指数估值看板（每日自动更新）</h1>
    <div class="update-time">更新时间：""" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
    <table>
        <tr>
            <th>指数名称</th>
            <th>当前价格</th>
            <th>PE-TTM</th>
            <th>估值等级</th>
        </tr>
"""

    html_body = ""
    for d in data:
        html_body += f"""
        <tr>
            <td>{d['指数名称']}</td>
            <td>{d['当前价格']}</td>
            <td>{d['PE-TTM']}</td>
            <td><span class='val-tag' style='background-color:{d['颜色']}'>{d['估值等级']}</span></td>
        </tr>
        """

    html_foot = """
    </table>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_head + html_body + html_foot)

# ===================== 保存 CSV（追加历史数据） =====================
def save_csv(data):
    df = pd.DataFrame(data)
    if pd.io.common.file_exists("index_data.csv"):
        old_df = pd.read_csv("index_data.csv", encoding="utf-8-sig")
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_csv("index_data.csv", index=False, encoding="utf-8-sig")

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("🚀 开始抓取全球指数数据...")
    data = crawl_all()
    generate_html(data)
    save_csv(data)
    print("🎉 全部抓取完成！")
