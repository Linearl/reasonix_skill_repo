# mail-skill 技能 — 修改说明

## 原始来源
- **仓库**: [lgwanai/mail-skill](https://github.com/lgwanai/mail-skill)（24 ⭐，MIT 协议）
- **原始路径**: 根目录（SKILL.md + scripts/ + config/ + references/）
- **获取时间**: 2026-08-24

## 我们的修改

### 1. 删除 config.txt（脱敏）
**删除文件**: `config.txt`

**删除原因**: 原始 config.txt 含用户真实凭据（邮箱地址 + 授权码），不能上传到公开仓库。

**保留**: `example.config.txt`（配置模板，供用户填入自己的凭据）

### 2. 添加 POP3 协议支持说明
**修改文件**: README.md（如有）或在本文件中说明

**修改原因**: 原始 mail-skill 的 IMAP 通道在某些邮箱（如网易 126）会被 "Unsafe Login" 安全机制拦截，但 POP3 通道可用。

**协议选择建议**:
```bash
# 如果 IMAP 被拦截，改用 POP3
MAIL_ACCOUNT_1_PROTOCOL=pop3
MAIL_ACCOUNT_1_POP3_SERVER=pop.126.com
MAIL_ACCOUNT_1_POP3_PORT=995
```

### 3. 凭据说明
- 真实凭据存储在 `global-workspace/credential/garden-image-tts-keys.md`（本地，不上传）
- 126 邮箱的 "Unsafe Login" 问题解决方案见记忆 `mail-126-credential`

## 使用方式
```bash
# 收取邮件（POP3 协议）
python scripts/mail_cli.py fetch --days 7

# 搜索邮件
python scripts/mail_cli.py search --query "keyword"

# 发送邮件（SMTP，不需要修改）
python scripts/mail_cli.py send --to xxx@xxx.com --subject "Test" --body "Hello"
```

## 依赖安装
```bash
pip install imap-tools python-dotenv beautifulsoup4 jinja2 markdown chromadb sentence-transformers
```

## 许可证
MIT © lgwanai（原始作者）
