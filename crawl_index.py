import yfinance as yf
import pandas as pd
import datetime
import os

# ===================== 配置指数列表 =====================
INDEX_MAP = {
    "标普500(SPX)": "^GSPC",
    "纳斯达克100(NDX)": "^NDX",
    "日经225(N225)": "^N225",
    "英国富时100(FTSE)": "^FTSE",
    "法国CAC40(FCHI)": "^FCHI",
    "德国DAX(GDAXI)": "^GDAXI",
    "沪深300": "000300.SS",
    "中证500": "000905.SS",
    "恒生指数(HSI)": "^HSI",
    "恒生科技(HSTECH)": "HSTECH.HK"
}

# ===================== 估值等级配置（PE分位值） =====================
def get_valuation_level(pe_ttm: float) -> tuple:
    """
    根据PE-TTM返回估值等级和颜色
    返回：(等级文字, 颜色代码)
    """
    if pe_ttm > 90:
        return "极度高估", "#ff4444"  # 红色
    elif pe_ttm > 70:
        return "高估", "#ff9800"      # 橙色
    elif pe_ttm > 30:
        return "适中", "#ffeb3b"      # 黄色
    elif pe_ttm > 10:
        return "低估", "#8bc34a"      # 浅绿色
    else:
        return "极度低估", "#4caf50"   # 深绿色

# ===================== 抓取数据函数 =====================
def crawl_index_data():
    result = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    for name, ticker in INDEX_MAP.items():
        try:
            # 抓取指数实时数据
            idx = yf.Ticker(ticker)
            info = idx.info
            
            # 提取核心数据
            price = info.get("regularMarketPrice", "无数据")
            pe_ttm = info.get("trailingPE", 0)
            high_52w = info.get("fiftyTwoWeekHigh", "无数据")
            low_52w = info.get("fiftyTwoWeekLow", "无数据")

            # 处理PE数值
            try:
                pe_ttm = float(pe_ttm)
            except:
                pe_ttm = 0

            # 获取估值等级
            level, color = get_valuation_level(pe_ttm)

            # 组装数据
            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": price,
                "PE-TTM": round(pe_ttm, 2),
                "52周最高": high_52w,
                "52周最低": low_52w,
                "估值等级": level,
                "颜色": color
            })
            print(f"✅ 抓取成功：{name}")
        except Exception as e:
            print(f"❌ 抓取失败：{name}，错误：{str(e)}")
            result.append({
                "日期": today,
                "指数名称": name,
                "当前价格": "抓取失败",
                "PE-TTM": 0,
                "52周最高": "-",
                "52周最低": "-",
                "估值等级": "数据异常",
                "颜色": "#9e9e9e"
            })

    return result

# ===================== 保存数据 =====================
def save_data(data):
    # 保存为CSV
    df = pd.DataFrame(data)
    df.to_csv("index_data.csv", index=False, encoding="utf-8-sig")
    
    # 生成HTML可视化页面
    generate_html(df)
    print("📊 数据已保存：index_data.csv + index.html")

# ===================== 生成HTML色块可视化页面 =====================
def generate_html(df):
    html_head = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>全球指数估值看板</title>
        <style>
            body {font-family: Arial; margin: 20px;}
            table {border-collapse: collapse; width: 100%; margin-top: 20px;}
            th, td {border: 1px solid #ddd; padding: 12px; text-align: center;}
            th {background-color: #2196f3; color: white;}
            .val-tag {display: inline-block; padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold;}
        </style>
    </head>
    <body>
        <h1>🌍 全球指数每日估值看板</h1>
        <p>更新时间：""" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
        <table>
            <tr>
                <th>指数名称</th>
                <th>当前价格</th>
                <th>PE-TTM</th>
                <th>估值等级</th>
                <th>52周最高</th>
                <th>52周最低</th>
            </tr>
    """

    html_body = ""
    for _, row in df.iterrows():
        html_body += f"""
            <tr>
                <td>{row['指数名称']}</td>
                <td>{row['当前价格']}</td>
                <td>{row['PE-TTM']}</td>
                <td><span class='val-tag' style='background-color:{row['颜色']}'>{row['估值等级']}</span></td>
                <td>{row['52周最高']}</td>
                <td>{row['52周最低']}</td>
            </tr>
        """

    html_foot = """
        </table>
    </body>
    </html>
    """

    # 写入HTML文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_head + html_body + html_foot)

# ===================== 主函数 =====================
if __name__ == "__main__":
    print("🚀 开始抓取全球指数数据...")
    data = crawl_index_data()
    save_data(data)
    print("🎉 任务完成！")
