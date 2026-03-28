# 如何将技能代码推送到GitHub

## 方法1：使用GitHub CLI（最简单）

如果您已经安装了GitHub CLI，运行：
```bash
gh repo create stock-strong-board --public --description "沪深A股短线强势封板股分析技能" --source=. --remote=origin --push
```

## 方法2：使用个人访问令牌(PAT)

### 步骤1：生成PAT
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 选择 "classic" token
4. 设置权限：选择 `repo`（完全控制仓库）
5. 生成并复制token（看起来像 `ghp_xxxxxxxxxxxxxxxxxxxx`）

### 步骤2：推送代码
运行以下命令（将 `YOUR_TOKEN` 替换为您的PAT）：
```bash
# 进入技能目录
cd /workspace/projects/workspace/skills/stock-strong-board

# 使用PAT配置远程仓库
git remote add origin https://YOUR_TOKEN@github.com/Aiknighterrant/stock-strong-board.git

# 推送代码
git push -u origin main
```

或者使用提供的脚本：
```bash
cd /workspace/projects/workspace/skills/stock-strong-board
./push_to_github.sh YOUR_TOKEN
```

## 方法3：使用SSH密钥

### 步骤1：配置SSH密钥
1. 生成SSH密钥（如果还没有）：
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. 将公钥添加到GitHub：
   - 复制 `~/.ssh/id_ed25519.pub` 内容
   - 访问 https://github.com/settings/keys
   - 点击 "New SSH key"
   - 粘贴公钥

### 步骤2：使用SSH URL推送
```bash
cd /workspace/projects/workspace/skills/stock-strong-board
git remote set-url origin git@github.com:Aiknighterrant/stock-strong-board.git
git push -u origin main
```

## 方法4：通过GitHub网页界面

### 步骤1：创建空仓库
1. 访问 https://github.com/new
2. 填写信息：
   - Repository name: `stock-strong-board`
   - Description: `沪深A股短线强势封板股分析技能`
   - Public
   - 不要初始化README、.gitignore或license
3. 点击 "Create repository"

### 步骤2：按照GitHub的提示推送
创建后，GitHub会显示类似这样的命令：
```bash
git remote add origin https://github.com/Aiknighterrant/stock-strong-board.git
git branch -M main
git push -u origin main
```

## 验证推送成功

推送成功后，您可以：
1. 访问 https://github.com/Aiknighterrant/stock-strong-board
2. 查看所有文件是否已上传
3. 检查提交历史

## 故障排除

### 错误：认证失败
- 确保PAT有正确的权限（`repo`）
- 检查PAT是否已过期
- 尝试重新生成PAT

### 错误：仓库不存在
- 确保仓库已创建
- 检查仓库URL是否正确
- 确保您有仓库的写入权限

### 错误：网络问题
- 检查网络连接
- 尝试使用SSH方式
- 使用GitHub CLI可能更稳定

## 成功推送后的操作

1. **启用GitHub Pages**（可选）：
   - 设置 → Pages → Source: `main` branch, `/docs` folder

2. **查看自动化测试**：
   - Actions标签页会显示测试结果

3. **分享仓库**：
   - 将仓库链接分享给其他人
   - 可以添加协作者

## 联系支持

如果遇到问题：
1. 查看GitHub文档：https://docs.github.com
2. 检查GitHub状态：https://www.githubstatus.com
3. 在GitHub仓库中创建Issue

---

**提示**：推荐使用方法2（PAT）或方法3（SSH），这些方法更安全且方便。