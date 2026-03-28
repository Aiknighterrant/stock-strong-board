#!/usr/bin/env python3
"""
板块强度分析模块
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import log_debug
from fetch_stock_data import fetch_sector_data

def analyze_sector_strength(date_str: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    分析板块强度
    
    Args:
        date_str: 日期字符串
        debug: 调试模式
    
    Returns:
        板块强度数据列表
    """
    log_debug(f"开始分析板块强度，日期: {date_str}", debug)
    
    # 获取板块数据
    sector_data = fetch_sector_data(date_str, debug)
    
    if not sector_data:
        log_debug("未获取到板块数据", debug)
        return []
    
    # 计算板块强度得分
    for sector in sector_data:
        sector_score = calculate_sector_score(sector)
        sector['sector_score'] = sector_score
    
    # 按板块强度得分排序
    sorted_sectors = sorted(sector_data, key=lambda x: x.get('sector_score', 0), reverse=True)
    
    # 输出板块强度排名
    if debug and sorted_sectors:
        log_debug("板块强度排名前5:", debug)
        for i, sector in enumerate(sorted_sectors[:5], 1):
            log_debug(f"  {i}. {sector['sector_name']}: "
                     f"涨幅={sector['change_pct']:.2f}%, "
                     f"成交额={sector['amount']:.1f}亿, "
                     f"涨停={sector['limit_up_count']}只, "
                     f"强度得分={sector['sector_score']:.1f}", debug)
    
    log_debug(f"板块强度分析完成，共分析 {len(sorted_sectors)} 个板块", debug)
    
    return sorted_sectors

def calculate_sector_score(sector: Dict[str, Any]) -> float:
    """
    计算板块强度得分
    
    Args:
        sector: 板块数据
    
    Returns:
        板块强度得分（0-100）
    """
    scores = []
    weights = []
    
    # 1. 板块涨跌幅得分（权重0.4）
    change_pct = sector.get('change_pct', 0)
    change_score = calculate_change_score(change_pct)
    scores.append(change_score)
    weights.append(0.4)
    
    # 2. 板块成交额占比得分（权重0.3）
    amount = sector.get('amount', 0)
    stock_count = sector.get('stock_count', 1)
    amount_per_stock = amount / stock_count if stock_count > 0 else 0
    amount_score = calculate_amount_score(amount_per_stock)
    scores.append(amount_score)
    weights.append(0.3)
    
    # 3. 板块内涨停股数量得分（权重0.2）
    limit_up_count = sector.get('limit_up_count', 0)
    limit_up_score = calculate_limit_up_score(limit_up_count, stock_count)
    scores.append(limit_up_score)
    weights.append(0.2)
    
    # 4. 板块资金流向得分（权重0.1）
    net_inflow = sector.get('net_inflow', 0)
    inflow_score = calculate_inflow_score(net_inflow, amount)
    scores.append(inflow_score)
    weights.append(0.1)
    
    # 计算加权平均
    total_score = sum(s * w for s, w in zip(scores, weights))
    return round(total_score, 1)

def calculate_change_score(change_pct: float) -> float:
    """
    计算涨跌幅得分
    
    Args:
        change_pct: 涨跌幅（%）
    
    Returns:
        涨跌幅得分（0-100）
    """
    if change_pct >= 5.0:
        return 100.0
    elif change_pct >= 3.0:
        return 80.0 + (change_pct - 3.0) * 10.0
    elif change_pct >= 0.0:
        return 60.0 + change_pct * 6.67
    elif change_pct >= -1.0:
        return 40.0 + (change_pct + 1.0) * 20.0
    else:
        return max(0.0, 40.0 + change_pct * 40.0)

def calculate_amount_score(amount_per_stock: float) -> float:
    """
    计算成交额得分
    
    Args:
        amount_per_stock: 平均每只股票的成交额（亿元）
    
    Returns:
        成交额得分（0-100）
    """
    if amount_per_stock >= 2.0:
        return 100.0
    elif amount_per_stock >= 1.0:
        return 80.0 + (amount_per_stock - 1.0) * 20.0
    elif amount_per_stock >= 0.5:
        return 60.0 + (amount_per_stock - 0.5) * 40.0
    elif amount_per_stock >= 0.2:
        return 40.0 + (amount_per_stock - 0.2) * 66.67
    else:
        return amount_per_stock * 200.0

def calculate_limit_up_score(limit_up_count: int, stock_count: int) -> float:
    """
    计算涨停股数量得分
    
    Args:
        limit_up_count: 涨停股数量
        stock_count: 板块内股票总数
    
    Returns:
        涨停股数量得分（0-100）
    """
    if stock_count <= 0:
        return 0.0
    
    # 计算涨停股占比
    limit_up_ratio = limit_up_count / stock_count * 100
    
    if limit_up_ratio >= 10.0:
        return 100.0
    elif limit_up_ratio >= 5.0:
        return 80.0 + (limit_up_ratio - 5.0) * 4.0
    elif limit_up_ratio >= 2.0:
        return 60.0 + (limit_up_ratio - 2.0) * 6.67
    elif limit_up_ratio >= 1.0:
        return 40.0 + (limit_up_ratio - 1.0) * 20.0
    else:
        return limit_up_ratio * 40.0

