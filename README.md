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

#### 发送消息（默认方式）
```
python send.py "这是一条测试通知消息"
```

#### 配置服务器
```
python send.py config --ip 192.168.1.100 --port 5000
```

#### 查看当前配置
```
python send.py show
```

#### 执行命令并通知
使用notify.py可以执行命令，并在命令完成后发送通知：
```
python notify.py cp -r source_dir target_dir
```

这将执行`cp -r source_dir target_dir`命令，并在命令完成后发送通知消息，包含命令执行状态和用时。

## 打包分发

### 使用PyInstaller打包

```
pyinstaller --onefile server.py
pyinstaller --onefile send.py
pyinstaller --onefile notify.py
```

生成的可执行文件将位于dist目录下。

### 打包后的使用方法

#### 服务器
```
./server
```

#### 发送消息
```
./send "这是一条测试通知消息"
```

#### 配置服务器
```
./send config --ip 192.168.1.100 --port 5000
```

#### 执行命令并通知
```
./notify cp -r source_dir target_dir
```

### 添加到PATH

为了更方便地使用这些工具，可以将它们添加到PATH环境变量中：

```
sudo cp dist/server dist/send dist/notify /usr/local/bin/
```

或者添加到用户目录：

```
mkdir -p ~/bin
cp dist/server dist/send dist/notify ~/bin/
```

确保`~/bin`在你的PATH环境变量中：

```
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```
