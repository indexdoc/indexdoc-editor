import shutil
import time
import multiprocessing
import client_global
import signal
import socket
import webview
import logging
import psutil
import os
import client_config



def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def on_close():
    pid = os.getpid()  # 当前 Python 进程 PID
    p = psutil.Process(pid)
    try:
        tmp_path = client_config.tmp_path
        shutil.rmtree(tmp_path)
    except:
        pass
    p.send_signal(signal.SIGTERM)  # 等同于停止按钮发送的终止信号

def on_window_closing():
    """
    当窗口即将关闭时调用。
    返回 True 表示允许关闭，返回 False 表示取消关闭。
    """
    # 使用 pywebview 内置的确认对话框（完全在 Python 中）
    result = client_global.client_window.create_confirmation_dialog(
        title='⚠️ 确认退出 IndexDoc',  # 添加警告 emoji
        message='❌ 您确定要退出吗？'
    )
    if result:
        # print("用户确认退出，关闭应用。")
        return True  # 允许关闭
    else:
        # print("用户取消退出。")
        return False  # 阻止关闭

def send_status_to_parent_process(status="启动中", progress=0):
    try:
        # 如果没有传入 comm_file，则使用默认命名规则
        global comm_file
        # 主程序自身的路径
        import sys
        signal_data = {
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pid": os.getpid(),
            "process_name": "_indexdoc_win.bin",
            "status": status,
            "progress": progress
        }
        logging.debug(f"已向主进程发送状态信号: status={status}, progress={progress}")
    except Exception as e:
        logging.debug(f"发送状态信号失败: {e}")


def main():
    send_status_to_parent_process(status="开始启动", progress=0)
    multiprocessing.freeze_support()
    send_status_to_parent_process(status="启动中", progress=10)
    import client_server
    send_status_to_parent_process(status="启动中", progress=50)
    port = 8080
    client_global.web_port = port
    import threading
    # 在新线程中运行 Tornado 服务器
    server_thread = threading.Thread(target=client_server.start_tornado, args=(port, 0), daemon=True)
    server_thread.start()
    webview.settings['ALLOW_DOWNLOADS'] = True
    send_status_to_parent_process(status="启动中", progress=90)
    client_global.client_window = webview.create_window(
        'Markdown编辑器',
        url=f'http://localhost:{port}',
        width=1600,
        height=900,
        min_size=(1200, 800)
        # confirm_close=True,
        # localization={'global.quitConfirmation': '确定要退出吗?',
        #               },
    )

    # 注入自定义脚本
    def inject_scripts():
        send_status_to_parent_process(status="启动完成", progress=100)
        client_global.client_window.load_css("body { background-color: #f0f0f0; }")
    # 绑定加载完成事件
    client_global.client_window.events.closing += on_window_closing
    client_global.client_window.events.loaded += inject_scripts
    client_global.client_window.events.closed += on_close
    webview.start(debug=True)


if __name__ == "__main__":
    main()
