#!/usr/bin/env python3
"""
优化版股票筛选模块
处理封单数据缺失的情况，提供更稳定的筛选
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import log_debug, remove_outliers_iqr, calculate_filter_score

def filter_by_board_strength_optimized(stocks: List[Dict[str, Any]], 
                                      min_amount: float = 1.0,
                                      top_n: int = 25,
                                      debug: bool = False) -> List[Dict[str, Any]]:
    """
    优化版封板强度筛选（处理封单数据缺失）
    
    Args:
        stocks: 股票数据列表
        min_amount: 最小成交额（亿元）
        top_n: 保留前N名
        debug: 调试模式
    
    Returns:
        筛选后的股票列表
    """
    if not stocks:
        return []
    
    log_debug(f"开始优化版封板强度筛选，初始股票数: {len(stocks)}", debug)
    log_debug(f"筛选参数: min_amount={min_amount}亿, top_n={top_n}", debug)
    
    # 检查封单数据可用性
    board_data_available = check_board_data_availability(stocks, debug)
    
    if board_data_available:
        log_debug("封单数据可用，使用标准筛选流程", debug)
        return filter_by_board_strength_standard(stocks, min_amount, top_n, debug)
    else:
        log_debug("封单数据不可用，使用备选筛选流程", debug)
        return filter_by_board_strength_fallback(stocks, min_amount, top_n, debug)

def check_board_data_availability(stocks: List[Dict[str, Any]], debug: bool = False) -> bool:
    """
    检查封单数据可用性
    
    Args:
        stocks: 股票数据列表
        debug: 调试模式
    
    Returns:
        封单数据是否可用
    """
    if not stocks:
        return False
    
    # 检查是否有有效的封单数据
    valid_board_count = 0
    total_count = len(stocks)
    
    for stock in stocks:
        board_amount = stock.get('board_amount', 0)
        if board_amount > 0:
            valid_board_count += 1
    
    availability_rate = valid_board_count / total_count if total_count > 0 else 0
    log_debug(f"封单数据可用性: {valid_board_count}/{total_count} ({availability_rate:.1%})", debug)
    
    # 如果有超过50%的股票有封单数据，则认为可用
    return availability_rate > 0.5

def filter_by_board_strength_standard(stocks: List[Dict[str, Any]], 
                                     min_amount: float = 1.0,
                                     top_n: int = 25,
                                     debug: bool = False) -> List[Dict[str, Any]]:
    """
    标准封板强度筛选（有封单数据时使用）
    """
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
    step2_stocks = filter_board_amount_outliers_optimized(step1_stocks, debug)
    log_debug(f"步骤2(排除封单异常值)后剩余: {len(step2_stocks)}只", debug)
    
    if not step2_stocks:
        return []
    
    # 步骤3: 计算封板成交比并排序
    step3_stocks = sort_by_board_ratio_optimized(step2_stocks, debug)
    
    # 步骤4: 取前top_n名
    if len(step3_stocks) > top_n:
        filtered_stocks = step3_stocks[:top_n]
    else:
        filtered_stocks = step3_stocks
    
    log_debug(f"步骤4(取封板比前{top_n}名)后剩余: {len(filtered_stocks)}只", debug)
    
    return filtered_stocks

def filter_by_board_strength_fallback(stocks: List[Dict[str, Any]], 
                                     min_amount: float = 1.0,
                                     top_n: int = 25,
                                     debug: bool = False) -> List[Dict[str, Any]]:
    """
    备选封板强度筛选（无封单数据时使用）
    基于成交额和换手率筛选
    """
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
    
    # 步骤2: 按成交额排序（成交额越大，资金关注度越高）
    step2_stocks = sorted(step1_stocks, key=lambda x: x.get('amount', 0), reverse=True)
    
    # 步骤3: 考虑换手率（换手率适中为好）
    step3_stocks = []
    for stock in step2_stocks:
        turnover = stock.get('turnover_rate', 0)
        # 换手率在10%-30%之间为佳
        if 10 <= turnover <= 30:
            step3_stocks.append(stock)
    
    log_debug(f"步骤3(换手率10%-30%)后剩余: {len(step3_stocks)}只", debug)
    
    # 步骤4: 综合评分排序
    step4_stocks = sort_by_composite_score(step3_stocks, debug)
    
    # 步骤5: 取前top_n名
    if len(step4_stocks) > top_n:
        filtered_stocks = step4_stocks[:top_n]
    else:
        filtered_stocks = step4_stocks
    
    log_debug(f"步骤5(取综合评分前{top_n}名)后剩余: {len(filtered_stocks)}只", debug)
    
    return filtered_stocks

def filter_board_amount_outliers_optimized(stocks: List[Dict[str, Any]], 
                                         debug: bool = False) -> List[Dict[str, Any]]:
    """
    优化版排除封单金额异常值
    """
    if not stocks:
        return []
    
    # 提取封单金额
    board_amounts = []
    valid_stocks = []
    
    for stock in stocks:
        board_amount = stock.get('board_amount', 0)
        if board_amount > 0:  # 只处理有封单数据的股票
            board_amounts.append(board_amount)
            valid_stocks.append(stock)
    
    if not board_amounts:
        return stocks  # 没有封单数据，返回所有股票
    
    # 使用IQR方法识别异常值
    is_normal = remove_outliers_iqr(board_amounts)
    
    # 保留正常值
    filtered_stocks = []
    for stock, normal in zip(valid_stocks, is_normal):
        if normal:
            filtered_stocks.append(stock)
        else:
            log_debug(f"排除封单异常值: {stock.get('stock_name')} "
                     f"封单金额={stock.get('board_amount', 0):.0f}万", debug)
    
    # 添加没有封单数据的股票（这些股票不参与异常值检测）
    for stock in stocks:
        if stock.get('board_amount', 0) == 0 and stock not in valid_stocks:
            filtered_stocks.append(stock)
    
    return filtered_stocks

def sort_by_board_ratio_optimized(stocks: List[Dict[str, Any]], 
                                 debug: bool = False) -> List[Dict[str, Any]]:
    """
    优化版按封板成交比排序
    """
    if not stocks:
        return []
    
    # 确保所有股票都有封板成交比
    for stock in stocks:
        if 'board_ratio' not in stock or stock.get('board_ratio', 0) == 0:
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

def sort_by_composite_score(stocks: List[Dict[str, Any]], 
                           debug: bool = False) -> List[Dict[str, Any]]:
    """
    按综合评分排序
    评分 = 成交额标准化得分 * 0.6 + 换手率适中得分 * 0.4
    """
    if not stocks:
        return []
    
    # 提取成交额和换手率
    amounts = [stock.get('amount', 0) for stock in stocks]
    turnovers = [stock.get('turnover_rate', 0) for stock in stocks]
    
    if not amounts:
        return stocks
    
    # 标准化成交额（0-1范围）
    max_amount = max(amounts)
    min_amount = min(amounts)
    amount_range = max_amount - min_amount
    
    # 计算换手率适中得分（离15%越近得分越高）
    for i, stock in enumerate(stocks):
        amount = amounts[i]
        turnover = turnovers[i]
        
        # 成交额得分（成交额越大越好）
        if amount_range > 0:
            amount_score = (amount - min_amount) / amount_range
        else:
            amount_score = 0.5
        
        # 换手率得分（离15%越近越好）
        turnover_diff = abs(turnover - 15)
        if turnover_diff <= 15:  # 最大偏差15%
            turnover_score = 1 - (turnover_diff / 15)
        else:
            turnover_score = 0
        
        # 综合得分
        composite_score = amount_score * 0.6 + turnover_score * 0.4
        stock['composite_score'] = composite_score
        stock['amount_score'] = amount_score
        stock['turnover_score'] = turnover_score
    
    # 按综合得分降序排序
    sorted_stocks = sorted(stocks, key=lambda x: x.get('composite_score', 0), reverse=True)
    
    # 输出排序信息
    if debug and sorted_stocks:
        log_debug("综合评分排名前5:", debug)
        for i, stock in enumerate(sorted_stocks[:5], 1):
            log_debug(f"  {i}. {stock.get('stock_name')}: "
                     f"综合分={stock.get('composite_score', 0):.3f}, "
                     f"成交额={stock.get('amount', 0):.2f}亿, "
                     f"换手率={stock.get('turnover_rate', 0):.1f}%", debug)
    
    return sorted_stocks

def filter_by_turnover_optimized(stocks: List[Dict[str, Any]], 
                                min_turnover: float = 10.0,
                                max_turnover: float = 20.0,
                                debug: bool = False) -> List[Dict[str, Any]]:
    """
    优化版换手率筛选
    
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
    
    log_debug(f"开始换手率筛选，参数: {min_turnover}%-{max_turnover}%", debug)
    
    filtered_stocks = []
    for stock in stocks:
        turnover = stock.get('turnover_rate', 0)
        if min_turnover <= turnover <= max_turnover:
            filtered_stocks.append(stock)
        else:
            log_debug(f"排除: {stock.get('stock_name')} 换手率={turnover:.1f}%", debug)
    
    log_debug(f"换手率筛选后剩余: {len(filtered_stocks)}只", debug)
    
    return filtered_stocks

