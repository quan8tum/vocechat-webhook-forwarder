#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoceChat Webhook 转发服务
将 VoceChat 的 Webhook 消息转发到企业微信群机器人
"""

import json
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from bottle import Bottle, request, response, run

from config import (
    WECHAT_CONFIG, SERVER_CONFIG, SECURITY_CONFIG, 
    LOG_CONFIG, VOCECHAT_CONFIG
)

# 创建 Bottle 应用
app = Bottle()

# 全局统计
stats = {
    'requests_count': 0,
    'start_time': time.time(),
    'last_request_time': None,
    'errors_count': 0
}

def setup_logging():
    """设置日志配置"""
    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器（轮转日志）
    if LOG_CONFIG['file']:
        file_handler = RotatingFileHandler(
            LOG_CONFIG['file'],
            maxBytes=LOG_CONFIG['max_size'] * 1024 * 1024,  # 转换为字节
            backupCount=LOG_CONFIG['backup_count']
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 设置日志
logger = setup_logging()

@app.route('/health', method='GET')
def health_check():
    """健康检查接口"""
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}

@app.route('/webhook/vocechat', method=['GET', 'POST'])
def vocechat_webhook():
    """VoceChat Webhook 接口"""
    global stats
    stats['requests_count'] += 1
    stats['last_request_time'] = time.time()
    
    try:
        # GET 请求用于 VoceChat 的预校验
        if request.method == 'GET':
            logger.info("VoceChat webhook 预校验请求")
            return {'status': 'ok'}
        
        # 获取请求数据
        try:
            # 尝试解析 JSON
            data = request.json
            if not data:
                # 如果 JSON 为空，尝试表单数据
                data = dict(request.forms)
                if not data:
                    raise ValueError("No data received")
        except Exception as e:
            logger.error(f"解析请求数据失败: {e}")
            response.status = 400
            return {'error': 'Invalid request data'}
        
        logger.info(f"收到 VoceChat webhook 数据: {json.dumps(data, ensure_ascii=False)}")
        
        # 安全检查
        if not security_check(request):
            stats['errors_count'] += 1
            response.status = 403
            return {'error': 'Access denied'}
        
        # 消息过滤
        if should_filter_message(data):
            logger.info("消息被过滤，跳过处理")
            return {'status': 'filtered'}
        
        # 格式化消息
        wechat_message = format_vocechat_message(data)
        if not wechat_message:
            logger.warning("消息格式化失败")
            return {'status': 'format_error'}
        
        # 发送到企业微信
        success = send_to_wechat(wechat_message)
        
        if success:
            return {'status': 'success'}
        else:
            stats['errors_count'] += 1
            response.status = 500
            return {'status': 'send_failed'}
            
    except Exception as e:
        logger.error(f"处理 webhook 请求时发生错误: {e}")
        stats['errors_count'] += 1
        response.status = 500
        return {'error': str(e)}

@app.route('/test', method='GET')
def test_webhook():
    """测试企业微信 Webhook"""
    test_message = {
        'msgtype': 'text',
        'text': {
            'content': f'🧪 VoceChat Webhook 转发服务测试\n\n⏰ 测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n✅ 服务运行正常',
            'mentioned_list': WECHAT_CONFIG.get('mentioned_list', []),
            'mentioned_mobile_list': WECHAT_CONFIG.get('mentioned_mobile_list', [])
        }
    }
    
    success = send_to_wechat(test_message)
    
    if success:
        return {'status': 'success', 'message': '测试消息发送成功'}
    else:
        response.status = 500
        return {'status': 'failed', 'message': '测试消息发送失败'}

@app.route('/stats', method='GET')
def get_stats():
    """获取服务统计信息"""
    uptime = time.time() - stats['start_time']
    
    return {
        'requests_count': stats['requests_count'],
        'errors_count': stats['errors_count'],
        'uptime_seconds': int(uptime),
        'uptime_human': f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        'last_request_time': datetime.fromtimestamp(stats['last_request_time']).isoformat() if stats['last_request_time'] else None,
        'start_time': datetime.fromtimestamp(stats['start_time']).isoformat(),
        'config': {
            'server': SERVER_CONFIG,
            'wechat_configured': bool(WECHAT_CONFIG.get('webhook_url')),
            'security_enabled': bool(SECURITY_CONFIG.get('ip_whitelist') or SECURITY_CONFIG.get('api_key')),
            'vocechat_filters': {
                'allowed_message_types': VOCECHAT_CONFIG['allowed_message_types'],
                'ignore_bot_messages': VOCECHAT_CONFIG['ignore_bot_messages'],
                'max_message_length': VOCECHAT_CONFIG['max_message_length']
            }
        }
    }

def security_check(request):
    """安全检查"""
    # IP 白名单检查
    if SECURITY_CONFIG.get('ip_whitelist'):
        client_ip = request.environ.get('REMOTE_ADDR')
        if client_ip not in SECURITY_CONFIG['ip_whitelist']:
            logger.warning(f"IP {client_ip} 不在白名单中")
            return False
    
    # API 密钥检查
    if SECURITY_CONFIG.get('api_key'):
        api_key = request.headers.get('X-API-Key') or request.query.get('api_key')
        if api_key != SECURITY_CONFIG['api_key']:
            logger.warning("API 密钥验证失败")
            return False
    
    return True

def should_filter_message(data):
    """检查消息是否应该被过滤"""
    try:
        # 获取消息详情
        detail = data.get('detail', {})
        message_type = detail.get('type', 'normal')
        content = detail.get('content', '')
        content_type = detail.get('content_type', '')
        
        # 获取用户和频道信息
        from_uid = data.get('from_uid')
        target = data.get('target', {})
        gid = target.get('gid')  # 频道ID
        
        # 检查消息类型是否允许
        if message_type not in VOCECHAT_CONFIG['allowed_message_types']:
            logger.info(f"消息类型 {message_type} 不在允许列表中")
            return True
        
        # 检查特定消息类型的处理开关
        if message_type == 'edit' and not VOCECHAT_CONFIG['process_edit_messages']:
            logger.info("编辑消息处理已禁用")
            return True
        
        if message_type == 'delete' and not VOCECHAT_CONFIG['process_delete_messages']:
            logger.info("删除消息处理已禁用")
            return True
        
        if message_type == 'reply' and not VOCECHAT_CONFIG['process_reply_messages']:
            logger.info("回复消息处理已禁用")
            return True
        
        # 检查文件消息
        if content_type == 'vocechat/file' and not VOCECHAT_CONFIG['process_file_messages']:
            logger.info("文件消息处理已禁用")
            return True
        
        # 检查机器人消息
        if VOCECHAT_CONFIG['ignore_bot_messages']:
            bot_user_ids = VOCECHAT_CONFIG.get('bot_user_ids', [])
            if bot_user_ids and from_uid in bot_user_ids:
                logger.info(f"忽略机器人用户 {from_uid} 的消息")
                return True
        
        # 检查用户黑名单
        if from_uid in VOCECHAT_CONFIG['user_blacklist']:
            logger.info(f"用户 {from_uid} 在黑名单中")
            return True
        
        # 检查频道黑名单
        if gid in VOCECHAT_CONFIG['channel_blacklist']:
            logger.info(f"频道 {gid} 在黑名单中")
            return True
        
        # 检查消息长度（仅对文本内容）
        if isinstance(content, str) and len(content) > VOCECHAT_CONFIG['max_message_length']:
            logger.info(f"消息长度 {len(content)} 超过限制 {VOCECHAT_CONFIG['max_message_length']}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"消息过滤检查时发生错误: {e}")
        return True  # 出错时过滤消息

def format_vocechat_message(data):
    """将 VoceChat 消息格式化为企业微信消息"""
    try:
        # 获取基本信息
        detail = data.get('detail', {})
        message_type = detail.get('type', 'normal')
        content = detail.get('content', '')
        content_type = detail.get('content_type', '')
        
        from_uid = data.get('from_uid', 'Unknown')
        mid = data.get('mid', 'Unknown')
        created_at = data.get('created_at', 0)
        
        target = data.get('target', {})
        gid = target.get('gid', 'Unknown')
        
        # 格式化时间
        if created_at:
            timestamp = datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 根据消息类型构建标题和内容
        if message_type == 'normal':
            if content_type == 'vocechat/file':
                # 文件消息
                if isinstance(content, dict):
                    file_name = content.get('name', 'Unknown')
                    file_size = content.get('size', 0)
                    file_type = content.get('content_type', 'Unknown')
                    
                    title = "📎 VoceChat 文件消息"
                    message_content = f"文件名: {file_name}\n文件大小: {file_size} bytes\n文件类型: {file_type}"
                else:
                    title = "📎 VoceChat 文件消息"
                    message_content = str(content)
            else:
                # 普通文本/Markdown消息
                title = "📝 VoceChat 新消息"
                message_content = str(content)
        
        elif message_type == 'edit':
            title = "✏️ VoceChat 消息编辑"
            message_content = f"编辑后内容: {content}"
        
        elif message_type == 'delete':
            title = "🗑️ VoceChat 消息删除"
            message_content = "消息已被删除"
        
        elif message_type == 'reply':
            title = "💬 VoceChat 回复消息"
            reply_mid = detail.get('reply_mid', 'Unknown')
            message_content = f"回复消息 #{reply_mid}: {content}"
        
        else:
            title = "📨 VoceChat 消息"
            message_content = str(content)
        
        # 构建完整消息
        full_message = f"{title}\n\n👤 用户: {from_uid}\n📢 频道: {gid}\n🆔 消息ID: {mid}\n🕐 时间: {timestamp}\n\n💬 内容: {message_content}"
        
        # 构建企业微信消息格式
        wechat_message = {
            'msgtype': 'text',
            'text': {
                'content': full_message,
                'mentioned_list': WECHAT_CONFIG.get('mentioned_list', []),
                'mentioned_mobile_list': WECHAT_CONFIG.get('mentioned_mobile_list', [])
            }
        }
        
        return wechat_message
        
    except Exception as e:
        logger.error(f"格式化消息时发生错误: {e}")
        return None

def send_to_wechat(message):
    """发送消息到企业微信"""
    webhook_url = WECHAT_CONFIG.get('webhook_url')
    if not webhook_url:
        logger.error("企业微信 Webhook URL 未配置")
        return False
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            webhook_url,
            json=message,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"企业微信 API 返回错误: {result}")
                return False
        else:
            logger.error(f"HTTP 请求失败: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"发送消息到企业微信时发生网络错误: {e}")
        return False
    except Exception as e:
        logger.error(f"发送消息到企业微信时发生未知错误: {e}")
        return False

def run_server():
    """启动服务器"""
    host = SERVER_CONFIG['host']
    port = SERVER_CONFIG['port']
    debug = SERVER_CONFIG['debug']
    
    logger.info(f"🚀 VoceChat Webhook 转发服务启动")
    logger.info(f"📡 服务地址: http://{host}:{port}")
    logger.info(f"🔗 Webhook 接口: http://{host}:{port}/webhook/vocechat")
    logger.info(f"❤️ 健康检查: http://{host}:{port}/health")
    logger.info(f"🧪 测试接口: http://{host}:{port}/test")
    logger.info(f"📊 统计接口: http://{host}:{port}/stats")
    
    # 检查企业微信配置
    if not WECHAT_CONFIG.get('webhook_url'):
        logger.warning("⚠️ 企业微信 Webhook URL 未配置，请检查环境变量 WECHAT_WEBHOOK_URL")
    else:
        logger.info("✅ 企业微信 Webhook 配置正常")
    
    # 启动服务
    run(app, host=host, port=port, debug=debug, quiet=not debug)

if __name__ == '__main__':
    run_server()
