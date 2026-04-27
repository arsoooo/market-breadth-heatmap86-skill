#!/usr/bin/env python3
"""
86行业 MA20 站上率热力图 V3 - 按一级行业聚合 + 宽表格式
基于v2改进，保留v3的截图尺寸

功能：
1. 第1列：二级行业名称
2. 第2列：二级行业当日站上率
3. 第3-33列：近31天每天的MA20站上率
4. 按最新站上率排序
5. 根据站上率标色
"""
import json
import os
import urllib.request
import subprocess
from datetime import datetime

WORKDIR = os.path.dirname(os.path.abspath(__file__))
TG_GROUP = "这里填你的飞书会话id：oc_XXX"

# 一级行业到二级行业的映射
INDUSTRY_MAP = {
    "有色金属": ["有色金属", "小金属", "能源金属", "贵金属"],
    "医药": ["中药", "化学制药", "医疗器械", "医疗服务", "医药商业", "生物制品"],
    "传媒": ["文化传媒", "游戏"],
    "电子": ["半导体", "消费电子", "光学光电子", "电子元件"],
    "机械": ["专用设备", "仪器仪表", "工程机械", "电机", "通用设备"],
    "通信": ["通信设备", "通信服务"],
    "轻工制造": ["包装材料", "家用轻工", "家电行业", "造纸印刷"],
    "商贸零售": ["商业百货", "旅游酒店", "珠宝首饰", "美容护理", "贸易行业"],
    "汽车": ["汽车整车", "汽车服务", "汽车零部件"],
    "交通运输": ["交运设备", "物流行业", "航空机场", "航运港口", "铁路公路"],
    "银行": ["银行"],
    "化工": ["农药兽药", "化学制品", "化学原料", "化纤行业", "化肥行业", "塑料制品", "橡胶制品", "电子化学品", "非金属材料"],
    "纺织服装": ["纺织服装"],
    "计算机": ["互联网服务", "计算机设备", "软件开发"],
    "建筑": ["工程咨询服务", "工程建设", "水泥建材", "玻璃玻纤", "装修建材", "装修装饰"],
    "食品饮料": ["酿酒行业", "食品饮料"],
    "钢铁": ["钢铁行业"],
    "综合": ["专业服务", "综合行业", "教育"],
    "农林牧渔": ["农牧饲渔"],
    "金融": ["证券", "保险", "多元金融"],
    "石油": ["石油行业"],
    "国防军工": ["航天航空", "船舶制造"],
    "电力": ["光伏设备", "电池", "电源设备", "电网设备", "风电设备", "电力行业"],
    "房地产": ["房地产开发", "房地产服务"],
    "公用事业": ["公用事业", "燃气", "环保行业"],
    "煤炭": ["煤炭行业", "采掘行业"],
}


