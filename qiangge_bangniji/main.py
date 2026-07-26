"""
强哥帮你记 — 程序入口。
双击运行此文件即可启动记账软件。
"""
import ttkbootstrap as ttk
import sys
import os

# 获取当前文件所在目录（即 qiangge_bangniji/），记为项目根目录
PROJECT_ROOT = os.path.dirname(__file__)
# 把项目根目录加到 Python 的搜索路径里，这样 import 时就能找到 ui/、db/ 等子目录
sys.path.insert(0, PROJECT_ROOT)

from ui.main_window import MainWindow


def main():
    """启动记账软件的主函数。

    做的事情（按顺序）：
    1. 创建一个带现代主题的窗口（ttkbootstrap 是美化版 Tkinter）
    2. 设置窗口大小为 1200×750
    3. 加载程序图标（如果有的话）
    4. 把主界面（记账表单 + 账单列表）放到窗口里
    5. 启动窗口的"事件循环"——让窗口一直显示，直到用户关闭
    """
    # ttkbootstrap 内置了多种主题，"flatly" 是扁平简洁风格
    root = ttk.Window(themename="flatly", title="强哥帮你记")
    root.geometry("1200x750")

    # 设置窗口左上角的小图标（如果 assets/icon.ico 存在的话）
    icon_path = os.path.join(PROJECT_ROOT, 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    app = MainWindow(root)
    # mainloop() 是 Tkinter 的"事件循环"——让窗口一直运行，等用户点击按钮、输入文字
    root.mainloop()


if __name__ == "__main__":
    main()
   