def calculate_inflow_score(net_inflow: float, amount: float) -> float:
    """
    计算资金流向得分
    
    Args:
        net_inflow: 资金净流入（亿元）
        amount: 板块成交额（亿元）
    
    Returns:
        资金流向得分（0-100）
    """
    if amount <= 0:
        return 50.0  # 中性
    
    # 计算资金流入率
    inflow_ratio = net_inflow / amount * 100
    
    if inflow_ratio >= 10.0:
        return 100.0
    elif inflow_ratio >= 5.0:
        return 80.0 + (inflow_ratio - 5.0) * 4.0
    elif inflow_ratio >= 0.0:
        return 60.0 + inflow_ratio * 4.0
    elif inflow_ratio >= -5.0:
        return 40.0 + (inflow_ratio + 5.0) * 4.0
    else:
        return max(0.0, 40.0 + inflow_ratio * 8.0)

def filter_by_sector(stocks: List[Dict[str, Any]], 
                    sector_data: List[Dict[str, Any]],
                    sector_threshold: float = -0.5,
                    sector_score_min: int = 60,
                    debug: bool = False) -> List[Dict[str, Any]]:
    """
    根据板块强度筛选股票
    
    Args:
        stocks: 股票数据列表
        sector_data: 板块强度数据列表
        sector_threshold: 板块涨跌幅阈值（%）
        sector_score_min: 板块强度最低分
        debug: 调试模式
    
    Returns:
        筛选后的股票列表
    """
    if not stocks or not sector_data:
        return stocks if stocks else []
    
    log_debug(f"开始板块强度筛选，初始股票数: {len(stocks)}", debug)
    log_debug(f"筛选参数: 板块涨幅>{sector_threshold}%，板块得分≥{sector_score_min}", debug)
    
    # 创建板块数据字典，便于查找
    sector_dict = {}
    for sector in sector_data:
        sector_code = sector.get('sector_code', '')
        if sector_code:
            sector_dict[sector_code] = sector
    
    filtered_stocks = []
    removed_count = 0
    
    for stock in stocks:
        sector_code = stock.get('sector_code', '')
        
        if not sector_code:
            # 没有板块信息，默认保留
            log_debug(f"股票无板块信息，保留: {stock.get('stock_name')}", debug)
            filtered_stocks.append(stock)
            continue
        
        # 查找板块数据
        sector = sector_dict.get(sector_code)
        
        if not sector:
            # 未找到板块数据，默认保留
            log_debug(f"未找到板块数据，保留: {stock.get('stock_name')}", debug)
            filtered_stocks.append(stock)
            continue
        
        # 检查板块条件
        sector_change = sector.get('change_pct', 0)
        sector_score = sector.get('sector_score', 0)
        
        if sector_change <= sector_threshold:
            log_debug(f"板块下跌排除: {stock.get('stock_name')} "
                     f"板块涨幅={sector_change:.2f}% ≤ {sector_threshold}%", debug)
            removed_count += 1
            continue
        
        if sector_score < sector_score_min:
            log_debug(f"板块强度不足排除: {stock.get('stock_name')} "
                     f"板块得分={sector_score:.1f} < {sector_score_min}", debug)
            removed_count += 1
            continue
        
        # 添加板块信息到股票数据
        stock['sector_change'] = sector_change
        stock['sector_score'] = sector_score
        stock['sector_net_inflow'] = sector.get('net_inflow', 0)
        stock['sector_limit_up_count'] = sector.get('limit_up_count', 0)
        
        filtered_stocks.append(stock)
    
    log_debug(f"板块强度筛选结果: 保留{len(filtered_stocks)}只，排除{removed_count}只", debug)
    
    return filtered_stocks

def analyze_sector_trend(sector_data: List[Dict[str, Any]], 
                        days: int = 5) -> Dict[str, Any]:
    """
    分析板块趋势
    
    Args:
        sector_data: 板块数据列表（多日数据）
        days: 分析的天数
    
    Returns:
        板块趋势分析结果
    """
    if not sector_data or len(sector_data) < days:
        return {}
    
    # 按板块分组
    sector_groups = {}
    for data in sector_data:
        sector_code = data.get('sector_code', '')
        if sector_code not in sector_groups:
            sector_groups[sector_code] = []
        sector_groups[sector_code].append(data)
    
    trend_results = {}
    
    for sector_code, data_list in sector_groups.items():
        if len(data_list) < days:
            continue
        
        # 按日期排序
        sorted_data = sorted(data_list, key=lambda x: x.get('date', ''))
        
        # 提取最近days天的数据
        recent_data = sorted_data[-days:]
        
        # 计算趋势指标
        changes = [d.get('change_pct', 0) for d in recent_data]
        amounts = [d.get('amount', 0) for d in recent_data]
        
        # 涨跌幅趋势
        change_trend = calculate_trend(changes)
        
        # 成交额趋势
        amount_trend = calculate_trend(amounts)
        
        # 最近表现
        recent_change = changes[-1]
        recent_amount = amounts[-1]
        
        # 趋势评分
        trend_score = (change_trend * 0.6 + amount_trend * 0.4) * 100
        
        trend_results[sector_code] = {
            'sector_name': recent_data[-1].get('sector_name', ''),
            'recent_change': recent_change,
            'recent_amount': recent_amount,
            'change_trend': change_trend,
            'amount_trend': amount_trend,
            'trend_score': trend_score,
            'trend_direction': 'up' if trend_score > 0 else 'down',
            'volatility': np.std(changes) if len(changes) > 1 else 0
        }
    
    return trend_results

