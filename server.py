#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import json
import os
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
import datetime

class NotificationWindow:
    """通知窗口，用于显示收到的消息"""
    def __init__(self, message, parent=None):
        self.message = message
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("新通知")
        
        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 设置窗口大小和位置（随机位置，避免窗口堆叠）
        window_width = 400
        window_height = 220
        x_position = random.randint(50, max(50, screen_width - window_width - 50))
        y_position = random.randint(50, max(50, screen_height - window_height - 50))
        
        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window.attributes("-topmost", True)  # 窗口置顶
        self.window.resizable(False, False)
        
        # 设置窗口样式
        self.setup_window()
    
    def setup_window(self):
        """设置窗口界面"""
        # 设置窗口背景色 - 使用渐变效果
        self.window.configure(bg="#2c3e50")
        
        # 创建字体
        title_font = tkfont.Font(family="Microsoft YaHei", size=13, weight="bold")
        message_font = tkfont.Font(family="Microsoft YaHei", size=11)
        time_font = tkfont.Font(family="Microsoft YaHei", size=9, slant="italic")
        
        # 顶部栏 - 更醒目的设计
        top_frame = tk.Frame(self.window, bg="#e74c3c", height=40)
        top_frame.pack(fill=tk.X)
        
        # 标题标签
        title_label = tk.Label(
            top_frame, 
            text="新通知!", 
            font=title_font,
            bg="#e74c3c", 
            fg="white",
            padx=10,
            pady=8
        )
        title_label.pack(side=tk.LEFT)
        
        # 时间标签
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_label = tk.Label(
            self.window,
            text=f"接收时间: {current_time}",
            font=time_font,
            bg="#2c3e50",
            fg="#ecf0f1",
            padx=10
        )
        time_label.pack(anchor=tk.W, pady=(10, 0))
        
        # 消息框架 - 更美观的设计
        message_frame = tk.Frame(self.window, bg="#34495e", bd=1, relief=tk.GROOVE)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 消息文本
        message_text = tk.Text(
            message_frame, 
            font=message_font,
            wrap=tk.WORD,
            width=40, 
            height=5,
            bd=0,
            bg="#ecf0f1",
            fg="#2c3e50",
            padx=8,
            pady=8
        )
        message_text.pack(fill=tk.BOTH, expand=True)
        message_text.insert(tk.END, self.message)
        message_text.config(state=tk.DISABLED)  # 设置为只读
        
        # 底部按钮框架
        button_frame = tk.Frame(self.window, bg="#2c3e50", pady=10)
        button_frame.pack(fill=tk.X)
        
        # 关闭按钮 - 更美观的设计
        close_button = tk.Button(
            button_frame, 
            text="关闭通知", 
            font=message_font,
            bg="#3498db", 
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.close
        )
        close_button.pack()
    
    def close(self):
        """关闭通知窗口"""
        self.window.destroy()

class ServerConfig:
    """服务器配置管理"""
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_config.json')
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        default_config = {
            'host': '0.0.0.0',  # 监听所有网络接口
            'port': 5000,
            'max_connections': 10
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return default_config
        
        # 如果配置文件不存在，创建一个默认配置
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """保存配置"""
        if config is not None:
            self.config = config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

class MessageReceiver:
    """消息接收模块，通过socket接收客户端消息"""
    def __init__(self, config, gui):
        self.config = config
        self.gui = gui
        self.server_socket = None
        self.is_running = False
        self.clients = []
    
    def start(self):
        """启动服务器"""
        if self.is_running:
            return False, "服务器已经在运行"
        
        try:
            # 创建socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置端口复用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 绑定地址和端口
            self.server_socket.bind((self.config.config['host'], self.config.config['port']))
            # 开始监听
            self.server_socket.listen(self.config.config['max_connections'])
            
            # 设置为运行状态
            self.is_running = True
            
            # 启动监听线程
            self.listen_thread = threading.Thread(target=self._listen_for_clients, daemon=True)
            self.listen_thread.start()
            
            return True, f"服务器已启动，监听 {self.config.config['host']}:{self.config.config['port']}"
        except Exception as e:
            return False, f"启动服务器失败: {str(e)}"
    
    def stop(self):
        """停止服务器"""
        if not self.is_running:
            return False, "服务器未运行"
        
        try:
            # 设置为非运行状态
            self.is_running = False
            
            # 关闭所有客户端连接
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            
            # 关闭服务器socket
            if self.server_socket:
                self.server_socket.close()
            
            return True, "服务器已停止"
        except Exception as e:
            return False, f"停止服务器失败: {str(e)}"
    
    def _listen_for_clients(self):
        """监听客户端连接"""
        self.gui.update_status("服务器正在监听客户端连接...")
        
        while self.is_running:
            try:
                # 接受客户端连接
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # 更新状态
                self.gui.update_status(f"接受来自 {client_address[0]}:{client_address[1]} 的连接")
                
                # 启动客户端处理线程
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
            except socket.error:
                if self.is_running:  # 只有在服务器应该运行时才报告错误
                    self.gui.update_status("监听客户端连接时出错")
                break
    
    def _handle_client(self, client_socket, client_address):
        """处理客户端消息"""
        try:
            # 接收消息
            message = client_socket.recv(4096).decode('utf-8')
            
            if message:
                # 更新状态
                status_msg = f"收到来自 {client_address[0]}:{client_address[1]} 的消息"
                self.gui.update_status(status_msg)
                self.gui.add_log_message(status_msg)
                
                # 显示通知
                self.gui.show_notification(message)
                
                # 向客户端发送确认
                client_socket.send("消息已接收".encode('utf-8'))
        except Exception as e:
            self.gui.update_status(f"处理客户端消息时出错: {str(e)}")
        finally:
            # 关闭客户端连接
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)

