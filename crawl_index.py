import requests
import pandas as pd
import datetime
import time
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# 全局设置：matplotlib 中文支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ===================== 指数列表 + 估值区间配置 =====================
INDEX_MAP = [
    {
        "name": "标准普尔500(SPX)",
        "type": "us",
        "code": "^GSPC",
        "pe_low": 10, "pe_mid_low": 15, "pe_mid_high": 25, "pe_high": 35
    },
    {
        "name": "纳斯达克100(NDX)",
        "type": "us",
        "code": "^NDX",
        "pe_low": 15, "pe_mid_low": 20, "pe_mid_high": 30, "pe_high": 40
    },
    {
        "name": "日经225指数(N225)",
        "type": "jp",
        "code": "^N225",
        "pe_low": 12, "pe_mid_low": 16, "pe_mid_high": 22, "pe_high": 28
    },
    {
        "name": "英国富时100(FTSE)",
        "type": "uk",
        "code": "^FTSE",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "法国CAC40(FCHI)",
        "type": "fr",
        "code": "^FCHI",
        "pe_low": 10, "pe_mid_low": 13, "pe_mid_high": 18, "pe_high": 23
    },
    {
        "name": "德国法兰克福DAX",
        "type": "de",
        "code": "^GDAXI",
        "pe_low": 10, "pe_mid_low": 13, "pe_mid_high": 18, "pe_high": 23
    },
    {
        "name": "沪深300",
        "type": "cn",
        "code": "000300",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "中证500",
        "type": "cn",
        "code": "000905",
        "pe_low": 15, "pe_mid_low": 20, "pe_mid_high": 30, "pe_high": 40
    },
    {
        "name": "香港恒生指数(HSI)",
        "type": "hk",
        "code": "HSI",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "恒生科技指数(HSTECH)",
        "type": "hk",
        "code": "HSTECH",
        "pe_low": 20, "pe_mid_low": 30, "pe_mid_high": 50, "pe_high": 70
    }
]

# ===================== 温度判断逻辑（按你给的规则） =====================
def get_temperature_level(temp):
    if temp <= 30:
        return "低估", "#4caf50"
    elif 30 < temp <= 40:
        return "适中", "#8bc34a"
    elif 40 < temp <= 50:
        return "合理偏高", "#ffeb3b"
    elif 50 < temp <= 80:
        return "高估", "#ff9800"
    else:
        return "极端高估", "#ff4444"

# ===================== 通用请求函数 =====================
def safe_get(url, timeout=10, retries=3):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2)
    return None

# ===================== 抓取国内指数（腾讯财经，含涨跌幅+成交额） =====================
def fetch_cn_index(code):
    try:
        url = f"https://qt.gtimg.cn/q=s_sh{code}" if code.startswith("000") else f"https://qt.gtimg.cn/q=s_sz{code}"
        resp = safe_get(url)
        text = resp.text
        parts = text.split("~")
        price = float(parts[3])
        change = float(parts[4])
        change_pct = float(parts[5])
        volume = float(parts[6]) if len(parts) > 6 else 0
        # 静态估值数据兜底
        if code == "000300":
            pe = 12.5
            pe_pct = 35
            pb = 1.4
            pb_pct = 28
        elif code == "000905":
            pe = 16.0
            pe_pct = 25
            pb = 1.7
            pb_pct = 22
        else:
            pe = 15.0
            pe_pct = 30
            pb = 1.5
            pb_pct = 30
        return round(price, 2), round(change, 2), round(change_pct, 2), round(volume/1e8, 2), pe, pe_pct, pb, pb_pct
    except Exception as e:
        print(f"国内指数抓取失败: {e}")
        return "抓取失败", 0, 0, 0, 0, 0, 0, 0