# 兼容性函数
def filter_by_board_strength(stocks: List[Dict[str, Any]], 
                            min_amount: float = 1.0,
                            top_n: int = 25,
                            debug: bool = False) -> List[Dict[str, Any]]:
    """兼容性函数"""
    return filter_by_board_strength_optimized(stocks, min_amount, top_n, debug)

def filter_by_turnover(stocks: List[Dict[str, Any]], 
                      min_turnover: float = 10.0,
                      max_turnover: float = 20.0,
                      debug: bool = False) -> List[Dict[str, Any]]:
    """兼容性函数"""
    return filter_by_turnover_optimized(stocks, min_turnover, max_turnover, debug)

# 测试函数
if __name__ == "__main__":
    # 测试数据
    test_stocks = [
        {
            'stock_code': '000001',
            'stock_name': '测试股票1',
            'amount': 10.5,
            'board_amount': 5000,
            'turnover_rate': 12.5
        },
        {
            'stock_code': '000002',
            'stock_name': '测试股票2',
            'amount': 5.2,
            'board_amount': 0,  # 无封单数据
            'turnover_rate': 18.3
        },
        {
            'stock_code': '000003',
            'stock_name': '测试股票3',
            'amount': 20.8,
            'board_amount': 15000,
            'turnover_rate': 8.7
        }
    ]
    
    print("测试优化版筛选模块:")
    
    # 测试封板强度筛选
    print("\n1. 封板强度筛选测试:")
    filtered = filter_by_board_strength_optimized(test_stocks, debug=True)
    print(f"   筛选结果: {len(filtered)}只股票")
    for stock in filtered:
        print(f"   - {stock['stock_name']}: 成交额={stock['amount']}亿")
    
    # 测试换手率筛选
    print("\n2. 换手率筛选测试:")
    filtered = filter_by_turnover_optimized(test_stocks, min_turnover=10, max_turnover=20, debug=True)
    print(f"   筛选结果: {len(filtered)}只股票")
    for stock in filtered:
        print(f"   - {stock['stock_name']}: 换手率={stock['turnover_rate']}%")