def fetch_data():
    """Step 1: 获取原始数据"""
    api_url = "https://sckd.dapanyuntu.com/api/api/industry_ma20_analysis_page?page=0"
    req = urllib.request.Request(api_url, headers={
        "Referer": "https://sckd.dapanyuntu.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    output_path = os.path.join(WORKDIR, "raw_86_data_v3.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"获取数据完成: {len(data['industries'])} 个行业, {len(data['dates'])} 个日期")
    return data


def get_color(value):
    """根据值返回颜色"""
    if value is None or value == 0:
        return "#333333", "-"
    if value < 20:
        return "#4d96ff", f"{value:.0f}%"  # 蓝 0-20
    elif value < 40:
        return "#6bcb77", f"{value:.0f}%"  # 绿 20-40
    elif value < 60:
        return "#ffd93d", f"{value:.0f}%"  # 黄 40-60
    elif value < 80:
        return "#ffa502", f"{value:.0f}%"  # 橙 60-80
    else:
        return "#ff6b6b", f"{value:.0f}%"  # 红 80-100


def render_html_v3(data, ts, output_dir):
    """Step 2: 生成 HTML 热力图 (V3版本 - 宽表格式)"""
    industries = data["industries"]
    dates = data["dates"]
    raw_data = data["data"]
    
    # 最新日期索引
    latest_idx = len(dates) - 1
    # 近31天
    thirty_one_days = 31
    
    # 构建行业-日期-值的映射
    industry_values = {ind: [None] * len(dates) for ind in industries}
    for date_idx, ind_idx, val in raw_data:
        ind_name = industries[ind_idx]
        if 0 <= date_idx < len(dates):
            industry_values[ind_name][date_idx] = val
    
    # 计算一级行业数据
    primaries = {}
    for primary, secondaries in INDUSTRY_MAP.items():
        # 找出实际存在的二级行业
        existing_secs = [s for s in secondaries if s in industry_values]
        if existing_secs:
            # 获取最新日期的站上率
            latest_rates = [industry_values[s][latest_idx] for s in existing_secs if industry_values[s][latest_idx] is not None]
            avg_rate = sum(latest_rates) / len(latest_rates) if latest_rates else 0
            
            primaries[primary] = {
                "secondaries": existing_secs,
                "latest_rate": avg_rate,
            }
    
    # 按一级行业站上率排序（高→低）
    sorted_primaries = sorted(primaries.keys(), key=lambda x: primaries[x]["latest_rate"], reverse=True)
    
    # 生成表头（近31天日期）
    date_headers = [dates[i][5:] for i in range(latest_idx - thirty_one_days + 1, latest_idx + 1)]  # 只取月-日
    date_headers_html = ''.join([f'<th>{d}</th>' for d in date_headers])
    
    # 生成表格行
    rows = []
    for primary in sorted_primaries:
        info = primaries[primary]
        secs = info["secondaries"]
        primary_latest = info["latest_rate"]
        
        # 二级行业按最新站上率排序
        sorted_secs = sorted(secs, key=lambda s: industry_values[s][latest_idx] or 0, reverse=True)
        
        primary_color, primary_text = get_color(primary_latest)
        
        for i, sec in enumerate(sorted_secs):
            # 获取该二级行业近31天的所有值
            sec_values = industry_values[sec]
            
            # 构建31天的td
            day_cells = []
            for day_idx in range(latest_idx - thirty_one_days + 1, latest_idx + 1):
                val = sec_values[day_idx] if day_idx >= 0 else None
                cell_color, cell_text = get_color(val)
                day_cells.append(f'<td class="cell" style="background:{cell_color}">{cell_text}</td>')
            
            day_cells_html = ''.join(day_cells)
            
            if i == 0:
                # 第一个二级行业，合并显示一级行业
                rows.append(f'''<tr>
                    <td class="primary-cell" rowspan="{len(sorted_secs)}" style="background:#16213e;color:#58a6ff;font-weight:bold;vertical-align:middle">{primary}</td>
                    <td class="rate-cell" rowspan="{len(sorted_secs)}" style="background:#16213e;color:{primary_color};font-weight:bold;vertical-align:middle">{primary_text}</td>
                    <td class="secondary-cell" style="background:#1a1a2e">{sec}</td>
                    {day_cells_html}
                    <td class="secondary-cell-right" style="background:#1a1a2e">{sec}</td>
                </tr>''')
            else:
                rows.append(f'''<tr>
                    <td class="secondary-cell" style="background:#1a1a2e">{sec}</td>
                    {day_cells_html}
                    <td class="secondary-cell-right" style="background:#1a1a2e">{sec}</td>
                </tr>''')
    
    rows_html = ''.join(rows)
    
    # 生成HTML（参考v2样式）
    html_template = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>86个二级行业 MA20 站上率热力图 V3</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e; 
            color: #eee;
            padding: 20px;
        }}
        h1 {{ 
            text-align: center; 
            margin-bottom: 10px; 
            font-size: 24px;
        }}
        .subtitle {{ 
            text-align: center; 
            color: #888; 
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .date-range {{ 
            text-align: center; 
            color: #666; 
            margin-bottom: 20px;
            font-size: 12px;
        }}
        .heatmap-container {{
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            margin: 0 auto;
            font-size: 11px;
        }}
        th, td {{
            border: 1px solid #333;
            text-align: center;
            padding: 4px 6px;
            min-width: 45px;
        }}
        th {{
            background: #16213e;
            color: #fff;
            font-weight: normal;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th.primary-col {{
            position: sticky;
            left: 0;
            z-index: 20;
            min-width: 100px;
            background: #16213e;
        }}
        /* 第2列：当日站上率（固定） */
        th.rate-col {{
            min-width: 80px;
            position: sticky;
            left: 100px;  /* 第1列宽100px */
            z-index: 18;
            background: #16213e;
        }}
        /* 第3列：二级行业（固定） */
        th.industry-col {{
            min-width: 80px;
            position: sticky;
            left: 180px;  /* 第1列100px + 第2列80px */
            z-index: 16;
            background: #16213e;
        }}
        /* 第35列：二级行业（右侧固定） */
        th.industry-col-right {{
            min-width: 60px;
            position: sticky;
            right: 0px;  
            z-index: 16;
            background: #16213e;
        }}
        /* 第1列td：一级行业（固定） */
        td.primary-cell {{
            background: #16213e;
            color: #fff;
            font-weight: 500;
            position: sticky;
            left: 0;
            z-index: 10;
        }}
        /* 第2列td：当日站上率（固定） */
        td.rate-cell {{
            background: #16213e;
            color: #fff;
            font-weight: 500;
            position: sticky;
            left: 100px;
            z-index: 8;
        }}
        
        /* 第3列td：二级行业（固定） */
        td.secondary-cell {{
            background: #1a1a2e;
            color: #eee;
            text-align: left;
            position: sticky;
            left: 180px;
            z-index: 5;
            min-width: 80px;
        }}
        /* 第35列td：二级行业（右侧固定） */
        td.secondary-cell-right {{
            background: #1a1a2e;
            color: #eee;
            text-align: left;
            position: sticky;
            right: 0px;
            z-index: 5;
            min-width: 60px;
        }}
        
        td.cell {{
            color: #000;
            font-weight: bold;
            min-width: 45px;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border: 1px solid #333;
        }}
    </style>
</head>
<body>
    <h1>📊 86个二级行业 MA20 站上率热力图 V3</h1>
    <div class="subtitle">按一级行业聚合 | 按MA20站上率排序（高→低）</div>
    <div class="date-range">数据区间: {dates[0]} ~ {dates[-1]}（共{len(dates)}个交易日）</div>
    <div class="heatmap-container">
        <table>
            <thead>
                <tr>
                    <!-- 第1列：一级行业（固定） -->
                    <th class="primary-col">一级行业</th>
                    <!-- 第2列：一级行业当日站上率（固定） -->
                    <th class="rate-col">当日站上率</th>
                    <!-- 第3列：二级行业名称（固定） -->
                    <th class="industry-col">二级行业</th>
                    {date_headers_html}
                    <th class="industry-col-right">二级行业</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    <div class="legend">
        <span>图例:</span>
        <div class="legend-item"><div class="legend-color" style="background:#4d96ff"></div>0-20%</div>
        <div class="legend-item"><div class="legend-color" style="background:#6bcb77"></div>20-40%</div>
        <div class="legend-item"><div class="legend-color" style="background:#ffd93d"></div>40-60%</div>
        <div class="legend-item"><div class="legend-color" style="background:#ffa502"></div>60-80%</div>
        <div class="legend-item"><div class="legend-color" style="background:#ff6b6b"></div>80-100%</div>
    </div>
</body>
</html>'''
    
    output_path = os.path.join(output_dir, f"heatmap_86_v3_{ts}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"HTML 生成完成: {output_path}")
    return output_path


def capture_html(html_path, output_path):
    """Step 3: 截图"""
    skill_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    capture_js = os.path.join(skill_base, "assets", "capture.js")
    
    if not os.path.exists(capture_js):
        print(f"错误: capture.js 不存在")
        return None
    
    # V3 尺寸：横向更长（1,800 x 2,400）
    width = 1800
    height = 2400
    dpr = 2
    
    print(f"正在截图: {html_path} -> {output_path}")
    cmd = ["node", capture_js, html_path, output_path, str(width), str(height), str(dpr)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=skill_base)
    
    if result.returncode != 0:
        print(f"截图失败: {result.stderr}")
        return None
    
    print(f"截图完成: {output_path}")
    return output_path


def generate_weekly_analysis(data, industries):
    """生成二级行业的近一周变化分析：增幅 TOP5 + 降幅 TOP5"""
    dates = data["dates"]
    raw_data = data["data"]
    
    # 构建行业-日期-值的映射
    industry_values = {ind: [None] * len(dates) for ind in industries}
    for date_idx, ind_idx, val in raw_data:
        ind_name = industries[ind_idx]
        if 0 <= date_idx < len(dates):
            industry_values[ind_name][date_idx] = val
    
    # 最近7天
    start_idx = len(dates) - 7
    end_idx = len(dates)
    
    rows = []
    for ind_name, vals in industry_values.items():
        old_val = vals[start_idx] if start_idx < len(vals) else None
        new_val = vals[end_idx - 1] if end_idx - 1 < len(vals) else None
        
        if old_val and new_val:
            change = new_val - old_val
            rows.append((ind_name, old_val, new_val, change))
    
    # 按变化排序
    rows.sort(key=lambda x: x[3], reverse=True)
    
    # 增幅 TOP5
    top5 = rows[:5]
    # 降幅 TOP5（最后5个）
    bottom5 = rows[-5:]
    
    analysis = ["## 📊 二级行业 MA20 站上率 - 近一周变化", ""]
    analysis.append("**🚀 增幅 TOP5:**")
    analysis.append("| 行业 | 7日前 | 今日 | 变化 |")
    analysis.append("|------|-------|------|-----|")
    for ind_name, old, new, chg in top5:
        analysis.append(f"| {ind_name} | {old:.1f} | {new:.1f} | +{chg:.1f} 🚀 |")
    
    analysis.append("")
    analysis.append("**📉 降幅 TOP5:**")
    analysis.append("| 行业 | 7日前 | 今日 | 变化 |")
    analysis.append("|------|-------|------|-----|")
    for ind_name, old, new, chg in bottom5:
        analysis.append(f"| {ind_name} | {old:.1f} | {new:.1f} | {chg:.1f} 📉 |")
    
    return "\n".join(analysis)


def send_to_group_msg(png_path, analysis_text, current_date):
    """发送到飞书群"""
    # 保存分析到临时文件
    with open("/tmp/analysis_86.txt", "w", encoding="utf-8") as f:
        f.write(analysis_text)
    
    # 调用 openclaw message 发送
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", TG_GROUP,
        "--message", f"📊 A股市场宽度热力图（86行业版） - {current_date}\n\n按一级行业聚合，86个二级行业 MA20 站上率趋势（近31天）\n颜色：淡紫(低) → 浅蓝 → 浅绿 → 浅黄 → 浅橙(高)",
        "--media", png_path
    ]
    
    subprocess.run(cmd, check=True)
    
    #print(f"[{datetime.now()}] 每日任务完成!")
    
    #result = subprocess.run(cmd, capture_output=True, text=True)
    #if result.returncode != 0:
    #    print(f"发送失败: {result.stderr}")
    #    return False
    #print(f"已发送到群: {TG_GROUP}")
    return True


def send_to_group(file_path):
    """发送到飞书群"""
   
    
    # 调用 openclaw message 发送
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", TG_GROUP,
        "--media", file_path
    ]
    
    subprocess.run(cmd, check=True)
    
    #print(f"[{datetime.now()}] 每日任务完成!")
    
    
def send_to_xhs_note(png_path, analysis_text, current_date):
    """发送小红书私密笔记"""
    # 转换日期：2026-04-24 → 4月24日
    dt = datetime.strptime(current_date, "%Y-%m-%d")
    date_display = f"{dt.month}月{dt.day}日"
    
    # 标题格式：86行业股市MA20站上率-4月24日
    title = f"86行业股市MA20站上率-{date_display}"
    
    # 笔记内容
    content = f"📊 A股市场宽度分析 {date_display}\n\n{analysis_text}"
    
    # 保存到临时文件（避免命令行过长）
    with open("/tmp/xhs_note_content.txt", "w", encoding="utf-8") as f:
        f.write(content)
        
    # 调用 xhs 发布私密笔记
    cmd = [
        "xhs", "post",
        "--title", title,
        "--body", content,
        "--images", png_path,
        #"--images", "/root/.openclaw/workspace/market-breadth-heatmap-skill/market_breadth_heatmap.png"
        "--private"  # 私密发布
    ]
    
    subprocess.run(cmd, check=True)

def main():
    # 生成时间戳
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 创建output文件夹
    output_dir = os.path.join(WORKDIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[{datetime.now()}] 开始生成86行业热力图 V3...")
    
    # Step 1: 获取数据
    print("Step 1: 获取数据...")
    data = fetch_data()
    
    # Step 2: 生成HTML
    print("Step 2: 生成HTML...")
    html_path = render_html_v3(data, ts, output_dir)
    
    # Step 3: 截图
    print("Step 3: 截图...")
    png_path = os.path.join(output_dir, f"heatmap_86_v3_{ts}.png")
    capture_html(html_path, png_path)
    
    # Step 4: 生成一周分析
    print("Step 4: 一周数据分析...")
    analysis_text = generate_weekly_analysis(data, data["industries"])
    print(analysis_text)
    
    # Step 5: 发送到群
    print("Step 5: 发送到群...")
    send_to_group_msg(png_path, analysis_text, current_date)
    #send_to_group(html_path)
    
    # Step 6: 发小红书
    # send_to_xhs_note(png_path, analysis_text, current_date)
    
    print(f"[{datetime.now()}] 完成! PNG: {png_path} & HTML: {html_path}")


if __name__ == "__main__":
    main()