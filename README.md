# NotifyPy 通知系统

这是一个基于Python的通知系统，包含客户端和服务器两部分。

## 功能特点

### 客户端
- 命令行工具，方便集成到脚本中
- 配置服务器IP和端口并保存到~/.config目录
- 发送简单文本消息至服务器

### 服务器
- 接收来自客户端的消息
- 弹出美观的GUI通知窗口
- 支持声音提醒
- 可处理多个客户端的消息

## 安装依赖

```
pip install -r requirements.txt
```

## 使用方法

### 启动服务器
```
python server.py
```

### 客户端使用

#### 配置服务器
```
python client.py config --ip 192.168.1.100 --port 5000
```

#### 查看当前配置
```
python client.py config
```

#### 发送消息
```
python client.py send "这是一条测试通知消息"
```

## 打包分发

使用PyInstaller打包为可执行文件：

```
pyinstaller --onefile server.py
pyinstaller --onefile client.py
```

生成的可执行文件将位于dist目录下。