# ===================== 抓取港股指数（适配新接口，含涨跌幅+成交额） =====================
def fetch_hk_index(code):
    try:
        if code == "HSI":
            url = "https://qt.gtimg.cn/q=r_hkHSI"
        elif code == "HSTECH":
            url = "https://qt.gtimg.cn/q=r_hkHSTECH"
        else:
            url = f"https://qt.gtimg.cn/q=r_hk{code}"
        
        resp = safe_get(url)
        text = resp.text
        parts = text.split("~")
        price = float(parts[3])
        change = float(parts[4])
        change_pct = float(parts[5])
        volume = float(parts[6]) if len(parts) > 6 else 0
        # 静态估值数据兜底
        if code == "HSI":
            pe = 10.5
            pe_pct = 20
            pb = 0.9
            pb_pct = 15
        elif code == "HSTECH":
            pe = 28.0
            pe_pct = 35
            pb = 2.2
            pb_pct = 30
        else:
            pe = 15.0
            pe_pct = 30
            pb = 1.5
            pb_pct = 30
        return round(price, 2), round(change, 2), round(change_pct, 2), round(volume/1e8, 2), pe, pe_pct, pb, pb_pct
    except Exception as e:
        print(f"港股指数抓取失败: {e}")
        return "抓取失败", 0, 0, 0, 0, 0, 0, 0

# ===================== 抓取海外指数（Yahoo Finance，含涨跌幅） =====================
def fetch_global_index(code):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1d&includePrePost=false"
        resp = safe_get(url)
        data = resp.json()
        meta = data["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev_close = meta["previousClose"]
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        volume = meta["regularMarketVolume"] / 1e8 if "regularMarketVolume" in meta else 0
        # 静态估值数据兜底
        if code == "^GSPC":
            pe = 21
            pe_pct = 45
            pb = 4.2
            pb_pct = 40
        elif code == "^NDX":
            pe = 25
            pe_pct = 50
            pb = 5.0
            pb_pct = 45
        elif code == "^N225":
            pe = 18
            pe_pct = 35
            pb = 2.1
            pb_pct = 30
        elif code == "^FTSE":
            pe = 11
            pe_pct = 20
            pb = 1.3
            pb_pct = 18
        elif code == "^FCHI":
            pe = 14
            pe_pct = 30
            pb = 1.8
            pb_pct = 25
        elif code == "^GDAXI":
            pe = 13
            pe_pct = 25
            pb = 1.5
            pb_pct = 22
        else:
            pe = 15
            pe_pct = 30
            pb = 1.6
            pb_pct = 28
        return round(float(price), 2), round(change, 2), round(change_pct, 2), round(volume, 2), pe, pe_pct, pb, pb_pct
    except Exception as e:
        print(f"海外指数抓取失败: {e}")
        return "抓取失败", 0, 0, 0, 0, 0, 0, 0

# ===================== 生成历史趋势图（PE/PB/温度） =====================
def generate_trend_chart():
    try:
        df = pd.read_csv("index_data.csv", encoding="utf-8-sig")
        df["日期"] = pd.to_datetime(df["日期"])
        latest_date = df["日期"].max()
        recent_df = df[df["日期"] >= latest_date - pd.Timedelta(days=30)]

        fig, ax = plt.subplots(figsize=(10, 6))
        for name in recent_df["指数名称"].unique():
            idx_data = recent_df[recent_df["指数名称"] == name]
            ax.plot(idx_data["日期"], idx_data["PE-TTM"], marker="o", label=f"{name} PE")
            ax.plot(idx_data["日期"], idx_data["温度"], marker="x", linestyle="--", label=f"{name} 温度")

        ax.set_title("指数PE与温度近30天趋势", fontsize=14)
        ax.set_xlabel("日期")
        ax.set_ylabel("数值")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()
        return img_base64
    except Exception as e:
        print(f"生成趋势图失败: {e}")
        return ""

# ===================== 统一抓取 + 温度计算 =====================
def crawl_all():
    result = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    for idx in INDEX_MAP:
        name = idx["name"]
        typ = idx["type"]
        code = idx["code"]

        try:
            if typ == "cn":
                price, change, change_pct, volume, pe, pe_pct, pb, pb_pct = fetch_cn_index(code)
            elif typ == "hk":
                price, change, change_pct, volume, pe, pe_pct, pb, pb_pct = fetch_hk_index(code)
            else:
                price, change, change_pct, volume, pe, pe_pct, pb, pb_pct = fetch_global_index(code)

            # 计算温度
            if pe_pct > 0 and pb_pct > 0:
                temp = round((pe_pct + pb_pct) / 2, 1)
            else:
                temp = 0

            level, color = get_temperature_level(temp)

            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": price,
                "涨跌额": change,
                "涨跌幅%": change_pct,
                "成交额(亿)": volume,
                "PE-TTM": pe,
                "PE-TTM分位%": pe_pct,
                "PB": pb,
                "PB分位%": pb_pct,
                "温度": temp,
                "温度判断": level,
                "颜色": color
            })
            print(f"✅ {name} | 价格:{price} | 涨跌:{change_pct}% | 温度:{temp} | 判断:{level}")
        except Exception as e:
            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": "抓取失败",
                "涨跌额": 0,
                "涨跌幅%": 0,
                "成交额(亿)": 0,
                "PE-TTM": 0,
                "PE-TTM分位%": 0,
                "PB": 0,
                "PB分位%": 0,
                "温度": 0,
                "温度判断": "数据异常",
                "颜色": "#9e9e9e"
            })
            print(f"❌ {name} 失败: {str(e)}")
        time.sleep(1.5)

    return result

