#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
从环境变量加载配置
"""

import os
import json
from typing import List, Dict, Any

def get_env_bool(key: str, default: bool = False) -> bool:
    """从环境变量获取布尔值"""
    value = os.getenv(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    elif value in ('false', '0', 'no', 'off'):
        return False
    return default

def get_env_int(key: str, default: int = 0) -> int:
    """从环境变量获取整数值"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """从环境变量获取列表（逗号分隔）"""
    if default is None:
        default = []
    
    value = os.getenv(key, '')
    if not value:
        return default
    
    # 支持 JSON 格式
    if value.startswith('[') and value.endswith(']'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # 逗号分隔格式
    return [item.strip() for item in value.split(',') if item.strip()]

# 企业微信配置
WECHAT_CONFIG = {
    'webhook_url': os.getenv('WECHAT_WEBHOOK_URL'),
    'mentioned_list': get_env_list('WECHAT_MENTIONED_LIST'),
    'mentioned_mobile_list': get_env_list('WECHAT_MENTIONED_MOBILE_LIST')
}

# 服务器配置
SERVER_CONFIG = {
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),
    'port': get_env_int('SERVER_PORT', 8080),
    'debug': get_env_bool('SERVER_DEBUG', False)
}

# 安全配置
SECURITY_CONFIG = {
    'ip_whitelist': get_env_list('SECURITY_IP_WHITELIST'),
    'api_key': os.getenv('SECURITY_API_KEY')
}

# VoceChat 配置
VOCECHAT_CONFIG = {
    'allowed_message_types': get_env_list('VOCECHAT_ALLOWED_MESSAGE_TYPES', ['normal', 'edit', 'delete', 'reply']),
    'ignore_bot_messages': get_env_bool('VOCECHAT_IGNORE_BOT_MESSAGES', True),
    'bot_user_ids': get_env_list('VOCECHAT_BOT_USER_IDS'),
    'max_message_length': get_env_int('VOCECHAT_MAX_MESSAGE_LENGTH', 4000),
    'user_blacklist': get_env_list('VOCECHAT_USER_BLACKLIST'),
    'channel_blacklist': get_env_list('VOCECHAT_CHANNEL_BLACKLIST'),
    'process_file_messages': get_env_bool('VOCECHAT_PROCESS_FILE_MESSAGES', True),
    'process_edit_messages': get_env_bool('VOCECHAT_PROCESS_EDIT_MESSAGES', True),
    'process_delete_messages': get_env_bool('VOCECHAT_PROCESS_DELETE_MESSAGES', True),
    'process_reply_messages': get_env_bool('VOCECHAT_PROCESS_REPLY_MESSAGES', True)
}

# 日志配置
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file': os.getenv('LOG_FILE', 'vocechat_webhook.log'),
    'max_size': get_env_int('LOG_MAX_SIZE', 10),  # MB
    'backup_count': get_env_int('LOG_BACKUP_COUNT', 5)
}

# 配置验证
def validate_config():
    """验证配置"""
    errors = []
    
    # 检查必需的配置
    if not WECHAT_CONFIG['webhook_url']:
        errors.append("WECHAT_WEBHOOK_URL 环境变量未设置")
    
    # 检查端口范围
    if not (1 <= SERVER_CONFIG['port'] <= 65535):
        errors.append(f"SERVER_PORT 必须在 1-65535 范围内，当前值: {SERVER_CONFIG['port']}")
    
    # 检查日志级别
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOG_CONFIG['level'].upper() not in valid_log_levels:
        errors.append(f"LOG_LEVEL 必须是 {valid_log_levels} 中的一个，当前值: {LOG_CONFIG['level']}")
    
    # 检查消息类型
    valid_message_types = ['normal', 'edit', 'delete', 'reply']
    for msg_type in VOCECHAT_CONFIG['allowed_message_types']:
        if msg_type not in valid_message_types:
            errors.append(f"无效的消息类型: {msg_type}，有效类型: {valid_message_types}")
    
    if errors:
        raise ValueError("配置验证失败:\n" + "\n".join(f"- {error}" for error in errors))

if __name__ == '__main__':
    # 验证配置
    try:
        validate_config()
        print("✅ 配置验证通过")
        
        # 打印配置信息（隐藏敏感信息）
        print("\n📋 当前配置:")
        print(f"服务器: {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
        print(f"调试模式: {SERVER_CONFIG['debug']}")
        print(f"企业微信 Webhook: {'已配置' if WECHAT_CONFIG['webhook_url'] else '未配置'}")
        print(f"安全配置: IP白名单={len(SECURITY_CONFIG['ip_whitelist'])}个, API密钥={'已设置' if SECURITY_CONFIG['api_key'] else '未设置'}")
        print(f"VoceChat 过滤: 允许消息类型={VOCECHAT_CONFIG['allowed_message_types']}")
        print(f"日志配置: 级别={LOG_CONFIG['level']}, 文件={LOG_CONFIG['file']}")
        
    except ValueError as e:
        print(f"❌ {e}")
        exit(1)
