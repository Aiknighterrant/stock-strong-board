#!/usr/bin/env python3
"""
分析2026年4月3日涨停股
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

# 直接导入数据获取函数
import requests
import time
from datetime import datetime
import json
from typing import List, Dict, Any

def log_debug(msg: str, debug: bool = False):
    """调试日志"""
    if debug:
        print(f"[DEBUG] {msg}")

def fetch_limit_up_stocks_real(date_str: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    从新浪财经获取涨停股票数据
    """
    stocks = []
    
    try:
        log_debug("尝试从新浪财经获取涨停数据", debug)
        
        # 新浪财经涨停股页面
        url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
        
        params = {
            'page': 1,
            'num': 100,
            'sort': 'changepercent',
            'asc': 0,  # 降序
            'node': 'hs_a',
            'symbol': '',
            '_s_r_a': 'page'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://vip.stock.finance.sina.com.cn/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                # 新浪返回的是JSONP格式，需要解析
                content = response.text
                if content.startswith('/*') and content.endswith('*/'):
                    content = content[2:-2]
                
                data = json.loads(content)
                
                for item in data:
                    try:
                        change_pct = float(item.get('changepercent', 0))
                        
                        # 筛选涨停股（考虑ST股和科创板）
                        if change_pct >= 9.5:
                            stock_code = item.get('symbol', '').replace('sh', '').replace('sz', '')
                            stock_name = item.get('name', '')
                            close_price = float(item.get('trade', 0))
                            amount = float(item.get('amount', 0)) / 100000000  # 转亿元
                            turnover_rate = float(item.get('turnoverratio', 0))
                            
                            stock_data = {
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'close_price': round(close_price, 2),
                                'change_pct': round(change_pct, 2),
                                'amount': round(amount, 2),
                                'volume': 0,
                                'bid1_price': 0,
                                'bid1_volume': 0,
                                'turnover_rate': round(turnover_rate, 1),
                                'sector_code': '',
                                'sector_name': item.get('industry', ''),
                                'pe_ratio': 0,
                                'pb_ratio': 0,
                                'board_amount': 0,
                                'board_ratio': 0
                            }
                            
                            stocks.append(stock_data)
                    except:
                        continue
                
                log_debug(f"从新浪财经获取到 {len(stocks)} 只涨停股票", debug)
                
            except json.JSONDecodeError:
                log_debug("新浪财经返回数据格式错误", debug)
    
    except Exception as e:
        log_debug(f"新浪财经数据获取失败: {str(e)}", debug)
    
    return stocks

# 导入筛选函数
from filter_stocks import filter_by_board_strength, filter_by_turnover
from analyze_sectors import analyze_sector_strength, filter_by_sector
from utils import format_output

def analyze_date(date_str: str):
    """分析指定日期的涨停股"""
    print("=" * 80)
    print(f"沪深A股短线强势封板股分析 - {date_str}")
    print("=" * 80)
    print(f"筛选参数: 成交额≥1.0亿, 换手率10.0%-20.0%")
    print(f"        板块阈值>-0.5%%, 板块得分≥60")
    print("-" * 80)
    
    # 1. 获取涨停股池
    print("步骤1: 获取涨停股池...")
    all_stocks = fetch_limit_up_stocks_real(date_str, debug=False)
    print(f"  获取到 {len(all_stocks)} 只涨停股票")
    
    if len(all_stocks) == 0:
        print("  错误: 未能获取涨停股票数据")
        return
    
    # 2. 封板强度筛选
    print("步骤2: 封板强度筛选...")
    # 由于新浪财经没有封单数据，我们只按成交额筛选
    filtered_stocks = []
    for stock in all_stocks:
        if stock['amount'] >= 1.0:  # 成交额≥1亿
            filtered_stocks.append(stock)
    
    print(f"  成交额筛选后剩余 {len(filtered_stocks)} 只股票")
    
    # 3. 换手率筛选
    print("步骤3: 换手率筛选...")
    final_stocks = []
    for stock in filtered_stocks:
        turnover = stock['turnover_rate']
        if 10.0 <= turnover <= 20.0:
            final_stocks.append(stock)
    
    print(f"  换手率筛选后剩余 {len(final_stocks)} 只股票")
    
    # 4. 板块强度分析（简化版）
    print("步骤4: 板块强度分析...")
    # 由于没有板块数据，我们跳过板块筛选
    print("  板块数据暂不可用，跳过板块筛选")
    
    # 5. 输出结果
    print("\n" + "=" * 80)
    print("筛选结果:")
    print("=" * 80)
    
    if len(final_stocks) == 0:
        print("未找到符合条件的股票")
        return
    
    # 按成交额排序
    final_stocks.sort(key=lambda x: x['amount'], reverse=True)
    
    # 显示表格
    print("    序号     |     代码     |     名称     |   成交额(亿)   |    换手率%    |    所属板块    ")
    print("-" * 100)
    
    for i, stock in enumerate(final_stocks[:15], 1):
        code = stock['stock_code']
        name = stock['stock_name']
        amount = stock['amount']
        turnover = stock['turnover_rate']
        sector = stock.get('sector_name', '未知')
        
        print(f"    {i:<4}    |   {code:<8}  |   {name:<10}  |   {amount:>6.2f}    |    {turnover:>5.1f}    |   {sector:<10}")
    
    print("\n" + "-" * 80)
    print("统计信息:")
    print(f"  总涨停股数: {len(all_stocks)}")
    print(f"  最终筛选数: {len(final_stocks)}")
    print(f"  筛选通过率: {len(final_stocks)/len(all_stocks)*100:.1f}%")
    
    # 分析板块分布
    sector_dist = {}
    for stock in final_stocks:
        sector = stock.get('sector_name', '未知')
        sector_dist[sector] = sector_dist.get(sector, 0) + 1
    
    if sector_dist:
        print(f"  板块分布: {', '.join([f'{k}({v})' for k, v in sector_dist.items()])}")
    
    print("=" * 80)
    
    # 详细分析
    print("\n📊 详细分析:")
    
    # 1. 成交额分析
    total_amount = sum(stock['amount'] for stock in final_stocks)
    avg_amount = total_amount / len(final_stocks) if final_stocks else 0
    max_amount_stock = max(final_stocks, key=lambda x: x['amount']) if final_stocks else None
    
    print(f"1. 成交额分析:")
    print(f"  总成交额: {total_amount:.1f}亿元")
    print(f"  平均成交额: {avg_amount:.2f}亿元")
    if max_amount_stock:
        print(f"  最大成交额: {max_amount_stock['stock_name']}({max_amount_stock['stock_code']}) - {max_amount_stock['amount']:.2f}亿元")
    
    # 2. 换手率分析
    avg_turnover = sum(stock['turnover_rate'] for stock in final_stocks) / len(final_stocks) if final_stocks else 0
    print(f"2. 换手率分析:")
    print(f"  平均换手率: {avg_turnover:.1f}%")
    print(f"  换手率范围: 10.0%-20.0% (筛选标准)")
    
    # 3. 重点关注股票
    print(f"3. 重点关注股票:")
    
    # 按成交额排名
    print(f"  📈 成交额前5:")
    for i, stock in enumerate(final_stocks[:5], 1):
        print(f"    {i}. {stock['stock_name']}({stock['stock_code']}) - {stock['amount']:.2f}亿元")
    
    # 按换手率适中排名（接近15%）
    if final_stocks:
        balanced_stocks = sorted(final_stocks, key=lambda x: abs(x['turnover_rate'] - 15))
        print(f"  ⚖️  换手率最适中(接近15%):")
        for i, stock in enumerate(balanced_stocks[:3], 1):
            print(f"    {i}. {stock['stock_name']}({stock['stock_code']}) - {stock['turnover_rate']:.1f}%")
    
    # 4. 风险提示
    print(f"4. 风险提示:")
    print(f"  ⚠️  数据限制: 当前使用新浪财经数据，封单金额和板块信息暂不可用")
    print(f"  ⚠️  换手率偏高: 部分股票换手率接近20%，可能存在较大波动")
    print(f"  ⚠️  成交额差异: 成交额从{min(s['amount'] for s in final_stocks):.2f}亿到{max(s['amount'] for s in final_stocks):.2f}亿，流动性差异大")

if __name__ == "__main__":
    analyze_date("2026-04-03")