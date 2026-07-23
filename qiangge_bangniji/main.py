"""
强哥帮你记 — 程序入口
双击运行此文件即可启动记账软件。
"""
import ttkbootstrap as ttk
import sys
import os

PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)

from ui.main_window import MainWindow


def main():
    # 使用 ttkbootstrap 的现代主题
    root = ttk.Window(themename="flatly", title="强哥帮你记")
    root.geometry("1200x750")

    # 设置窗口图标
    icon_path = os.path.join(PROJECT_ROOT, 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
   
