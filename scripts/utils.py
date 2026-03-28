#!/usr/bin/env python3
"""
工具函数模块
"""

import re
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any, Optional, Union

def validate_date(date_str: str) -> Optional[str]:
    """
    验证日期字符串，返回标准格式的日期字符串
    
    Args:
        date_str: 日期字符串，支持格式：
                 - "today": 今日
                 - "yesterday": 昨日
                 - "YYYY-MM-DD": 标准日期格式
    
    Returns:
        标准格式的日期字符串，如 "2025-03-28"，失败返回None
    """
    try:
        if date_str.lower() == 'today':
            return datetime.now().strftime('%Y-%m-%d')
        elif date_str.lower() == 'yesterday':
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            # 验证日期格式
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None

def is_trading_day(date_str: str) -> bool:
    """
    判断是否为交易日（简化版，实际应使用交易日历）
    
    Args:
        date_str: 日期字符串
    
    Returns:
        是否为交易日
    """
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        # 简单判断：排除周末
        weekday = dt.weekday()  # 0=周一, 6=周日
        if weekday >= 5:  # 周六、周日
            return False
        
        # TODO: 这里应该添加节假日判断
        # 可以使用第三方库如 chinese_calendar 或维护一个节假日列表
        
        return True
    except:
        return False

def calculate_board_amount(bid1_price: float, bid1_volume: int) -> float:
    """
    计算封单金额
    
    Args:
        bid1_price: 买一价（元）
        bid1_volume: 买一量（手）
    
    Returns:
        封单金额（万元）
    """
    # 1手 = 100股
    total_shares = bid1_volume * 100
    board_amount_yuan = bid1_price * total_shares
    board_amount_wan = board_amount_yuan / 10000  # 转换为万元
    return board_amount_wan

def calculate_board_ratio(board_amount: float, amount: float) -> float:
    """
    计算封板成交比
    
    Args:
        board_amount: 封单金额（万元）
        amount: 成交额（亿元）
    
    Returns:
        封板成交比
    """
    if amount <= 0:
        return 0.0
    
    # 将成交额从亿元转换为万元
    amount_wan = amount * 10000
    ratio = board_amount / amount_wan
    return ratio

def remove_outliers_iqr(data: List[float]) -> List[bool]:
    """
    使用IQR方法识别异常值
    
    Args:
        data: 数值列表
    
    Returns:
        布尔列表，True表示正常值，False表示异常值
    """
    if not data:
        return []
    
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    is_normal = [(lower_bound <= x <= upper_bound) for x in data]
    return is_normal

