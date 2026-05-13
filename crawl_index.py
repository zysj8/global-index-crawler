import asyncio
import pandas as pd
import datetime
import time
from playwright.async_api import async_playwright

# 全部你要的指数 + 韭圈儿链接 + 专属PE估值区间
INDEX_MAP = [
    {
        "name": "标准普尔500(SPX)",
        "path": "https://www.jiuquaner.com/index/%5EGSPC",
        "pe_low": 10, "pe_mid_low": 15, "pe_mid_high": 25, "pe_high": 35
    },
    {
        "name": "纳斯达克100(NDX)",
        "path": "https://www.jiuquaner.com/index/%5ENDX",
        "pe_low": 15, "pe_mid_low": 20, "pe_mid_high": 30, "pe_high": 40
    },
    {
        "name": "日经225指数(N225)",
        "path": "https://www.jiuquaner.com/index/%5EN225",
        "pe_low": 12, "pe_mid_low": 16, "pe_mid_high": 22, "pe_high": 28
    },
    {
        "name": "英国富时100(FTSE)",
        "path": "https://www.jiuquaner.com/index/%5EFTSE",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "法国CAC40(FCHI)",
        "path": "https://www.jiuquaner.com/index/%5EFCHI",
        "pe_low": 10, "pe_mid_low": 13, "pe_mid_high": 18, "pe_high": 23
    },
    {
        "name": "德国法兰克福DAX",
        "path": "https://www.jiuquaner.com/index/%5EGDAXI",
        "pe_low": 10, "pe_mid_low": 13, "pe_mid_high": 18, "pe_high": 23
    },
    {
        "name": "沪深300",
        "path": "https://www.jiuquaner.com/index/000300",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "中证500",
        "path": "https://www.jiuquaner.com/index/000905",
        "pe_low": 15, "pe_mid_low": 20, "pe_mid_high": 30, "pe_high": 40
    },
    {
        "name": "香港恒生指数(HSI)",
        "path": "https://www.jiuquaner.com/index/HSI",
        "pe_low": 8, "pe_mid_low": 11, "pe_mid_high": 16, "pe_high": 20
    },
    {
        "name": "恒生科技指数(HSTECH)",
        "path": "https://www.jiuquaner.com/index/HSTECH",
        "pe_low": 20, "pe_mid_low": 30, "pe_mid_high": 50, "pe_high": 70
    }
]

# 估值五级 + 对应色块
def get_valuation_level(pe, pe_low, pe_mid_low, pe_mid_high, pe_high):
    try:
        pe = float(pe)
    except:
        pe = 0

    if pe <= 0:
        return "无PE数据", "#9e9e9e"
    elif pe > pe_high:
        return "极度高估", "#ff4444"
    elif pe > pe_mid_high:
        return "高估", "#ff9800"
    elif pe > pe_mid_low:
        return "适中", "#ffeb3b"
    elif pe > pe_low:
        return "低估", "#8bc34a"
    else:
        return "极度低估", "#4caf50"

# 单只指数从韭圈儿抓取：价格、PE-TTM、PE历史分位
async def fetch_one(index_info, page):
    name = index_info["name"]
    url = index_info["path"]
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_selector(".price", timeout=30000)

        price_text = await page.locator(".price").inner_text()
        price = float(price_text.replace(",", "").strip())

        pe_ttm_text = await page.xpath("//div[text()='PE(TTM)']/following-sibling::div").inner_text()
        pe_ttm = float(pe_ttm_text.replace(",", "").strip())

        pe_percent_text = await page.xpath("//div[text()='PE历史分位']/following-sibling::div").inner_text()

        return round(price, 2), round(pe_ttm, 2), pe_percent_text.strip()
    except Exception as e:
        print(f"❌ {name} 抓取失败: {str(e)[:60]}")
        return "抓取失败", 0.0, "无数据"

# 批量抓取全部指数
async def crawl_all():
    result = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )

        for item in INDEX_MAP:
            name = item["name"]
            price, pe, pe_pct = await fetch_one(item, page)
            level, color = get_valuation_level(pe,
                item["pe_low"], item["pe_mid_low"], item["pe_mid_high"], item["pe_high"])

            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": price,
                "PE_TTM": pe,
                "PE历史分位": pe_pct,
                "估值等级": level,
                "颜色": color
            })
            print(f"✅ {name} | 价格:{price} | PE:{pe} | 分位:{pe_pct} | 估值:{level}")
            time.sleep(2.5)

        await browser.close()
    return result

# 生成深色HTML估值看板
def generate_html(data):
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_head = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全球指数估值看板（韭圈儿数据源）</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;background:#1e1e1e;color:#eee;}}
h1{{text-align:center;color:#fff;}}
.info{{text-align:center;color:#aaa;margin-bottom:20px;}}
table{{width:100%;max-width:1200px;margin:0 auto;border-collapse:collapse;background:#282828;}}
th{{background:#007acc;color:#fff;padding:12px;border:1px solid #444;}}
td{{padding:12px;text-align:center;border:1px solid #444;}}
tr:nth-child(even){{background:#252525;}}
.tag{{padding:5px 10px;border-radius:4px;color:#fff;font-weight:bold;}}
</style>
</head>
<body>
<h1>🌍 全球指数估值看板</h1>
<div class="info">数据来源：韭圈儿 | 更新时间：{update_time}</div>
<table>
<tr>
<th>指数名称</th>
<th>当前价格</th>
<th>PE-TTM</th>
<th>PE历史分位</th>
<th>估值等级</th>
</tr>
"""
    html_body = ""
    for row in data:
        html_body += f"""
<tr>
<td>{row['指数名称']}</td>
<td>{row['当前价格']}</td>
<td>{row['PE_TTM']}</td>
<td>{row['PE历史分位']}</td>
<td><span class="tag" style="background:{row['颜色']}">{row['估值等级']}</span></td>
"""
    html_foot = """
</table>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_head + html_body + html_foot)

# 保存历史CSV
def save_csv(data):
    df = pd.DataFrame(data)
    try:
        old = pd.read_csv("index_data.csv", encoding="utf-8-sig")
        df = pd.concat([old, df], ignore_index=True)
    except:
        pass
    df.to_csv("index_data.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    print("🚀 开始从韭圈儿抓取全部全球指数数据...")
    data = asyncio.run(crawl_all())
    generate_html(data)
    save_csv(data)
    print("🎉 全部完成，已生成 index.html 和 index_data.csv")
