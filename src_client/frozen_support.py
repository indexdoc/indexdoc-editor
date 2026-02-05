import logging
import shutil
import sys
import os
import re
import ctypes

def is_frozen():
    """判断是否是打包后的 EXE 运行"""
    return getattr(sys, 'frozen', False)

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if is_frozen():
        # 打包后：资源在 sys._MEIPASS 中（PyInstaller 创建的临时文件夹）
        base_path = sys._MEIPASS
        _temp_str = re.sub(r'^(\.\./|\.\.\\)+', '', relative_path) #去掉相对路径
        return os.path.normpath(os.path.join(base_path, _temp_str))
    else:
        # 直接运行 .py：资源在源代码目录中
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(base_path, relative_path))

def get_tmp_path():
    if is_frozen():
        # 打包后：资源在 sys._MEIPASS 中（PyInstaller 创建的临时文件夹）
        base_path = sys._MEIPASS
        tmp_path = os.path.normpath(base_path + '/../tmp')
    else:
        # 直接运行 .py：资源在源代码目录中
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取上一级目录路径
        tmp_path= os.path.normpath(base_path + '/tmp')
    if not os.path.isdir(tmp_path):
        os.mkdir(tmp_path)
    return tmp_path

def get_base_path():
    if is_frozen():
        # 打包后：资源在 sys._MEIPASS 中（PyInstaller 创建的临时文件夹）
        base_path = sys._MEIPASS
        return os.path.normpath(base_path)
    else:
        # 直接运行 .py：资源在源代码目录中
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取上一级目录路径
        return os.path.normpath(base_path)

def get_update_work_path():
    if is_frozen():
        update_work_path = get_tmp_path() + '/update_work'
        return os.path.normpath(update_work_path)
    else:
        update_work_path = get_base_path() + '/tmp/indexdoc_win/tmp/update_work'
        return os.path.normpath(update_work_path)

def get_updater_path():
    if is_frozen():
        return os.path.normpath(get_tmp_path() + '/update_work/unpacked/_internal/updater.exe')
    else:
        return os.path.normpath(get_base_path() + '/tmp/indexdoc_win/_internal/updater.exe')

def get_vector_model_path():
    if is_frozen():
        # 打包后：资源在 sys._MEIPASS 中（PyInstaller 创建的临时文件夹）
        return os.path.normpath(f'{get_base_path()}/lib/model/BAAI/bge-small-zh-v1.5')
    else:
        return os.path.normpath(f'{get_base_path()}/lib/model/BAAI/bge-small-zh-v1.5')

def get_antiword_path():
    if is_frozen():
        # 打包后：资源在 sys._MEIPASS 中（PyInstaller 创建的临时文件夹）
        return os.path.normpath(f'{get_base_path()}/lib/model/antiword/bin64')
    else:
        return os.path.normpath(f'{get_base_path()}/lib/model/antiword/bin64')

def anti_debug():
    if not is_frozen():
        return
    #
    if sys.gettrace() or  \
        (hasattr(ctypes.windll.kernel32, 'IsDebuggerPresent') and ctypes.windll.kernel32.IsDebuggerPresent()) or \
        os.environ.get('PYDEVD_DISABLE_FILE_VALIDATION'):
        sys.exit("调试器被禁止")

import sys
import os

import subprocess
def unblock_files():
    try:
        if sys.platform == 'win32':
            # PowerShell 解除锁定
            subprocess.run([
                'powershell', '-Command',
                'Get-ChildItem . -Recurse | Unblock-File'
            ], check=False, capture_output=True)
    except Exception:
        pass  # 忽略错误，继续运行

def is_file_blocked(file_path):
    try:
        import pathlib
        file_path = pathlib.Path(file_path)
        if file_path.exists():
            # 尝试读取 Zone.Identifier 流
            zone_file = file_path.with_name(file_path.name + ':Zone.Identifier')
            if zone_file.exists():
                return True
    except Exception:
        pass

    return False