class ServerGUI:
    """服务器GUI界面"""
    def __init__(self, root):
        self.root = root
        self.root.title("NotifyPy 服务器")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化配置
        self.config = ServerConfig()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化消息接收器
        self.message_receiver = MessageReceiver(self.config, self)
        
        # 设置主题
        self.set_theme()
        
        # 自动启动服务器
        self.start_server()
    
    def set_theme(self):
        """设置界面主题"""
        bg_color = "#f5f5f5"
        self.root.configure(bg=bg_color)
        
        # ttk组件不支持直接设置bg属性
        # 可以通过ttk.Style设置样式
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建字体
        self.title_font = tkfont.Font(family="Microsoft YaHei", size=14, weight="bold")
        self.normal_font = tkfont.Font(family="Microsoft YaHei", size=10)
        self.log_font = tkfont.Font(family="Consolas", size=9)
        
        # 主框架
        self.frame_main = ttk.Frame(self.root, padding="10")
        self.frame_main.pack(fill=tk.BOTH, expand=True)
        
        # 标题标签
        ttk.Label(self.frame_main, text="NotifyPy 通知服务器", font=self.title_font).pack(pady=10)
        
        # 服务器控制框架
        self.frame_server = ttk.LabelFrame(self.frame_main, text="服务器控制", padding="10")
        self.frame_server.pack(fill=tk.X, pady=10)
        
        # 服务器设置
        settings_frame = ttk.Frame(self.frame_server)
        settings_frame.pack(fill=tk.X)
        
        ttk.Label(settings_frame, text="监听地址:", width=10).grid(row=0, column=0, padx=5, pady=5)
        self.host_var = tk.StringVar(value=self.config.config['host'])
        self.host_entry = ttk.Entry(settings_frame, textvariable=self.host_var, width=15)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="端口:", width=10).grid(row=0, column=2, padx=5, pady=5)
        self.port_var = tk.StringVar(value=str(self.config.config['port']))
        self.port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # 控制按钮框架
        control_frame = ttk.Frame(self.frame_server)
        control_frame.pack(fill=tk.X, pady=10)
        
        # 启动/停止按钮
        self.server_state = tk.StringVar(value="启动服务器")
        self.server_button = ttk.Button(control_frame, textvariable=self.server_state, command=self.toggle_server)
        self.server_button.pack(side=tk.LEFT, padx=5)
        
        # 保存设置按钮
        self.save_button = ttk.Button(control_frame, text="保存设置", command=self.save_settings)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # 测试通知按钮
        self.test_button = ttk.Button(control_frame, text="测试通知", command=self.test_notification)
        self.test_button.pack(side=tk.LEFT, padx=5)
        
        # 日志框架
        self.frame_log = ttk.LabelFrame(self.frame_main, text="服务器日志", padding="10")
        self.frame_log.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 日志文本框
        self.log_text = tk.Text(self.frame_log, height=15, width=70, font=self.log_font)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.frame_log, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 设置日志文本框为只读
        self.log_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def toggle_server(self):
        """切换服务器状态"""
        if self.message_receiver.is_running:
            success, message = self.message_receiver.stop()
            if success:
                self.server_state.set("启动服务器")
                self.host_entry.config(state=tk.NORMAL)
                self.port_entry.config(state=tk.NORMAL)
        else:
            success, message = self.message_receiver.start()
            if success:
                self.server_state.set("停止服务器")
                self.host_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
        
        self.update_status(message)
        self.add_log_message(message)
    
    def start_server(self):
        """启动服务器"""
        if not self.message_receiver.is_running:
            success, message = self.message_receiver.start()
            if success:
                self.server_state.set("停止服务器")
                self.host_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
            
            self.update_status(message)
            self.add_log_message(message)
    
    def save_settings(self):
        """保存服务器设置"""
        try:
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            
            # 验证端口
            if port <= 0 or port > 65535:
                raise ValueError("端口范围无效")
            
            # 更新配置
            self.config.config['host'] = host
            self.config.config['port'] = port
            
            # 保存配置
            if self.config.save_config():
                message = "设置已保存"
                messagebox.showinfo("成功", message)
            else:
                message = "保存设置失败"
                messagebox.showerror("错误", message)
            
            self.update_status(message)
            self.add_log_message(message)
        except ValueError:
            message = "端口必须是1-65535之间的整数"
            messagebox.showwarning("警告", message)
            self.update_status(message)
    
    def test_notification(self):
        """测试通知"""
        self.show_notification("这是一条测试通知消息。\n如果您看到这条消息，说明通知系统工作正常！")
        self.add_log_message("已发送测试通知")
    
    def show_notification(self, message):
        """显示通知"""
        # 创建通知窗口
        notification = NotificationWindow(message, self.root)
        
        # 记录日志
        self.add_log_message(f"显示通知: {message}")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def add_log_message(self, message):
        """添加日志消息"""
        # 启用文本框编辑
        self.log_text.config(state=tk.NORMAL)
        
        # 添加时间戳和消息
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 插入消息
        self.log_text.insert(tk.END, log_entry)
        
        # 滚动到底部
        self.log_text.see(tk.END)
        
        # 禁用文本框编辑
        self.log_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.message_receiver.is_running:
            if messagebox.askyesno("确认", "服务器正在运行，确定要退出吗？"):
                self.message_receiver.stop()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()