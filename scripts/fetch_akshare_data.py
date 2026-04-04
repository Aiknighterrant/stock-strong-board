#!/usr/bin/env python3
"""
基于 akshare 的实时股票数据获取模块
使用 akshare 获取涨停股、实时行情、板块数据等
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any, Optional
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import log_debug, calculate_board_amount, calculate_board_ratio, clean_numeric_value

class AkshareDataFetcher:
    """akshare 数据获取器"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        
    def fetch_limit_up_stocks(self, date_str: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的涨停股票列表
        
        Args:
            date_str: 日期字符串，格式 "YYYY-MM-DD" 或 "today"
        
        Returns:
            涨停股票列表
        """
        log_debug(f"开始从 akshare 获取 {date_str} 的涨停股票数据", self.debug)
        
        # 处理日期
        if date_str == "today":
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 检查缓存
        cache_key = f"limit_up_{date_str}"
        if cache_key in self.cache:
            cache_data, cache_timestamp = self.cache[cache_key]
            if time.time() - cache_timestamp < self.cache_timeout:
                log_debug(f"使用缓存数据: {len(cache_data)} 只涨停股票", self.debug)
                return cache_data
        
        stocks = []
        
        try:
            # 方法1: 使用涨停股池函数
            log_debug("尝试使用 stock_zt_pool_em 获取涨停股数据", self.debug)
            zt_df = ak.stock_zt_pool_em()
            
            if len(zt_df) > 0:
                log_debug(f"从 stock_zt_pool_em 获取到 {len(zt_df)} 只涨停股票", self.debug)
                
                for _, row in zt_df.iterrows():
                    try:
                        stock_data = self._parse_zt_pool_row(row)
                        if stock_data:
                            stocks.append(stock_data)
                    except Exception as e:
                        log_debug(f"解析股票数据失败: {e}", self.debug)
                        continue
            
            # 如果涨停股池为空，尝试其他方法
            if len(stocks) == 0:
                log_debug("涨停股池为空，尝试使用实时行情筛选涨停股", self.debug)
                stocks = self._fetch_limit_up_from_spot(date_str)
        
        except Exception as e:
            log_debug(f"akshare 涨停股数据获取失败: {e}", self.debug)
            # 尝试备用方法
            stocks = self._fetch_limit_up_from_spot(date_str)
        
        # 更新缓存
        self.cache[cache_key] = (stocks, time.time())
        
        return stocks
    
    def _parse_zt_pool_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """解析涨停股池数据行"""
        try:
            # 获取基础数据
            stock_code = str(row.get('代码', '')).strip()
            stock_name = str(row.get('名称', '')).strip()
            
            if not stock_code or not stock_name:
                return None
            
            # 价格数据
            close_price = clean_numeric_value(row.get('最新价'))
            change_pct = clean_numeric_value(row.get('涨跌幅'))
            
            # 成交数据
            amount = clean_numeric_value(row.get('成交额'))
            if amount > 0:
                amount = amount / 100000000  # 转亿元
            
            volume = clean_numeric_value(row.get('成交量'))
            if volume > 0:
                volume = volume / 10000  # 转万手
            
            turnover_rate = clean_numeric_value(row.get('换手率'))
            
            # 封单数据（如果可用）
            bid_price = clean_numeric_value(row.get('买一价', 0))
            bid_volume = clean_numeric_value(row.get('买一量', 0))
            
            # 计算封单金额（万元）
            board_amount = 0
            if bid_price > 0 and bid_volume > 0:
                board_amount = (bid_price * bid_volume * 100) / 10000
            
            # 计算封板成交比
            board_ratio = 0
            if amount > 0:
                board_ratio = board_amount / (amount * 10000)
            
            # 获取板块信息
            sector_name = str(row.get('所属板块', '')).strip()
            if not sector_name:
                sector_name = self._get_stock_sector(stock_code)
            
            stock_data = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'close_price': round(close_price, 2),
                'change_pct': round(change_pct, 2),
                'amount': round(amount, 2),
                'volume': round(volume, 1),
                'bid1_price': round(bid_price, 2),
                'bid1_volume': int(bid_volume),
                'turnover_rate': round(turnover_rate, 1),
                'sector_code': '',
                'sector_name': sector_name,
                'pe_ratio': clean_numeric_value(row.get('市盈率', 0)),
                'pb_ratio': clean_numeric_value(row.get('市净率', 0)),
                'board_amount': round(board_amount, 0),
                'board_ratio': round(board_ratio, 3)
            }
            
            return stock_data
            
        except Exception as e:
            log_debug(f"解析涨停股数据行失败: {e}", self.debug)
            return None
    
    def _fetch_limit_up_from_spot(self, date_str: str) -> List[Dict[str, Any]]:
        """
        从实时行情中筛选涨停股
        
        Args:
            date_str: 日期字符串
        
        Returns:
            涨停股票列表
        """
        stocks = []
        
        try:
            log_debug("尝试获取A股实时行情", self.debug)
            
            # 获取A股实时行情
            spot_df = ak.stock_zh_a_spot_em()
            
            if len(spot_df) > 0:
                # 筛选涨停股（涨跌幅 >= 9.5%）
                limit_up_df = spot_df[spot_df['涨跌幅'] >= 9.5]
                
                log_debug(f"从实时行情中筛选出 {len(limit_up_df)} 只涨停股票", self.debug)
                
                for _, row in limit_up_df.iterrows():
                    try:
                        stock_code = str(row.get('代码', '')).strip()
                        stock_name = str(row.get('名称', '')).strip()
                        
                        if not stock_code or not stock_name:
                            continue
                        
                        close_price = clean_numeric_value(row.get('最新价'))
                        change_pct = clean_numeric_value(row.get('涨跌幅'))
                        amount = clean_numeric_value(row.get('成交额', 0)) / 100000000
                        turnover_rate = clean_numeric_value(row.get('换手率', 0))
                        
                        # 获取封单数据（如果可用）
                        bid_price = clean_numeric_value(row.get('买一价', 0))
                        bid_volume = clean_numeric_value(row.get('买一量', 0))
                        
                        # 计算封单金额
                        board_amount = 0
                        if bid_price > 0 and bid_volume > 0:
                            board_amount = (bid_price * bid_volume * 100) / 10000
                        
                        # 计算封板成交比
                        board_ratio = 0
                        if amount > 0:
                            board_ratio = board_amount / (amount * 10000)
                        
                        # 获取板块信息
                        sector_name = self._get_stock_sector(stock_code)
                        
                        stock_data = {
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'close_price': round(close_price, 2),
                            'change_pct': round(change_pct, 2),
                            'amount': round(amount, 2),
                            'volume': 0,  # 实时行情可能没有成交量
                            'bid1_price': round(bid_price, 2),
                            'bid1_volume': int(bid_volume),
                            'turnover_rate': round(turnover_rate, 1),
                            'sector_code': '',
                            'sector_name': sector_name,
                            'pe_ratio': 0,
                            'pb_ratio': 0,
                            'board_amount': round(board_amount, 0),
                            'board_ratio': round(board_ratio, 3)
                        }
                        
                        stocks.append(stock_data)
                        
                    except Exception as e:
                        log_debug(f"解析实时行情数据失败: {e}", self.debug)
                        continue
        
        except Exception as e:
            log_debug(f"实时行情获取失败: {e}", self.debug)
        
        return stocks
    
    def _get_stock_sector(self, stock_code: str) -> str:
        """
        获取股票所属板块
        
        Args:
            stock_code: 股票代码
        
        Returns:
            板块名称
        """
        try:
            # 这里可以使用 akshare 的板块相关函数
            # 由于网络问题，这里暂时返回空
            return ""
        except:
            return ""
    
    def fetch_sector_data(self, date_str: str) -> List[Dict[str, Any]]:
        """
        获取板块数据
        
        Args:
            date_str: 日期字符串
        
        Returns:
            板块数据列表
        """
        sectors = []
        
        try:
            log_debug("尝试获取板块数据", self.debug)
            
            # 获取板块列表
            sector_df = ak.stock_board_industry_name_em()
            
            if len(sector_df) > 0:
                for _, row in sector_df.iterrows():
                    try:
                        sector_data = {
                            'sector_code': str(row.get('板块代码', '')),
                            'sector_name': str(row.get('板块名称', '')),
                            'change_pct': clean_numeric_value(row.get('涨跌幅', 0)),
                            'total_market_cap': clean_numeric_value(row.get('总市值', 0)),
                            'turnover_rate': clean_numeric_value(row.get('换手率', 0)),
                            'leading_stock': str(row.get('领涨股票', ''))
                        }
                        
                        sectors.append(sector_data)
                    except:
                        continue
        
        except Exception as e:
            log_debug(f"板块数据获取失败: {e}", self.debug)
        
        return sectors
    
    def fetch_stock_detail(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票详细信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票详细信息
        """
        try:
            log_debug(f"获取股票 {stock_code} 详细信息", self.debug)
            
            # 获取实时行情
            spot_df = ak.stock_zh_a_spot_em()
            
            if len(spot_df) > 0:
                stock_data = spot_df[spot_df['代码'] == stock_code]
                
                if len(stock_data) > 0:
                    row = stock_data.iloc[0]
                    
                    detail = {
                        'stock_code': stock_code,
                        'stock_name': str(row.get('名称', '')),
                        'close_price': clean_numeric_value(row.get('最新价')),
                        'change_pct': clean_numeric_value(row.get('涨跌幅')),
                        'amount': clean_numeric_value(row.get('成交额', 0)) / 100000000,
                        'volume': clean_numeric_value(row.get('成交量', 0)) / 10000,
                        'turnover_rate': clean_numeric_value(row.get('换手率', 0)),
                        'amplitude': clean_numeric_value(row.get('振幅', 0)),
                        'volume_ratio': clean_numeric_value(row.get('量比', 0)),
                        'pe_ratio': clean_numeric_value(row.get('市盈率', 0)),
                        'pb_ratio': clean_numeric_value(row.get('市净率', 0)),
                        'market_cap': clean_numeric_value(row.get('总市值', 0)),
                        'circulating_market_cap': clean_numeric_value(row.get('流通市值', 0))
                    }
                    
                    return detail
        
        except Exception as e:
            log_debug(f"获取股票详细信息失败: {e}", self.debug)
        
        return None

# 兼容性函数
def fetch_limit_up_stocks_akshare(date_str: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    兼容性函数，用于替换原来的 fetch_limit_up_stocks
    
    Args:
        date_str: 日期字符串
        debug: 调试模式
    
    Returns:
        涨停股票列表
    """
    fetcher = AkshareDataFetcher(debug=debug)
    return fetcher.fetch_limit_up_stocks(date_str)

# 测试函数
if __name__ == "__main__":
    print("测试 akshare 数据获取功能...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    fetcher = AkshareDataFetcher(debug=True)
    
    # 测试今日涨停股
    print("\n1. 获取今日涨停股:")
    today_stocks = fetcher.fetch_limit_up_stocks("today")
    print(f"   获取到 {len(today_stocks)} 只涨停股票")
    
    if len(today_stocks) > 0:
        print("   前3只涨停股:")
        for i, stock in enumerate(today_stocks[:3], 1):
            print(f"     {i}. {stock['stock_name']}({stock['stock_code']}) - "
                  f"涨跌幅:{stock['change_pct']}% 成交额:{stock['amount']}亿")
    
    # 测试板块数据
    print("\n2. 获取板块数据:")
    sectors = fetcher.fetch_sector_data("today")
    print(f"   获取到 {len(sectors)} 个板块数据")
    
    if len(sectors) > 0:
        print("   前3个板块:")
        for i, sector in enumerate(sectors[:3], 1):
            print(f"     {i}. {sector['sector_name']} - "
                  f"涨跌幅:{sector['change_pct']}%")