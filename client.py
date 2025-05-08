#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import json
import os
import sys
import argparse

class ConfigManager:
    """配置管理模块，用于保存和加载服务器IP和端口"""
    def __init__(self):
        # 使用用户的.config目录
        config_dir = os.path.join(os.path.expanduser('~'), '.config', 'notifypy')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.config_file = os.path.join(config_dir, 'client_config.json')
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            'server_ip': '127.0.0.1',
            'server_port': 5000
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return default_config
        return default_config
    
    def save_config(self, server_ip, server_port):
        """保存配置到文件"""
        self.config['server_ip'] = server_ip
        self.config['server_port'] = int(server_port)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

class MessageSender:
    """消息发送模块，通过socket发送消息到服务器"""
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def send_message(self, message):
        """发送消息到服务器"""
        server_ip = self.config_manager.config['server_ip']
        server_port = self.config_manager.config['server_port']
        
        # 创建socket连接
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # 设置连接超时时间
            client_socket.settimeout(5)
            # 连接服务器
            client_socket.connect((server_ip, server_port))
            
            # 发送消息
            client_socket.send(message.encode('utf-8'))
            
            # 接收服务器确认
            response = client_socket.recv(1024).decode('utf-8')
            client_socket.close()
            
            return True, response
        except socket.timeout:
            return False, "连接服务器超时，请检查网络或服务器是否启动"
        except ConnectionRefusedError:
            return False, "无法连接到服务器，请检查服务器是否启动"
        except Exception as e:
            return False, f"发送消息失败: {str(e)}"
        finally:
            client_socket.close()

class NotifyClient:
    """命令行通知客户端"""
    def __init__(self):
        # 初始化配置管理器和消息发送器
        self.config_manager = ConfigManager()
        self.message_sender = MessageSender(self.config_manager)
    
    def send_message(self, message):
        """发送消息"""
        if not message:
            print("错误: 消息内容不能为空！")
            return False
        
        print(f"正在发送消息到 {self.config_manager.config['server_ip']}:{self.config_manager.config['server_port']}...")
        
        success, response = self.message_sender.send_message(message)
        
        if success:
            print("消息发送成功！")
            return True
        else:
            print(f"发送失败: {response}")
            return False
    
    def configure(self, ip=None, port=None):
        """配置服务器设置"""
        # 如果没有提供参数，显示当前配置
        if ip is None and port is None:
            print(f"当前配置:")
            print(f"  服务器IP: {self.config_manager.config['server_ip']}")
            print(f"  服务器端口: {self.config_manager.config['server_port']}")
            return True
        
        # 如果只提供了一个参数，使用当前配置的另一个参数
        if ip is None:
            ip = self.config_manager.config['server_ip']
        if port is None:
            port = self.config_manager.config['server_port']
        
        # 验证端口
        try:
            port = int(port)
            if port <= 0 or port > 65535:
                raise ValueError()
        except ValueError:
            print("错误: 端口必须是1-65535之间的整数！")
            return False
        
        # 保存配置
        if self.config_manager.save_config(ip, port):
            print(f"配置已保存: 服务器 {ip}:{port}")
            return True
        else:
            print("错误: 无法保存配置，请检查权限！")
            return False

def main():
    parser = argparse.ArgumentParser(description='NotifyPy 客户端 - 发送通知到服务器')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 发送消息命令
    send_parser = subparsers.add_parser('send', help='发送通知消息')
    send_parser.add_argument('message', help='要发送的消息内容')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置服务器设置')
    config_parser.add_argument('--ip', help='服务器IP地址')
    config_parser.add_argument('--port', type=int, help='服务器端口')
    
    # 解析参数
    args = parser.parse_args()
    
    # 创建客户端
    client = NotifyClient()
    
    # 根据命令执行操作
    if args.command == 'send':
        if client.send_message(args.message):
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.command == 'config':
        if client.configure(args.ip, args.port):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # 如果没有提供命令，显示帮助
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
