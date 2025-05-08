#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import time

# u5bfcu5165send.pyu4e2du7684u529fu80fd
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
from send import NotifyClient

def run_command_and_notify(command):
    """执行命令并在完成后发送通知"""
    start_time = time.time()
    
    # 打印要执行的命令
    print(f"正在执行: {command}")
    
    try:
        # 导入select模块用于非阻塞读取
        import select
        
        # 执行命令，实时显示输出
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            bufsize=1  # 行缓冲
        )
        
        # 设置非阻塞模式
        import fcntl, os
        for pipe in [process.stdout, process.stderr]:
            fd = pipe.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # 收集输出
        all_output = []
        all_error = []
        stdout_data = b''
        stderr_data = b''
        
        # 实时打印输出
        while True:
            # 使用select检查输出
            reads = [process.stdout, process.stderr]
            ret = select.select(reads, [], [], 0.1)
            
            # 处理标准输出
            for fd in ret[0]:
                if fd is process.stdout:
                    chunk = fd.read(4096)
                    if chunk:
                        stdout_data += chunk
                        # 处理完整行
                        if b'\n' in stdout_data:
                            lines = stdout_data.split(b'\n')
                            for line in lines[:-1]:
                                line_str = line.decode('utf-8', errors='replace')
                                print(line_str)
                                all_output.append(line_str + '\n')
                            stdout_data = lines[-1]
                elif fd is process.stderr:
                    chunk = fd.read(4096)
                    if chunk:
                        stderr_data += chunk
                        # 处理完整行
                        if b'\n' in stderr_data:
                            lines = stderr_data.split(b'\n')
                            for line in lines[:-1]:
                                line_str = line.decode('utf-8', errors='replace')
                                print(line_str, file=sys.stderr)
                                all_error.append(line_str + '\n')
                            stderr_data = lines[-1]
            
            # 检查进程是否结束
            if process.poll() is not None:
                # 处理剩余输出
                if stdout_data:
                    line_str = stdout_data.decode('utf-8', errors='replace')
                    if line_str:
                        print(line_str)
                        all_output.append(line_str)
                if stderr_data:
                    line_str = stderr_data.decode('utf-8', errors='replace')
                    if line_str:
                        print(line_str, file=sys.stderr)
                        all_error.append(line_str)
                break
        
        # 检查进程返回码
        return_code = process.poll()
        success = (return_code == 0)
        output = ''.join(all_output)
        error = ''.join(all_error)
    
        # 计算执行时间
        elapsed_time = time.time() - start_time
        time_str = f"{elapsed_time:.2f}秒"
        
        # 准备通知消息
        if success:
            status = "成功"
            message = f"命令已完成: {command} (用时: {time_str})"
        else:
            status = "失败"
            message = f"命令执行失败: {command} (用时: {time_str})\n错误: {error}"
    
        # 打印命令执行结果
        print(f"命令{status}执行完毕。用时: {time_str}")
        
        # 直接使用NotifyClient发送通知
        client = NotifyClient()
        
        # 打印当前服务器地址和端口
        server_ip = client.config_manager.config['server_ip']
        server_port = client.config_manager.config['server_port']
        print(f"发送通知到服务器: {server_ip}:{server_port}")
        
        client.send_message(message)
    
        # 返回原始命令的执行状态
        return success
    except Exception as e:
        print(f"执行命令时发生错误: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python notify.py <要执行的命令>")
        print("例如: python notify.py ls -la")
        sys.exit(1)
    
    # 组合命令行参数为完整命令
    command = " ".join(sys.argv[1:])
    
    # 执行命令并发送通知
    success = run_command_and_notify(command)
    
    # 返回与原始命令相同的退出状态
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
