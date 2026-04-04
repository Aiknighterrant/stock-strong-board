#!/usr/bin/env python3
"""
测试 akshare 数据源
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import time

def test_akshare_functions():
    """测试 akshare 各种函数"""
    print("=" * 60)
    print("akshare 数据源测试")
    print("=" * 60)
    
    # 1. 测试涨停股池
    print("\n1. 涨停股池测试")
    try:
        # 尝试获取涨停股池
        zt_df = ak.stock_zt_pool_em()
        print(f"  涨停股池数据形状: {zt_df.shape}")
        if len(zt_df) > 0:
            print(f"  获取到 {len(zt_df)} 只涨停股票")
            print("  数据列:", list(zt_df.columns))
            print("\n  前3只涨停股:")
            print(zt_df[['代码', '名称', '最新价', '涨跌幅', '成交额', '换手率']].head(3))
        else:
            print("  当前无涨停股数据（可能非交易时间或数据未更新）")
    except Exception as e:
        print(f"  涨停股池获取失败: {e}")
    
    # 2. 测试实时行情
    print("\n2. A股实时行情测试")
    try:
        spot_df = ak.stock_zh_a_spot_em()
        print(f"  实时行情数据形状: {spot_df.shape}")
        if len(spot_df) > 0:
            # 筛选涨停股（涨跌幅 >= 9.5%）
            limit_up = spot_df[spot_df['涨跌幅'] >= 9.5]
            print(f"  总股票数: {len(spot_df)}")
            print(f"  涨停股数: {len(limit_up)}")
            
            if len(limit_up) > 0:
                print("\n  涨停股示例:")
                print(limit_up[['代码', '名称', '最新价', '涨跌幅', '成交额', '换手率']].head(5))
            else:
                print("  当前无涨停股（可能非交易时间）")
    except Exception as e:
        print(f"  实时行情获取失败: {e}")
    
    # 3. 测试历史数据
    print("\n3. 历史数据测试")
    try:
        # 获取贵州茅台的历史数据
        hist_df = ak.stock_zh_a_hist(symbol="000858", period="daily", start_date="20240401", end_date="20240405")
        print(f"  历史数据形状: {hist_df.shape}")
        if len(hist_df) > 0:
            print("  历史数据列:", list(hist_df.columns))
            print("\n  最近3天数据:")
            print(hist_df[['日期', '开盘', '收盘', '涨跌幅', '成交量', '成交额']].head(3))
    except Exception as e:
        print(f"  历史数据获取失败: {e}")
    
    # 4. 测试板块数据
    print("\n4. 板块数据测试")
    try:
        # 获取板块列表
        sector_df = ak.stock_board_industry_name_em()
        print(f"  板块数据形状: {sector_df.shape}")
        if len(sector_df) > 0:
            print(f"  获取到 {len(sector_df)} 个板块")
            print("  前5个板块:")
            print(sector_df[['板块代码', '板块名称', '涨跌幅', '总市值']].head(5))
    except Exception as e:
        print(f"  板块数据获取失败: {e}")
    
    # 5. 测试龙虎榜数据（可能包含封单信息）
    print("\n5. 龙虎榜数据测试")
    try:
        lhb_df = ak.stock_lhb_ggtj_sina(date="20240404")
        print(f"  龙虎榜数据形状: {lhb_df.shape}")
        if len(lhb_df) > 0:
            print(f"  获取到 {len(lhb_df)} 条龙虎榜记录")
            print("  数据列:", list(lhb_df.columns)[:8])
    except Exception as e:
        print(f"  龙虎榜数据获取失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

def check_akshare_availability():
    """检查 akshare 可用性"""
    print("\n检查 akshare 模块可用性:")
    print(f"akshare 版本: {ak.__version__}")
    
    # 列出所有涨停相关函数
    zt_functions = [f for f in dir(ak) if 'zt' in f.lower() or '涨停' in f]
    print(f"\n涨停相关函数 ({len(zt_functions)} 个):")
    for func in sorted(zt_functions):
        print(f"  - {func}")
    
    # 列出所有股票相关函数
    stock_functions = [f for f in dir(ak) if 'stock' in f.lower() and f not in zt_functions]
    print(f"\n股票相关函数 (前20个，共{len(stock_functions)}个):")
    for func in sorted(stock_functions)[:20]:
        print(f"  - {func}")

if __name__ == "__main__":
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_akshare_availability()
    test_akshare_functions()