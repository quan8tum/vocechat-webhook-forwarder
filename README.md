# VoceChat Webhook 转发服务

这是一个将 VoceChat 的 Webhook 消息转发到企业微信群机器人的服务。

## 功能特性

- 🚀 支持多种 VoceChat 消息类型（文本、Markdown、文件、编辑、删除、回复）
- 🔒 安全的 IP 白名单和 API 密钥验证
- 🎯 灵活的消息过滤（用户黑名单、频道黑名单、消息长度限制）
- 📝 详细的日志记录和错误处理
- ⚙️ 丰富的配置选项
- 📊 运行状态统计接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 启动服务

```bash
# Linux/macOS
./start.sh

# Windows
start.bat

# 或直接运行
python app.py
```

## 配置说明

### 企业微信配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `WECHAT_WEBHOOK_URL` | 企业微信群机器人 Webhook 地址 | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` |
| `WECHAT_MENTIONED_LIST` | @成员列表（可选） | `["user1", "user2"]` |
| `WECHAT_MENTIONED_MOBILE_LIST` | @手机号列表（可选） | `["13800138000"]` |

### 服务器配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SERVER_HOST` | 服务器监听地址 | `0.0.0.0` |
| `SERVER_PORT` | 服务器端口 | `8080` |
| `SERVER_DEBUG` | 调试模式 | `false` |

### 安全配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECURITY_IP_WHITELIST` | IP 白名单 | `[]` |
| `SECURITY_API_KEY` | API 密钥（可选） | |

### VoceChat 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VOCECHAT_ALLOWED_MESSAGE_TYPES` | 允许的消息类型 | `["normal", "edit", "delete", "reply"]` |
| `VOCECHAT_IGNORE_BOT_MESSAGES` | 忽略机器人消息 | `true` |
| `VOCECHAT_BOT_USER_IDS` | 机器人用户ID列表 | `[]` |
| `VOCECHAT_MAX_MESSAGE_LENGTH` | 最大消息长度 | `1000` |
| `VOCECHAT_USER_BLACKLIST` | 用户黑名单 | `[]` |
| `VOCECHAT_CHANNEL_BLACKLIST` | 频道黑名单 | `[]` |
| `VOCECHAT_PROCESS_FILE_MESSAGES` | 处理文件消息 | `true` |
| `VOCECHAT_PROCESS_EDIT_MESSAGES` | 处理编辑消息 | `true` |
| `VOCECHAT_PROCESS_DELETE_MESSAGES` | 处理删除消息 | `true` |
| `VOCECHAT_PROCESS_REPLY_MESSAGES` | 处理回复消息 | `true` |

### 日志配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `webhook.log` |
| `LOG_MAX_SIZE` | 日志文件最大大小(MB) | `10` |
| `LOG_BACKUP_COUNT` | 日志备份数量 | `5` |

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