def calculate_trend(values: List[float]) -> float:
    """
    计算趋势（线性回归斜率）
    
    Args:
        values: 数值列表
    
    Returns:
        趋势斜率
    """
    if len(values) < 2:
        return 0.0
    
    x = np.arange(len(values))
    y = np.array(values)
    
    # 线性回归
    if np.all(y == y[0]):
        return 0.0
    
    slope, _ = np.polyfit(x, y, 1)
    return slope

def identify_leading_sectors(sector_data: List[Dict[str, Any]], 
                           top_n: int = 3) -> List[Dict[str, Any]]:
    """
    识别领涨板块
    
    Args:
        sector_data: 板块数据列表
        top_n: 返回前N个领涨板块
    
    Returns:
        领涨板块列表
    """
    if not sector_data:
        return []
    
    # 按涨跌幅排序
    sorted_sectors = sorted(sector_data, key=lambda x: x.get('change_pct', 0), reverse=True)
    
    # 取前top_n个
    leading_sectors = sorted_sectors[:top_n]
    
    return leading_sectors

def analyze_sector_correlation(stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析板块相关性
    
    Args:
        stocks: 股票数据列表
    
    Returns:
        相关性分析结果
    """
    if not stocks or len(stocks) < 2:
        return {}
    
    # 按板块分组
    sector_groups = {}
    for stock in stocks:
        sector_code = stock.get('sector_code', '')
        if sector_code:
            if sector_code not in sector_groups:
                sector_groups[sector_code] = []
            sector_groups[sector_code].append(stock)
    
    if len(sector_groups) < 2:
        return {}
    
    # 计算板块间相关性
    sector_correlations = {}
    
    sector_codes = list(sector_groups.keys())
    
    for i in range(len(sector_codes)):
        for j in range(i + 1, len(sector_codes)):
            sector1 = sector_codes[i]
            sector2 = sector_codes[j]
            
            # 提取股票涨跌幅
            changes1 = [s.get('change_pct', 0) for s in sector_groups[sector1]]
            changes2 = [s.get('change_pct', 0) for s in sector_groups[sector2]]
            
            # 计算相关性
            if len(changes1) > 1 and len(changes2) > 1:
                correlation = np.corrcoef(changes1, changes2)[0, 1]
                if not np.isnan(correlation):
                    key = f"{sector1}_{sector2}"
                    sector_correlations[key] = {
                        'sector1': sector1,
                        'sector2': sector2,
                        'correlation': correlation,
                        'strength': 'strong' if abs(correlation) > 0.7 else 
                                   'moderate' if abs(correlation) > 0.3 else 'weak'
                    }
    
    return sector_correlations

if __name__ == "__main__":
    # 测试板块分析功能
    print("测试板块分析模块...")
    
    # 获取模拟数据
    sector_data = analyze_sector_strength("2025-03-28", debug=True)
    
    print(f"\n获取到 {len(sector_data)} 个板块数据")
    
    if sector_data:
        # 输出前3个板块信息
        print("\n板块强度排名前3:")
        for i, sector in enumerate(sector_data[:3], 1):
            print(f"{i}. {sector['sector_name']}: "
                  f"涨幅={sector['change_pct']:.2f}%, "
                  f"成交额={sector['amount']:.1f}亿, "
                  f"涨停={sector['limit_up_count']}只, "
                  f"强度得分={sector['sector_score']:.1f}")
        
        # 测试板块筛选
        print("\n测试板块筛选...")
        test_stocks = [
            {
                'stock_code': '000001',
                'stock_name': '测试股票1',
                'sector_code': '881157',  # 银行板块
                'amount': 15.2,
                'board_amount': 5250.0,
                'board_ratio': 0.345,
                'turnover_rate': 12.5
            },
            {
                'stock_code': '000002',
                'stock_name': '测试股票2',
                'sector_code': '881138',  # 非银金融板块（下跌）
                'amount': 8.5,
                'board_amount': 2460.0,
                'board_ratio': 0.289,
                'turnover_rate': 15.2
            }
        ]
        
        filtered = filter_by_sector(test_stocks, sector_data, sector_threshold=-0.5, debug=True)
        print(f"板块筛选后剩余: {len(filtered)} 只股票")