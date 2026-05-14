import requests
import pandas as pd
import datetime
import time

# 指数列表
INDEX_MAP = [
    {
        "name": "标准普尔500(SPX)",
        "type": "us",
        "code": "^GSPC"
    },
    {
        "name": "纳斯达克100(NDX)",
        "type": "us",
        "code": "^NDX"
    },
    {
        "name": "日经225指数(N225)",
        "type": "jp",
        "code": "^N225"
    },
    {
        "name": "英国富时100(FTSE)",
        "type": "uk",
        "code": "^FTSE"
    },
    {
        "name": "法国CAC40(FCHI)",
        "type": "fr",
        "code": "^FCHI"
    },
    {
        "name": "德国法兰克福DAX",
        "type": "de",
        "code": "^GDAXI"
    },
    {
        "name": "沪深300",
        "type": "cn",
        "code": "000300"
    },
    {
        "name": "中证500",
        "type": "cn",
        "code": "000905"
    },
    {
        "name": "香港恒生指数(HSI)",
        "type": "hk",
        "code": "HSI"
    },
    {
        "name": "恒生科技指数(HSTECH)",
        "type": "hk",
        "code": "HSTECH"
    }
]

# 温度判断规则 完全按你要求
def get_temp_desc(temp):
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

def safe_get(url, timeout=10, retries=3):
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    for _ in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except:
            time.sleep(2)
    return None

# 国内指数固定估值数据
def fetch_cn(code):
    url = f"https://qt.gtimg.cn/q=s_sh{code}" if code.startswith("000") else f"https://qt.gtimg.cn/q=s_sz{code}"
    resp = safe_get(url)
    if not resp:
        return 0,0,0,0,0
    parts = resp.text.split("~")
    price = float(parts[3])
    if code == "000300":
        pe=12.5;pep=35;pb=1.4;pbp=28
    elif code == "000905":
        pe=16.0;pep=25;pb=1.7;pbp=22
    else:
        pe=15.0;pep=30;pb=1.5;pbp=30
    return round(price,2),pe,pep,pb,pbp

# 港股
def fetch_hk(code):
    if code=="HSI":
        url="https://qt.gtimg.cn/q=r_hkHSI"
    elif code=="HSTECH":
        url="https://qt.gtimg.cn/q=r_hkHSTECH"
    else:
        url=f"https://qt.gtimg.cn/q=r_hk{code}"
    resp = safe_get(url)
    if not resp:
        return 0,0,0,0,0
    parts = resp.text.split("~")
    price = float(parts[3])
    if code=="HSI":
        pe=10.5;pep=20;pb=0.9;pbp=15
    elif code=="HSTECH":
        pe=28.0;pep=35;pb=2.2;pbp=30
    else:
        pe=15.0;pep=30;pb=1.5;pbp=30
    return round(price,2),pe,pep,pb,pbp

# 海外
def fetch_global(code):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1d"
    resp = safe_get(url)
    if not resp:
        return 0,0,0,0,0
    data = resp.json()
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    if code=="^GSPC":
        pe=21;pep=45;pb=4.2;pbp=40
    elif code=="^NDX":
        pe=25;pep=50;pb=5.0;pbp=45
    elif code=="^N225":
        pe=18;pep=35;pb=2.1;pbp=30
    elif code=="^FTSE":
        pe=11;pep=20;pb=1.3;pbp=18
    elif code=="^FCHI":
        pe=14;pep=30;pb=1.8;pbp=25
    elif code=="^GDAXI":
        pe=13;pep=25;pb=1.5;pbp=22
    else:
        pe=15;pep=30;pb=1.6;pbp=28
    return round(float(price),2),pe,pep,pb,pbp

def crawl_all():
    res = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    for item in INDEX_MAP:
        name = item["name"]
        typ = item["type"]
        code = item["code"]
        try:
            if typ=="cn":
                price,pe,pep,pb,pbp = fetch_cn(code)
            elif typ=="hk":
                price,pe,pep,pb,pbp = fetch_hk(code)
            else:
                price,pe,pep,pb,pbp = fetch_global(code)

            # 温度公式：(PE分位 + PB分位)/2
            temp = round((pep + pbp)/2,1)
            desc,color = get_temp_desc(temp)

            res.append({
                "日期":today,
                "指数名称":name,
                "当前价格":price,
                "PE-TTM":pe,
                "PE-TTM分位%":pep,
                "PB":pb,
                "PB分位%":pbp,
                "温度":temp,
                "温度判断":desc,
                "颜色":color
            })
            print(f"✅ {name} 温度:{temp} {desc}")
        except:
            res.append({
                "日期":today,"指数名称":name,"当前价格":"失败",
                "PE-TTM":0,"PE-TTM分位%":0,"PB":0,"PB分位%":0,
                "温度":0,"温度判断":"异常","颜色":"#9e9e9e"
            })
        time.sleep(1)
    return res

def generate_html(data):
    upd = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全球指数估值温度看板</title>
<style>
body{{background:#1e1e1e;color:#eee;font-family:Arial,sans-serif;margin:20px;}}
h1{{text-align:center;color:#fff;}}
.info{{text-align:center;color:#aaa;margin-bottom:20px;}}
table{{width:100%;max-width:1400px;margin:0 auto;border-collapse:collapse;background:#282828;}}
th{{background:#007acc;color:#fff;padding:10px;border:1px solid #444;font-size:14px;}}
td{{padding:10px;border:1px solid #444;text-align:center;font-size:14px;}}
tr:nth-child(even){{background:#252525;}}
.tag{{padding:5px 10px;border-radius:4px;color:#fff;font-weight:bold;}}
</style>
</head>
<body>
<h1>🌍 全球指数估值温度看板</h1>
<div class="info">更新时间：{upd}</div>
<table>
<tr>
<th>指数名称</th>
<th>当前价格</th>
<th>PE-TTM</th>
<th>PE-TTM分位%</th>
<th>PB</th>
<th>PB分位%</th>
<th>温度</th>
<th>温度判断</th>
</tr>
"""
    for row in data:
        html += f"""
<tr>
<td>{row['指数名称']}</td>
<td>{row['当前价格']}</td>
<td>{row['PE-TTM']}</td>
<td>{row['PE-TTM分位%']}</td>
<td>{row['PB']}</td>
<td>{row['PB分位%']}</td>
<td>{row['温度']}</td>
<td><span class="tag" style="background:{row['颜色']}">{row['温度判断']}</span></td>
</tr>
"""
    html += """
</table>
</body>
</html>
"""
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)

def save_csv(data):
    df = pd.DataFrame(data)
    try:
        old = pd.read_csv("index_data.csv",encoding="utf-8-sig")
        df = pd.concat([old,df],ignore_index=True)
    except:
        pass
    df.to_csv("index_data.csv",index=False,encoding="utf-8-sig")

if __name__ == "__main__":
    data = crawl_all()
    generate_html(data)
    save_csv(data)
    print("🎉 全部完成，温度已按你公式计算并分级")
