#!/usr/bin/env python3
"""
股票筛选模块 - 封板强度和换手率筛选
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import log_debug, remove_outliers_iqr, calculate_filter_score

def filter_by_board_strength(stocks: List[Dict[str, Any]], 
                            min_amount: float = 1.0,
                            top_n: int = 25,
                            debug: bool = False) -> List[Dict[str, Any]]:
    """
    封板强度筛选
    
    Args:
        stocks: 股票数据列表
        min_amount: 最小成交额（亿元）
        top_n: 保留封板成交比前N名
        debug: 调试模式
    
    Returns:
        筛选后的股票列表
    """
    if not stocks:
        return []
    
    log_debug(f"开始封板强度筛选，初始股票数: {len(stocks)}", debug)
    log_debug(f"筛选参数: min_amount={min_amount}亿, top_n={top_n}", debug)
    
    filtered_stocks = []
    
    # 步骤1: 剔除成交额≤min_amount的股票
    step1_stocks = []
    for stock in stocks:
        amount = stock.get('amount', 0)
        if amount > min_amount:
            step1_stocks.append(stock)
    
    log_debug(f"步骤1(成交额>{min_amount}亿)后剩余: {len(step1_stocks)}只", debug)
    
    if not step1_stocks:
        return []
    
    # 步骤2: 排除封单金额异常值
    step2_stocks = filter_board_amount_outliers(step1_stocks, debug)
    log_debug(f"步骤2(排除封单异常值)后剩余: {len(step2_stocks)}只", debug)
    
    if not step2_stocks:
        return []
    
    # 步骤3: 计算封板成交比并排序
    step3_stocks = sort_by_board_ratio(step2_stocks, debug)
    
    # 步骤4: 取前top_n名
    if len(step3_stocks) > top_n:
        filtered_stocks = step3_stocks[:top_n]
    else:
        filtered_stocks = step3_stocks
    
    log_debug(f"步骤4(取封板比前{top_n}名)后剩余: {len(filtered_stocks)}只", debug)
    
    # 添加筛选标记和得分
    for i, stock in enumerate(filtered_stocks, 1):
        stock['board_rank'] = i
        stock['filter_score'] = calculate_filter_score(stock)
    
    return filtered_stocks

def filter_board_amount_outliers(stocks: List[Dict[str, Any]], 
                                debug: bool = False) -> List[Dict[str, Any]]:
    """
    排除封单金额异常值
    
    Args:
        stocks: 股票数据列表
        debug: 调试模式
    
    Returns:
        排除异常值后的股票列表
    """
    if not stocks:
        return []
    
    # 提取封单金额
    board_amounts = []
    for stock in stocks:
        board_amount = stock.get('board_amount', 0)
        board_amounts.append(board_amount)
    
    # 使用IQR方法识别异常值
    is_normal = remove_outliers_iqr(board_amounts)
    
    # 保留正常值
    filtered_stocks = []
    for stock, normal in zip(stocks, is_normal):
        if normal:
            filtered_stocks.append(stock)
        else:
            log_debug(f"排除封单异常值: {stock.get('stock_name')} "
                     f"封单金额={stock.get('board_amount', 0):.0f}万", debug)
    
    return filtered_stocks

def sort_by_board_ratio(stocks: List[Dict[str, Any]], 
                       debug: bool = False) -> List[Dict[str, Any]]:
    """
    按封板成交比排序
    
    Args:
        stocks: 股票数据列表
        debug: 调试模式
    
    Returns:
        按封板成交比降序排列的股票列表
    """
    if not stocks:
        return []
    
    # 确保所有股票都有封板成交比
    for stock in stocks:
        if 'board_ratio' not in stock:
            board_amount = stock.get('board_amount', 0)
            amount = stock.get('amount', 0)
            if amount > 0:
                stock['board_ratio'] = board_amount / (amount * 10000)
            else:
                stock['board_ratio'] = 0
    
    # 按封板成交比降序排序
    sorted_stocks = sorted(stocks, key=lambda x: x.get('board_ratio', 0), reverse=True)
    
    # 输出排序信息
    if debug and sorted_stocks:
        log_debug("封板成交比排名前5:", debug)
        for i, stock in enumerate(sorted_stocks[:5], 1):
            log_debug(f"  {i}. {stock.get('stock_name')}: "
                     f"封板比={stock.get('board_ratio', 0):.3f}, "
                     f"封单={stock.get('board_amount', 0):.0f}万, "
                     f"成交额={stock.get('amount', 0):.2f}亿", debug)
    
    return sorted_stocks

def filter_by_turnover(stocks: List[Dict[str, Any]], 
                      min_turnover: float = 10.0,
                      max_turnover: float = 20.0,
                      debug: bool = False) -> List[Dict[str, Any]]:
    """
    换手率筛选
    
    Args:
        stocks: 股票数据列表
        min_turnover: 最小换手率（%）
        max_turnover: 最大换手率（%）
        debug: 调试模式
    
    Returns:
        筛选后的股票列表
    """
    if not stocks:
        return []
    
    log_debug(f"开始换手率筛选，初始股票数: {len(stocks)}", debug)
    log_debug(f"筛选参数: {min_turnover}% ≤ 换手率 ≤ {max_turnover}%", debug)
    
    filtered_stocks = []
    removed_low = 0
    removed_high = 0
    
    for stock in stocks:
        turnover = stock.get('turnover_rate', 0)
        
        if turnover < min_turnover:
            removed_low += 1
            log_debug(f"换手率过低排除: {stock.get('stock_name')} "
                     f"换手率={turnover:.1f}% < {min_turnover}%", debug)
        elif turnover > max_turnover:
            removed_high += 1
            log_debug(f"换手率过高排除: {stock.get('stock_name')} "
                     f"换手率={turnover:.1f}% > {max_turnover}%", debug)
        else:
            filtered_stocks.append(stock)
    
    log_debug(f"换手率筛选结果: 总数{len(stocks)}, "
             f"保留{len(filtered_stocks)}, "
             f"排除过低{removed_low}, 排除过高{removed_high}", debug)
    
    # 更新筛选得分
    for stock in filtered_stocks:
        stock['filter_score'] = calculate_filter_score(stock)
    
    return filtered_stocks

def adjust_turnover_threshold(stocks: List[Dict[str, Any]], 
                             market_avg_turnover: float = None) -> Tuple[float, float]:
    """
    根据市场情况动态调整换手率阈值
    
    Args:
        stocks: 股票数据列表（用于计算市场平均换手率）
        market_avg_turnover: 市场平均换手率（如果为None则自动计算）
    
    Returns:
        (调整后的min_turnover, max_turnover)
    """
    # 默认阈值
    min_turnover = 10.0
    max_turnover = 20.0
    
    # 如果没有提供市场平均换手率，则从数据中计算
    if market_avg_turnover is None and stocks:
        turnovers = [s.get('turnover_rate', 0) for s in stocks]
        valid_turnovers = [t for t in turnovers if t > 0]
        if valid_turnovers:
            market_avg_turnover = np.mean(valid_turnovers)
    
    # 根据市场平均换手率调整阈值
    if market_avg_turnover is not None:
        if market_avg_turnover < 5.0:  # 市场低迷
            min_turnover = 8.0
            max_turnover = 25.0
        elif market_avg_turnover < 8.0:  # 市场偏冷
            min_turnover = 9.0
            max_turnover = 22.0
        elif market_avg_turnover > 15.0:  # 市场过热
            min_turnover = 12.0
            max_turnover = 18.0
        elif market_avg_turnover > 12.0:  # 市场活跃
            min_turnover = 11.0
            max_turnover = 19.0
    
    return min_turnover, max_turnover

def filter_by_market_cap(stocks: List[Dict[str, Any]], 
                        min_cap: float = 50.0,
                        max_cap: float = 1000.0,
                        debug: bool = False) -> List[Dict[str, Any]]:
    """
    市值筛选（可选功能）
    
    Args:
        stocks: 股票数据列表
        min_cap: 最小市值（亿元）
        max_cap: 最大市值（亿元）
        debug: 调试模式
    
    Returns:
        筛选后的股票列表
    """
    if not stocks:
        return []
    
    log_debug(f"开始市值筛选，参数: {min_cap}亿 ≤ 市值 ≤ {max_cap}亿", debug)
    
    filtered_stocks = []
    removed_count = 0
    
    for stock in stocks:
        # 注意：这里需要股票有市值字段，模拟数据中没有
        # 实际使用时需要从数据源获取市值
        market_cap = stock.get('market_cap', 0)
        
        if market_cap == 0:
            # 如果没有市值数据，默认保留
            filtered_stocks.append(stock)
        elif min_cap <= market_cap <= max_cap:
            filtered_stocks.append(stock)
        else:
            removed_count += 1
            log_debug(f"市值筛选排除: {stock.get('stock_name')} "
                     f"市值={market_cap:.1f}亿", debug)
    
    log_debug(f"市值筛选结果: 保留{len(filtered_stocks)}只，排除{removed_count}只", debug)
    
    return filtered_stocks

def filter_special_stocks(stocks: List[Dict[str, Any]], 
                         debug: bool = False) -> List[Dict[str, Any]]:
    """
    特殊股票处理（ST股票、新股等）
    
    Args:
        stocks: 股票数据列表
        debug: 调试模式
    
    Returns:
        处理后的股票列表
    """
    if not stocks:
        return []
    
    filtered_stocks = []
    st_count = 0
    new_stock_count = 0
    
    for stock in stocks:
        stock_code = str(stock.get('stock_code', ''))
        stock_name = stock.get('stock_name', '')
        
        # 检查是否为ST股票
        is_st = False
        if 'ST' in stock_name or 'st' in stock_name.lower():
            is_st = True
        elif stock_name.startswith('*'):
            is_st = True
        
        # 检查是否为新股（根据代码或名称判断）
        # 这里只是示例，实际需要更准确的判断
        is_new = False
        if 'N' in stock_name or '新股' in stock_name:
            is_new = True
        
        if is_st:
            st_count += 1
            log_debug(f"标记ST股票: {stock_name}({stock_code})", debug)
            stock['is_st'] = True
            stock['risk_level'] = 'high'
        elif is_new:
            new_stock_count += 1
            log_debug(f"标记新股: {stock_name}({stock_code})", debug)
            stock['is_new'] = True
            stock['risk_level'] = 'medium'
        else:
            stock['risk_level'] = 'normal'
        
        filtered_stocks.append(stock)
    
    if st_count > 0 or new_stock_count > 0:
        log_debug(f"特殊股票处理: ST股票{st_count}只, 新股{new_stock_count}只", debug)
    
    return filtered_stocks

def calculate_board_strength_score(stock: Dict[str, Any]) -> float:
    """
    计算封板强度得分
    
    Args:
        stock: 股票数据
    
    Returns:
        封板强度得分（0-100）
    """
    # 封板成交比得分（0-50分）
    board_ratio = stock.get('board_ratio', 0)
    ratio_score = min(50, board_ratio * 50)  # 封板比1.0得50分
    
    # 封单金额得分（0-30分）
    board_amount = stock.get('board_amount', 0)
    if board_amount >= 10000:  # 1亿元以上
        amount_score = 30
    elif board_amount >= 5000:  # 5000万-1亿
        amount_score = 25
    elif board_amount >= 2000:  # 2000万-5000万
        amount_score = 20
    elif board_amount >= 1000:  # 1000万-2000万
        amount_score = 15
    elif board_amount >= 500:   # 500万-1000万
        amount_score = 10
    else:
        amount_score = 5
    
    # 成交额得分（0-20分）
    amount = stock.get('amount', 0)
    if amount >= 20:  # 20亿元以上
        turnover_score = 20
    elif amount >= 10:  # 10-20亿元
        turnover_score = 16
    elif amount >= 5:   # 5-10亿元
        turnover_score = 12
    elif amount >= 2:   # 2-5亿元
        turnover_score = 8
    elif amount >= 1:   # 1-2亿元
        turnover_score = 4
    else:
        turnover_score = 0
    
    total_score = ratio_score + amount_score + turnover_score
    return min(100, total_score)

if __name__ == "__main__":
    # 测试筛选功能
    print("测试筛选模块...")
    
    # 创建测试数据
    test_stocks = [
        {
            'stock_code': '000001',
            'stock_name': '测试股票1',
            'amount': 15.2,
            'board_amount': 5250.0,  # 5250万元
            'board_ratio': 0.345,
            'turnover_rate': 12.5
        },
        {
            'stock_code': '000002',
            'stock_name': '测试股票2',
            'amount': 0.8,  # 成交额过低
            'board_amount': 2460.0,
            'board_ratio': 3.075,
            'turnover_rate': 8.2  # 换手率过低
        },
        {
            'stock_code': '000003',
            'stock_name': '测试股票3',
            'amount': 25.6,
            'board_amount': 12800.0,  # 可能异常值
            'board_ratio': 0.5,
            'turnover_rate': 18.7
        },
        {
            'stock_code': '000004',
            'stock_name': '测试股票4',
            'amount': 12.3,
            'board_amount': 6150.0,
            'board_ratio': 0.5,
            'turnover_rate': 22.5  # 换手率过高
        }
    ]
    
    print(f"初始股票数: {len(test_stocks)}")
    
    # 测试封板强度筛选
    filtered = filter_by_board_strength(test_stocks, min_amount=1.0, top_n=3, debug=True)
    print(f"封板强度筛选后: {len(filtered)}只")
    
    # 测试换手率筛选
    filtered = filter_by_turnover(filtered, min_turnover=10.0, max_turnover=20.0, debug=True)
    print(f"换手率筛选后: {len(filtered)}只")
    
    # 测试封板强度得分计算
    if filtered:
        for stock in filtered:
            score = calculate_board_strength_score(stock)
            print(f"{stock['stock_name']} 封板强度得分: {score:.1f}")