def format_number(value: float, decimals: int = 2) -> str:
    """
    格式化数字，添加千位分隔符
    
    Args:
        value: 数值
        decimals: 小数位数
    
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"
    
    try:
        # 格式化为指定小数位数
        format_str = f"{{:,.{decimals}f}}"
        return format_str.format(value)
    except:
        return str(value)

def format_output(stocks: List[Dict[str, Any]], output_format: str = 'table') -> str:
    """
    格式化输出结果
    
    Args:
        stocks: 股票数据列表
        output_format: 输出格式，支持 'table', 'json', 'csv'
    
    Returns:
        格式化后的字符串
    """
    if not stocks:
        return "无数据"
    
    if output_format == 'json':
        return json.dumps(stocks, ensure_ascii=False, indent=2)
    
    elif output_format == 'csv':
        if not stocks:
            return ""
        
        # 创建DataFrame
        df = pd.DataFrame(stocks)
        
        # 选择要输出的列
        columns = ['stock_code', 'stock_name', 'amount', 'board_amount', 
                  'board_ratio', 'turnover_rate', 'sector_name', 'sector_change']
        
        # 只保留存在的列
        existing_columns = [col for col in columns if col in df.columns]
        df = df[existing_columns]
        
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    else:  # table格式
        if not stocks:
            return "无数据"
        
        # 创建表格输出
        lines = []
        
        # 表头
        header = ["序号", "代码", "名称", "成交额(亿)", "封单(万)", 
                 "封板比", "换手率%", "所属板块", "板块涨幅%"]
        header_line = " | ".join([f"{h:^10}" for h in header])
        separator = "-" * len(header_line)
        
        lines.append(header_line)
        lines.append(separator)
        
        # 数据行
        for i, stock in enumerate(stocks, 1):
            row = [
                str(i),
                stock.get('stock_code', ''),
                stock.get('stock_name', ''),
                format_number(stock.get('amount', 0), 2),
                format_number(stock.get('board_amount', 0), 0),
                format_number(stock.get('board_ratio', 0), 3),
                format_number(stock.get('turnover_rate', 0), 1),
                stock.get('sector_name', '')[:8],  # 截断长板块名
                format_number(stock.get('sector_change', 0), 2)
            ]
            row_line = " | ".join([f"{str(r):^10}" for r in row])
            lines.append(row_line)
        
        return "\n".join(lines)

def save_results(stocks: List[Dict[str, Any]], filepath: str, output_format: str = 'json'):
    """
    保存结果到文件
    
    Args:
        stocks: 股票数据列表
        filepath: 文件路径
        output_format: 输出格式，支持 'json', 'csv'
    """
    if not stocks:
        print("无数据可保存")
        return
    
    try:
        if output_format == 'csv':
            csv_content = format_output(stocks, 'csv')
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write(csv_content)
            print(f"结果已保存为CSV: {filepath}")
        
        elif output_format == 'json':
            json_content = format_output(stocks, 'json')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_content)
            print(f"结果已保存为JSON: {filepath}")
        
        else:
            print(f"不支持的输出格式: {output_format}")
    
    except Exception as e:
        print(f"保存结果失败: {str(e)}")

def calculate_filter_score(stock: Dict[str, Any]) -> float:
    """
    计算综合筛选得分
    
    Args:
        stock: 股票数据
    
    Returns:
        综合得分（0-100）
    """
    scores = []
    weights = []
    
    # 1. 封板成交比得分（权重0.4）
    board_ratio = stock.get('board_ratio', 0)
    board_ratio_score = min(100, board_ratio * 100)  # 假设封板比1.0对应100分
    scores.append(board_ratio_score)
    weights.append(0.4)
    
    # 2. 换手率得分（权重0.2）
    turnover = stock.get('turnover_rate', 0)
    # 理想换手率在15%左右
    if 14 <= turnover <= 16:
        turnover_score = 100
    elif 10 <= turnover <= 20:
        turnover_score = 80 + (20 - abs(turnover - 15)) * 4
    else:
        turnover_score = max(0, 60 - abs(turnover - 15) * 5)
    scores.append(turnover_score)
    weights.append(0.2)
    
    # 3. 板块强度得分（权重0.3）
    sector_score = stock.get('sector_score', 50)
    scores.append(sector_score)
    weights.append(0.3)
    
    # 4. 成交额得分（权重0.1）
    amount = stock.get('amount', 0)
    amount_score = min(100, amount * 4)  # 25亿对应100分
    scores.append(amount_score)
    weights.append(0.1)
    
    # 计算加权平均
    total_score = sum(s * w for s, w in zip(scores, weights))
    return round(total_score, 2)

def parse_stock_code(stock_code: str) -> tuple:
    """
    解析股票代码，返回市场和代码
    
    Args:
        stock_code: 股票代码，如 "000001" 或 "sh600000"
    
    Returns:
        (market, code)，如 ("sz", "000001")
    """
    stock_code = str(stock_code).strip().lower()
    
    # 如果已经包含市场前缀
    if stock_code.startswith('sh'):
        return 'sh', stock_code[2:]
    elif stock_code.startswith('sz'):
        return 'sz', stock_code[2:]
    elif stock_code.startswith('bj'):
        return 'bj', stock_code[2:]
    
    # 根据代码判断市场
    if stock_code.startswith('6'):
        return 'sh', stock_code
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        return 'sz', stock_code
    elif stock_code.startswith('8'):
        return 'bj', stock_code
    else:
        return 'unknown', stock_code

def get_stock_full_code(stock_code: str) -> str:
    """
    获取完整的股票代码（带市场前缀）
    
    Args:
        stock_code: 股票代码
    
    Returns:
        完整代码，如 "sh600000"
    """
    market, code = parse_stock_code(stock_code)
    return f"{market}{code}"

def clean_numeric_value(value: Any, default: float = 0.0) -> float:
    """
    清理数值，转换为浮点数
    
    Args:
        value: 输入值
        default: 默认值
    
    Returns:
        清理后的浮点数
    """
    if value is None:
        return default
    
    try:
        # 如果是字符串，清理特殊字符
        if isinstance(value, str):
            # 移除逗号、空格、百分号等
            cleaned = re.sub(r'[,\s%￥¥$]', '', value)
            # 如果是空字符串
            if not cleaned:
                return default
            # 转换为浮点数
            return float(cleaned)
        else:
            return float(value)
    except (ValueError, TypeError):
        return default

def log_debug(message: str, debug: bool = False):
    """
    调试日志输出
    
    Args:
        message: 日志消息
        debug: 是否启用调试模式
    """
    if debug:
        print(f"[DEBUG] {message}")

if __name__ == "__main__":
    # 测试工具函数
    print("测试 validate_date:")
    print(f"  today: {validate_date('today')}")
    print(f"  yesterday: {validate_date('yesterday')}")
    print(f"  2025-03-28: {validate_date('2025-03-28')}")
    
    print("\n测试 calculate_board_amount:")
    print(f"  买一价10.5元，买一量50000手: {calculate_board_amount(10.5, 50000):.2f}万元")
    
    print("\n测试 calculate_board_ratio:")
    print(f"  封单金额5000万元，成交额10亿元: {calculate_board_ratio(5000, 10):.3f}")