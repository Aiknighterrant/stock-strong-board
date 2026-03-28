#!/usr/bin/env python3
"""
沪深A股短线强势封板股分析 - 主脚本
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
import json
import pandas as pd

# 添加脚本目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_stock_data import fetch_limit_up_stocks
from filter_stocks import filter_by_board_strength, filter_by_turnover
from analyze_sectors import analyze_sector_strength, filter_by_sector
from utils import format_output, save_results, validate_date

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='沪深A股短线强势封板股分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --date today                         # 分析今日强势封板股
  %(prog)s --date 2025-03-28 --output json     # 分析指定日期并输出JSON
  %(prog)s --date today --min_turnover 8 --max_turnover 25  # 自定义换手率参数
        """
    )
    
    # 主要参数
    parser.add_argument('--date', type=str, default='today',
                       help='分析日期，格式: YYYY-MM-DD 或 "today" (默认: today)')
    parser.add_argument('--output', type=str, default='table',
                       choices=['table', 'json', 'csv'],
                       help='输出格式: table, json, csv (默认: table)')
    parser.add_argument('--output_file', type=str,
                       help='输出文件路径（如: result.csv）')
    parser.add_argument('--limit', type=int, default=10,
                       help='输出股票数量限制 (默认: 10)')
    
    # 筛选参数
    parser.add_argument('--min_amount', type=float, default=1.0,
                       help='最小成交额（亿元）(默认: 1.0)')
    parser.add_argument('--min_turnover', type=float, default=10.0,
                       help='最小换手率（%%）(默认: 10.0)')
    parser.add_argument('--max_turnover', type=float, default=20.0,
                       help='最大换手率（%%）(默认: 20.0)')
    parser.add_argument('--top_n', type=int, default=25,
                       help='封板成交比前N名 (默认: 25)')
    parser.add_argument('--sector_threshold', type=float, default=-0.5,
                       help='板块涨跌幅阈值（%%）(默认: -0.5)')
    parser.add_argument('--sector_score_min', type=int, default=60,
                       help='板块强度最低分 (默认: 60)')
    
    # 调试参数
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式，输出详细信息')
    parser.add_argument('--test', action='store_true',
                       help='测试模式，使用模拟数据')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    print("=" * 80)
    print("沪深A股短线强势封板股分析")
    print("=" * 80)
    
    # 验证日期
    analysis_date = validate_date(args.date)
    if not analysis_date:
        print(f"错误: 无效的日期格式 '{args.date}'")
        sys.exit(1)
    
    print(f"分析日期: {analysis_date}")
    print(f"筛选参数: 成交额≥{args.min_amount}亿, 换手率{args.min_turnover}%-{args.max_turnover}%")
    print(f"        板块阈值>{args.sector_threshold}%%, 板块得分≥{args.sector_score_min}")
    print("-" * 80)
    
    try:
        # 步骤1: 获取涨停股池
        print("步骤1: 获取涨停股池...")
        if args.test:
            # 测试模式使用模拟数据
            stocks = get_test_data()
            print(f"  获取到 {len(stocks)} 只涨停股票（测试数据）")
        else:
            stocks = fetch_limit_up_stocks(analysis_date, debug=args.debug)
            if not stocks:
                print("  错误: 未能获取涨停股票数据")
                sys.exit(1)
            print(f"  获取到 {len(stocks)} 只涨停股票")
        
        # 步骤2: 封板强度筛选
        print("步骤2: 封板强度筛选...")
        filtered_stocks = filter_by_board_strength(
            stocks, 
            min_amount=args.min_amount,
            top_n=args.top_n,
            debug=args.debug
        )
        print(f"  封板强度筛选后剩余 {len(filtered_stocks)} 只股票")
        
        # 步骤3: 换手率筛选
        print("步骤3: 换手率筛选...")
        filtered_stocks = filter_by_turnover(
            filtered_stocks,
            min_turnover=args.min_turnover,
            max_turnover=args.max_turnover,
            debug=args.debug
        )
        print(f"  换手率筛选后剩余 {len(filtered_stocks)} 只股票")
        
        # 步骤4: 板块强度分析
        print("步骤4: 板块强度分析...")
        # 首先分析板块强度
        sector_data = analyze_sector_strength(analysis_date, debug=args.debug)
        
        # 然后根据板块强度筛选股票
        filtered_stocks = filter_by_sector(
            filtered_stocks,
            sector_data,
            sector_threshold=args.sector_threshold,
            sector_score_min=args.sector_score_min,
            debug=args.debug
        )
        print(f"  板块强度筛选后剩余 {len(filtered_stocks)} 只股票")
        
        # 限制输出数量
        if args.limit > 0 and len(filtered_stocks) > args.limit:
            filtered_stocks = filtered_stocks[:args.limit]
            print(f"  限制输出前{args.limit}只股票")
        
        # 输出结果
        print("\n" + "=" * 80)
        print("筛选结果:")
        print("=" * 80)
        
        if not filtered_stocks:
            print("未找到符合条件的股票")
            return
        
        # 格式化输出
        output_text = format_output(filtered_stocks, args.output)
        
        if args.output == 'table':
            print(output_text)
        elif args.output == 'json':
            if args.output_file:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"结果已保存到: {args.output_file}")
            else:
                print(output_text)
        elif args.output == 'csv':
            if args.output_file:
                with open(args.output_file, 'w', encoding='utf-8', newline='') as f:
                    f.write(output_text)
                print(f"结果已保存到: {args.output_file}")
            else:
                print(output_text)
        
        # 保存详细结果
        if args.output_file and args.output != 'csv':
            save_results(filtered_stocks, args.output_file, args.output)
        
        # 输出统计信息
        print("\n" + "-" * 80)
        print("统计信息:")
        print(f"  总涨停股数: {len(stocks)}")
        print(f"  最终筛选数: {len(filtered_stocks)}")
        print(f"  筛选通过率: {len(filtered_stocks)/len(stocks)*100:.1f}%")
        
        # 板块分布
        if filtered_stocks:
            sector_counts = {}
            for stock in filtered_stocks:
                sector = stock.get('sector_name', '未知')
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
            
            print(f"  板块分布: {', '.join([f'{k}({v})' for k, v in sector_counts.items()])}")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def get_test_data():
    """获取测试数据（用于测试模式）"""
    # 使用fetch_stock_data中的模拟数据
    from fetch_stock_data import get_mock_eastmoney_data
    import datetime
    
    # 获取今天的日期
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    test_stocks = get_mock_eastmoney_data(today)
    
    # 只返回部分数据用于测试
    return test_stocks[:10]  # 返回前10只股票

if __name__ == "__main__":
    main()