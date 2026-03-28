# 如何手动添加GitHub Actions工作流

由于GitHub对个人访问令牌(PAT)的权限限制，自动化测试工作流无法通过PAT推送。您需要手动在GitHub网页上添加工作流文件。

## 方法1：通过GitHub网页添加

### 步骤1：访问工作流目录
1. 打开您的仓库：https://github.com/Aiknighterrant/stock-strong-board
2. 点击 "Add file" → "Create new file"
3. 输入文件路径：`.github/workflows/test.yml`

### 步骤2：复制工作流内容
复制以下内容到文件中：

```yaml
name: Test Stock Strong Board Skill

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Test skill structure
      run: |
        echo "Checking skill structure..."
        ls -la
        ls -la scripts/
        ls -la references/
        
        [ -f SKILL.md ] && echo "✓ SKILL.md exists" || exit 1
        [ -f README.md ] && echo "✓ README.md exists" || exit 1
        [ -f requirements.txt ] && echo "✓ requirements.txt exists" || exit 1
    
    - name: Test Python scripts
      run: |
        echo "Testing Python scripts..."
        python scripts/main.py --help
        python scripts/main.py --date today --test --output json --limit 3
        
        python -c "import scripts.utils; print('✓ utils module imports successfully')"
        python -c "import scripts.fetch_stock_data; print('✓ fetch_stock_data module imports successfully')"
        python -c "import scripts.filter_stocks; print('✓ filter_stocks module imports successfully')"
        python -c "import scripts.analyze_sectors; print('✓ analyze_sectors module imports successfully')"
    
    - name: Run basic tests
      run: |
        echo "Running basic functionality tests..."
        python scripts/main.py --help > /dev/null && echo "✓ Help command works"
        python scripts/main.py --date today --test --output table --limit 5 > /dev/null && echo "✓ Test mode works"
        python scripts/main.py --date today --test --output json --limit 3 > /dev/null && echo "✓ JSON output works"
        python scripts/main.py --date today --test --output csv --limit 2 > /dev/null && echo "✓ CSV output works"
    
    - name: Validate skill
      run: |
        echo "Validating skill structure..."
        if grep -q "description:" SKILL.md; then
          echo "✓ SKILL.md has description field"
        else
          echo "✗ SKILL.md missing description field"
          exit 1
        fi
        
        if grep -q "name:" SKILL.md; then
          echo "✓ SKILL.md has name field"
        else
          echo "✗ SKILL.md missing name field"
          exit 1
        fi
```

### 步骤3：提交文件
4. 在页面底部填写提交信息："Add GitHub Actions workflow"
5. 选择 "Commit directly to the main branch"
6. 点击 "Commit new file"

## 方法2：使用SSH密钥推送

如果您配置了SSH密钥，可以使用以下命令：

```bash
# 切换到SSH URL
git remote set-url origin git@github.com:Aiknighterrant/stock-strong-board.git

# 恢复工作流文件
mkdir -p .github/workflows

# 创建test.yml文件（内容同上）
# ... 复制上面的YAML内容到 .github/workflows/test.yml ...

# 提交并推送
git add .github/
git commit -m "Add GitHub Actions workflow"
git push origin main
```

## 方法3：更新PAT权限

### 步骤1：更新PAT权限
1. 访问 https://github.com/settings/tokens
2. 找到您的PAT (以 ghp_ 开头)
3. 点击 "Edit"
4. 在权限部分，找到 "Workflow" 并勾选
5. 点击 "Update token"

### 步骤2：重新推送
```bash
# 使用更新后的PAT
git remote set-url origin https://<UPDATED_PAT>@github.com/Aiknighterrant/stock-strong-board.git

# 恢复工作流文件
mkdir -p .github/workflows
# ... 创建test.yml文件 ...

# 推送
git add .
git commit -m "Add GitHub Actions workflow with updated PAT"
git push origin main
```

## 验证工作流运行

添加工作流后：
1. 访问 https://github.com/Aiknighterrant/stock-strong-board/actions
2. 您应该看到工作流正在运行或已经完成
3. 绿色勾号表示测试通过

## 工作流功能

这个工作流提供：
- ✅ **多Python版本测试**：3.8, 3.9, 3.10, 3.11
- ✅ **技能结构验证**：检查必需文件是否存在
- ✅ **脚本功能测试**：测试所有Python模块
- ✅ **基本功能验证**：测试命令行参数和输出格式
- ✅ **自动触发**：推送代码或创建PR时自动运行

## 故障排除

### 工作流不运行
- 检查文件路径是否正确：`.github/workflows/test.yml`
- 确保文件使用YAML格式
- 检查YAML缩进（必须是空格，不能是制表符）

### 测试失败
- 检查Python版本兼容性
- 查看详细的错误日志
- 确保requirements.txt中的依赖正确

### 权限问题
- 确保PAT有 `workflow` 权限
- 或者使用SSH密钥
- 或者通过网页手动添加

## 不需要工作流的情况

如果您不需要自动化测试，可以：
1. 忽略这个文件
2. 手动运行测试：`python scripts/main.py --date today --test`
3. 技能功能完全正常，工作流只是额外的质量保证

---

**注意**：即使没有GitHub Actions工作流，技能本身的功能也是完整的。工作流只是提供了自动化的测试和质量保证。