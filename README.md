# 沪深A股短线强势封板股分析技能

一个用于识别沪深A股市场中短线强势封板股的OpenClaw技能。该技能通过多步筛选流程，从当日涨停股池中找出具有短线强势特征的封板股票。

## 功能特点

- 🎯 **智能筛选**：四步筛选流程，层层递进
- 📊 **数据全面**：成交额、封单金额、换手率、板块强度等多维度分析
- ⚡ **实时分析**：支持今日和历史日期分析
- 🔧 **参数可调**：灵活调整筛选参数适应不同市场环境
- 📈 **板块评估**：智能评估板块整体表现
- 🎨 **多格式输出**：支持表格、JSON、CSV格式输出

## 筛选流程

1. **获取涨停股池**：根据指定日期获取所有涨停股票
2. **封板强度筛选**：剔除成交额≤1亿，排除封单异常值，取封板成交比前25名
3. **换手率筛选**：剔除换手率<10%或>20%的个股
4. **板块强度筛选**：剔除所属板块下跌或活跃度低的股票

## 安装与使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 基本使用
```bash
# 分析今日强势封板股
python scripts/main.py --date today

# 分析指定日期
python scripts/main.py --date 2026-03-27

# 输出JSON格式
python scripts/main.py --date today --output json

# 保存为CSV文件
python scripts/main.py --date today --output csv --output_file result.csv
```

### 3. 参数说明
```bash
--date DATE          分析日期，格式: YYYY-MM-DD 或 "today" (默认: today)
--output {table,json,csv}  输出格式 (默认: table)
--output_file FILE   输出文件路径
--limit N            输出股票数量限制 (默认: 10)
--min_amount N       最小成交额（亿元）(默认: 1.0)
--min_turnover N     最小换手率（%）(默认: 10.0)
--max_turnover N     最大换手率（%）(默认: 20.0)
--top_n N            封板成交比前N名 (默认: 25)
--sector_threshold N 板块涨跌幅阈值（%）(默认: -0.5)
--sector_score_min N 板块强度最低分 (默认: 60)
--debug              启用调试模式
--test               测试模式（使用模拟数据）
```

## 技能结构

```
stock-strong-board/
├── SKILL.md                 # 技能主文档
├── README.md                # GitHub说明文档
├── requirements.txt         # Python依赖包
├── scripts/                 # 执行脚本
│   ├── main.py             # 主执行脚本
│   ├── fetch_stock_data.py # 数据获取模块
│   ├── filter_stocks.py    # 筛选逻辑模块
│   ├── analyze_sectors.py  # 板块分析模块
│   └── utils.py            # 工具函数模块
└── references/             # 参考资料
    ├── data_sources.md     # 数据源说明
    ├── sector_classification.md  # 板块分类体系
    └── filter_rules.md     # 筛选规则详细说明
```

## 数据源

本技能支持以下免费数据源：
- 东方财富网 - 涨停股池和基础数据
- 新浪财经 - 封单金额和换手率数据
- 同花顺 - 板块分类和表现数据

## 输出字段

筛选结果包含以下字段：
- 股票代码、股票名称
- 成交额（亿元）、封单金额（万元）
- 封板成交比、换手率（%）
- 所属板块、板块涨跌幅（%）
- 板块强度得分、综合筛选得分

## 使用示例

### 示例1：分析今日强势封板股
```bash
python scripts/main.py --date today --output table
```

### 示例2：自定义筛选参数
```bash
python scripts/main.py --date today \
  --min_amount 2 \
  --min_turnover 12 \
  --max_turnover 18 \
  --sector_threshold 0
```

### 示例3：批量分析并保存结果
```bash
# 分析最近3天
for day in today yesterday day_before_yesterday; do
  python scripts/main.py --date $day --output csv --output_file result_$day.csv
done
```

## 开发说明

### 数据源集成
当前版本使用模拟数据，实际使用时需要：
1. 实现真实数据源接口
2. 配置API密钥（如有）
3. 处理网络请求和错误

### 扩展功能
可扩展的功能包括：
- 添加更多技术指标
- 支持更多数据源
- 添加可视化图表
- 集成回测功能

## 注意事项

1. **数据延迟**：免费数据源可能存在15-30分钟延迟
2. **交易日历**：自动跳过非交易日（周末、节假日）
3. **数据完整性**：部分股票可能因数据源限制而缺失某些字段
4. **风险提示**：投资有风险，分析结果仅供参考

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系

- GitHub: [Aiknighterrant](https://github.com/Aiknighterrant)
- 技能作者: Jackey