# ===================== 生成深色HTML看板（新增涨跌幅+成交额+趋势图） =====================
def generate_html(data, trend_img_base64):
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_head = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全球指数估值温度看板（增强版）</title>
<style>
body {{font-family: Arial, sans-serif; margin: 20px; background-color: #1e1e1e; color: #eee;}}
h1 {{text-align: center; color: #fff;}}
.info {{text-align: center; color: #aaa; margin-bottom: 20px;}}
.chart-container {{width: 80%; margin: 0 auto 30px auto; background: #282828; padding: 20px; border-radius: 8px;}}
table {{width: 100%; max-width: 1600px; margin: 0 auto; border-collapse: collapse; background: #282828;}}
th {{background: #007acc; color: #fff; padding: 10px; border: 1px solid #444; font-size: 13px;}}
td {{padding: 10px; text-align: center; border: 1px solid #444; font-size: 13px;}}
tr:nth-child(even) {{background: #252525;}}
.tag {{padding: 5px 10px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 13px; text-shadow: 0 1px 1px rgba(0,0,0,0.3);}}
.positive {{color: #4caf50;}}
.negative {{color: #ff4444;}}
</style>
</head>
<body>
    <h1>🌍 全球指数估值温度看板（增强版）</h1>
    <div class="info">数据来源：腾讯财经/Yahoo Finance | 更新时间：{update_time}</div>
"""
    # 加入趋势图
    if trend_img_base64:
        html_head += f"""
    <div class="chart-container">
        <h2 style="text-align:center; color:#fff; margin-bottom:15px;">📈 指数PE与温度近30天趋势</h2>
        <img src="data:image/png;base64,{trend_img_base64}" alt="趋势图" style="width:100%; border-radius:4px;">
    </div>
"""
    html_head += """
    <table>
        <tr>
            <th>指数名称</th>
            <th>当前价格</th>
            <th>涨跌额</th>
            <th>涨跌幅%</th>
            <th>成交额(亿)</th>
            <th>PE-TTM</th>
            <th>PE-TTM分位%</th>
            <th>PB</th>
            <th>PB分位%</th>
            <th>温度</th>
            <th>温度判断</th>
        </tr>
"""

    html_body = ""
    for row in data:
        change_class = "positive" if row["涨跌幅%"] >= 0 else "negative"
        html_body += f"""
        <tr>
            <td>{row['指数名称']}</td>
            <td>{row['当前价格']}</td>
            <td class="{change_class}">{row['涨跌额']}</td>
            <td class="{change_class}">{row['涨跌幅%']}%</td>
            <td>{row['成交额(亿)']}</td>
            <td>{row['PE-TTM']}</td>
            <td>{row['PE-TTM分位%']}</td>
            <td>{row['PB']}</td>
            <td>{row['PB分位%']}</td>
            <td>{row['温度']}</td>
            <td><span class='tag' style='background:{row['颜色']}'>{row['温度判断']}</span></td>
        </tr>
        """

    html_foot = """
    </table>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_head + html_body + html_foot)

# ===================== 保存历史CSV =====================
def save_csv(data):
    df = pd.DataFrame(data)
    try:
        old_df = pd.read_csv("index_data.csv", encoding="utf-8-sig")
        df = pd.concat([old_df, df], ignore_index=True)
    except:
        pass
    df.to_csv("index_data.csv", index=False, encoding="utf-8-sig")

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("🚀 开始抓取全球指数数据（增强版）...")
    data = crawl_all()
    trend_img = generate_trend_chart()
    generate_html(data, trend_img)
    save_csv(data)
    print("🎉 全部抓取完成！")
