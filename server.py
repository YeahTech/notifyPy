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

# u5bfcu5165Pushbulletu5e93
try:
    from pushbullet import Pushbullet
    PUSHBULLET_AVAILABLE = True
except ImportError:
    PUSHBULLET_AVAILABLE = False
    print("Pushbullet library not available. Mobile notifications will be disabled.")


class NotificationWindow:
    """Notification window to display received messages"""
    def __init__(self, message, parent=None):
        self.message = message
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("New Notification")
        
        # Get screen size
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Set window size and position (random position to avoid stacking)
        window_width = 400
        window_height = 220
        x_position = random.randint(50, max(50, screen_width - window_width - 50))
        y_position = random.randint(50, max(50, screen_height - window_height - 50))
        
        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window.attributes("-topmost", True)  # Keep window on top
        self.window.resizable(False, False)
        
        # Set window style
        self.setup_window()
    
    def setup_window(self):
        """Set up window interface"""
        # Set window background color
        self.window.configure(bg="#2c3e50")
        
        # Create fonts
        title_font = tkfont.Font(family="Arial", size=13, weight="bold")
        message_font = tkfont.Font(family="Arial", size=11)
        time_font = tkfont.Font(family="Arial", size=9, slant="italic")
        
        # Top bar - eye-catching design
        top_frame = tk.Frame(self.window, bg="#e74c3c", height=40)
        top_frame.pack(fill=tk.X)
        
        # Title label
        title_label = tk.Label(
            top_frame, 
            text="New Notification!", 
            font=title_font,
            bg="#e74c3c", 
            fg="white",
            padx=10,
            pady=8
        )
        title_label.pack(side=tk.LEFT)
        
        # Time label
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_label = tk.Label(
            self.window,
            text=f"Received: {current_time}",
            font=time_font,
            bg="#2c3e50",
            fg="#ecf0f1",
            padx=10
        )
        time_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Message frame - improved design
        message_frame = tk.Frame(self.window, bg="#34495e", bd=1, relief=tk.GROOVE)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Message text
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
        message_text.config(state=tk.DISABLED)  # Set to read-only
        
        # Bottom button frame
        button_frame = tk.Frame(self.window, bg="#2c3e50", pady=10)
        button_frame.pack(fill=tk.X)
        
        # Close button - improved design
        close_button = tk.Button(
            button_frame, 
            text="Close Notification", 
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
        """Close notification window"""
        self.window.destroy()

class ServerConfig:
    """Server configuration management"""
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_config.json')
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration"""
        default_config = {
            'host': '0.0.0.0',  # Listen on all network interfaces
            'port': 5000,
            'max_connections': 10,
            'pushbullet_token': ''  # Pushbullet access token, empty by default
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # 确保所有默认配置项都存在
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                        
                return loaded_config
            except Exception as e:
                print(f"Failed to load config file: {e}")
                return default_config
        
        # If config file doesn't exist, create a default one
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """Save configuration"""
        if config is not None:
            self.config = config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save config file: {e}")
            return False

class MessageReceiver:
    """Message receiving module, receives client messages via socket"""
    def __init__(self, config, gui):
        self.config = config
        self.gui = gui
        self.server_socket = None
        self.is_running = False
        self.clients = []
    
    def start(self):
        """Start server"""
        if self.is_running:
            return False, "Server is already running"
        
        try:
            # Wait a short time to ensure previous socket is fully closed
            time.sleep(0.5)
            
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set socket options to reuse address and port
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # On some platforms, SO_REUSEPORT might be needed as well (if available)
            # This is not available on all systems, so we use try/except
            try:
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                # SO_REUSEPORT not available on this platform
                pass
                
            # Set socket timeout to avoid blocking indefinitely
            self.server_socket.settimeout(1.0)
            
            # Bind address and port
            self.server_socket.bind((self.config.config['host'], self.config.config['port']))
            
            # Start listening
            self.server_socket.listen(self.config.config['max_connections'])
            
            # Set running state
            self.is_running = True
            
            # Start listening thread
            self.listen_thread = threading.Thread(target=self._listen_for_clients, daemon=True)
            self.listen_thread.start()
            
            return True, f"Server started, listening on {self.config.config['host']}:{self.config.config['port']}"
        except Exception as e:
            return False, f"Failed to start server: {str(e)}"
    
    def stop(self):
        """Stop server"""
        if not self.is_running:
            return False, "Server is not running"
        
        try:
            # Set to not running state first to stop accept loop
            self.is_running = False
            
            # Close all client connections
            clients_copy = self.clients.copy()  # Create a copy to avoid modification during iteration
            for client in clients_copy:
                try:
                    client.close()
                except Exception as e:
                    print(f"Error closing client connection: {e}")
            
            # Clear clients list
            self.clients.clear()
            
            # Close server socket
            if self.server_socket:
                try:
                    # Shutdown socket to release it immediately
                    self.server_socket.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    # Socket might not be connected
                    print(f"Socket shutdown error (can be ignored): {e}")
                
                # Close the socket
                self.server_socket.close()
                self.server_socket = None  # Clear the socket to allow for restart
            
            # Wait a moment to ensure socket is fully released
            time.sleep(0.5)
            
            return True, "Server stopped"
        except Exception as e:
            return False, f"Failed to stop server: {str(e)}"
    
    def _listen_for_clients(self):
        """Listen for client connections"""
        self.gui.update_status("Server is listening for client connections...")
        
        while self.is_running:
            try:
                # Accept client connection with timeout
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # Update status
                self.gui.update_status(f"Accepted connection from {client_address[0]}:{client_address[1]}")
                
                # Start client handling thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                # This is expected due to the socket timeout we set
                # Just continue the loop to check if we should still be running
                continue
            except socket.error as e:
                if self.is_running:  # Only report error if server should be running
                    self.gui.update_status(f"Error listening for client connections: {e}")
                break
            except Exception as e:
                if self.is_running:
                    self.gui.update_status(f"Unexpected error in listener: {e}")
                break
    
    def _handle_client(self, client_socket, client_address):
        """Handle client messages"""
        try:
            # Receive message
            message = client_socket.recv(4096).decode('utf-8')
            
            if message:
                # Update status
                status_msg = f"Received message from {client_address[0]}:{client_address[1]}"
                self.gui.update_status(status_msg)
                self.gui.add_log_message(status_msg)
                
                # Show notification
                self.gui.show_notification(message)
                
                # Send confirmation to client
                client_socket.send("Message received".encode('utf-8'))
        except Exception as e:
            self.gui.update_status(f"Error handling client message: {str(e)}")
        finally:
            # Close client connection
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)

class ServerGUI:
    """Server GUI Interface"""
    def __init__(self, root):
        self.root = root
        self.root.title("NotifyPy Server")
        self.root.geometry("700x550")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set window icon (if available)
        # self.root.iconbitmap("icon.ico")
        
        # Initialize configuration
        self.config = ServerConfig()
        
        # Create styles
        self.create_styles()
        
        # Create interface
        self.create_widgets()
        
        # Initialize message receiver
        self.message_receiver = MessageReceiver(self.config, self)
        
        # Auto-start server
        self.start_server()
    
    def create_styles(self):
        """Create custom styles"""
        # Create fonts
        self.title_font = tkfont.Font(family="Arial", size=16, weight="bold")
        self.header_font = tkfont.Font(family="Arial", size=12, weight="bold")
        self.normal_font = tkfont.Font(family="Arial", size=10)
        self.log_font = tkfont.Font(family="Courier", size=9)
        
        # Create ttk style
        self.style = ttk.Style()
        
        # Configure theme colors
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabelframe", background="#f0f0f0")
        self.style.configure("TLabelframe.Label", background="#f0f0f0")
        
        # Button styles
        self.style.configure("TButton", padding=5)
        self.style.configure("Start.TButton", background="#4CAF50", foreground="white")
        self.style.configure("Stop.TButton", background="#f44336", foreground="white")
        self.style.configure("Action.TButton", background="#2196F3", foreground="white")
        
        # Label styles
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("Title.TLabel", foreground="#2c3e50", padding=10)
        
        # Set window background color
        self.root.configure(background="#f0f0f0")
    
    def create_widgets(self):
        """Create interface components"""
        # Main container
        main_container = ttk.Frame(self.root, padding=(20, 10, 20, 10))
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Use native tk.Label instead of ttk.Label to avoid font issues
        title_label = tk.Label(
            title_frame, 
            text="NotifyPy Server", 
            font=self.title_font,
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_indicator = tk.Canvas(title_frame, width=15, height=15, bg="#f0f0f0", highlightthickness=0)
        self.status_indicator.pack(side=tk.RIGHT, padx=5)
        self.status_indicator.create_oval(2, 2, 13, 13, fill="#cccccc", outline="")
        
        # Server control panel
        control_frame = ttk.LabelFrame(main_container, text="Server Control", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Server settings
        settings_frame = ttk.Frame(control_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid layout
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # IP settings
        ttk.Label(settings_frame, text="Listen Address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.host_var = tk.StringVar(value=self.config.config['host'])
        host_entry = ttk.Entry(settings_frame, textvariable=self.host_var, width=15)
        host_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Port settings
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(15, 5), pady=5)
        self.port_var = tk.StringVar(value=str(self.config.config['port']))
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=8)
        port_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Pushbullet settings
        ttk.Label(settings_frame, text="Pushbullet Token:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.pushbullet_token_var = tk.StringVar(value=self.config.config.get('pushbullet_token', ''))
        pushbullet_entry = ttk.Entry(settings_frame, textvariable=self.pushbullet_token_var, width=40)
        pushbullet_entry.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        
        # Pushbullet status
        pushbullet_status = "Available" if PUSHBULLET_AVAILABLE else "Not Available"
        ttk.Label(settings_frame, text=f"Pushbullet Status: {pushbullet_status}").grid(row=2, column=0, columnspan=4, sticky=tk.W, padx=0, pady=5)
        
        # Button area
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Start/stop button
        self.server_state = tk.StringVar(value="Start Server")
        self.server_button = ttk.Button(
            button_frame, 
            textvariable=self.server_state, 
            command=self.toggle_server,
            width=15
        )
        self.server_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save settings button
        save_button = ttk.Button(
            button_frame, 
            text="Save Settings", 
            command=self.save_settings,
            width=15
        )
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test notification button
        test_button = ttk.Button(
            button_frame, 
            text="Send Test Notification", 
            command=self.test_notification,
            width=15
        )
        test_button.pack(side=tk.LEFT)
        
        # Log area
        log_frame = ttk.LabelFrame(main_container, text="Server Log", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text box
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_container, 
            font=self.log_font, 
            bg="#ffffff", 
            fg="#333333",
            wrap=tk.WORD,
            borderwidth=1,
            relief=tk.SOLID
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Set log text box to read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Status bar
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            anchor=tk.W, 
            padding=(5, 2)
        )
        status_label.pack(fill=tk.X)
        
        # Save references for later use
        self.host_entry = host_entry
        self.port_entry = port_entry
    
    def toggle_server(self):
        """Toggle server state"""
        if self.message_receiver.is_running:
            success, message = self.message_receiver.stop()
            if success:
                self.server_state.set("Start Server")
                self.host_entry.config(state=tk.NORMAL)
                self.port_entry.config(state=tk.NORMAL)
                self.status_indicator.itemconfig(1, fill="#cccccc")  # Gray indicates stopped
                self.server_button.configure(style="TButton")
            else:
                messagebox.showerror("Error", message)
        else:
            success, message = self.message_receiver.start()
            if success:
                self.server_state.set("Stop Server")
                self.host_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
                self.status_indicator.itemconfig(1, fill="#4CAF50")  # Green indicates running
                self.server_button.configure(style="TButton")
            else:
                messagebox.showerror("Error", message)
        
        self.update_status(message)
        self.add_log_message(message)
    
    def start_server(self):
        """Start server"""
        if not self.message_receiver.is_running:
            success, message = self.message_receiver.start()
            if success:
                self.server_state.set("Stop Server")
                self.host_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
                self.status_indicator.itemconfig(1, fill="#4CAF50")  # Green indicates running
            else:
                messagebox.showerror("Error", message)
            
            self.update_status(message)
            self.add_log_message(message)
    
    def save_settings(self):
        """Save server settings"""
        try:
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            pushbullet_token = self.pushbullet_token_var.get().strip()
            
            # Validate port
            if port <= 0 or port > 65535:
                raise ValueError("Invalid port range")
            
            # Update configuration
            self.config.config['host'] = host
            self.config.config['port'] = port
            self.config.config['pushbullet_token'] = pushbullet_token
            
            # Test Pushbullet token if provided
            if pushbullet_token and PUSHBULLET_AVAILABLE:
                try:
                    pb = Pushbullet(pushbullet_token)
                    # Get user info to verify token
                    user = pb.user_info
                    self.add_log_message(f"Pushbullet connected: {user['name']} ({user['email']})")
                except Exception as e:
                    message = f"Pushbullet token error: {str(e)}"
                    messagebox.showwarning("Pushbullet Warning", message)
                    self.add_log_message(message)
            
            # Save configuration
            if self.config.save_config():
                message = "Settings saved"
                messagebox.showinfo("Success", message)
                
                # Send test notification if Pushbullet is configured
                if pushbullet_token and PUSHBULLET_AVAILABLE:
                    self.add_log_message("Sending test Pushbullet notification...")
                    self.send_pushbullet_notification("这是一条测试通知。如果你收到这条消息，说明Pushbullet配置正确！")
            else:
                message = "Failed to save settings"
                messagebox.showerror("Error", message)
            
            self.update_status(message)
            self.add_log_message(message)
        except ValueError:
            message = "Port must be an integer between 1-65535"
            messagebox.showwarning("Warning", message)
            self.update_status(message)
    
    def test_notification(self):
        """Test notification"""
        self.show_notification("This is a test notification message.\nIf you can see this message, the notification system is working properly!")
        self.add_log_message("Test notification sent")
    
    def show_notification(self, message):
        """Show notification"""
        # Create notification window
        notification = NotificationWindow(message, self.root)
        
        # Send Pushbullet notification if configured
        self.send_pushbullet_notification(message)
        
        # Log
        self.add_log_message(f"Showing notification: {message}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
    
    def send_pushbullet_notification(self, message):
        """Send notification to Pushbullet"""
        # Check if Pushbullet is available and token is configured
        token = self.config.config.get('pushbullet_token', '')
        if not token:
            self.add_log_message("Pushbullet通知未发送：未配置Token")
            return False
        
        if not PUSHBULLET_AVAILABLE:
            self.add_log_message("Pushbullet通知未发送：库不可用，请安装pushbullet.py")
            return False
        
        self.add_log_message("正在尝试发送Pushbullet通知...")
        
        try:
            # Create Pushbullet instance
            pb = Pushbullet(token)
            
            # Get devices (for debugging)
            devices = pb.devices
            device_info = []
            for device in devices:
                if hasattr(device, 'nickname') and device.nickname:
                    device_info.append(f"{device.nickname} ({device.device_iden})")
            
            if device_info:
                self.add_log_message(f"找到Pushbullet设备: {', '.join(device_info)}")
            else:
                self.add_log_message("未找到Pushbullet设备，但仍将尝试发送通知")
            
            # Send notification
            push = pb.push_note("NotifyPy通知", message)
            
            # Log success with more details
            push_id = push.get('iden', 'Unknown ID')
            self.add_log_message(f"Pushbullet通知发送成功: {push_id}")
            
            # Try to get push status
            try:
                pushes = pb.get_pushes(limit=1)
                if pushes and len(pushes) > 0:
                    latest = pushes[0]
                    self.add_log_message(f"最新推送状态: {latest.get('status', '未知')}")
            except Exception as e2:
                self.add_log_message(f"无法获取推送状态: {str(e2)}")
            
            return True
        except Exception as e:
            # Log detailed error
            error_msg = f"发送Pushbullet通知失败: {str(e)}"
            self.add_log_message(error_msg)
            
            # Show warning to user
            messagebox.showwarning("Pushbullet警告", "发送移动通知失败。请检查日志了解详情。")
            return False
    
    def add_log_message(self, message):
        """Add log message"""
        # Enable text box editing
        self.log_text.config(state=tk.NORMAL)
        
        # Add timestamp and message
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Insert message
        self.log_text.insert(tk.END, log_entry)
        
        # Scroll to bottom
        self.log_text.see(tk.END)
        
        # Disable text box editing
        self.log_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle window closing"""
        if self.message_receiver.is_running:
            if messagebox.askyesno("Confirm", "Server is running. Are you sure you want to exit?"):
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