"""
贪吃蛇小游戏 — 内置在记账 APP 中。
纯 Tkinter Canvas 实现，零额外依赖。
"""
import tkinter as tk
import random


class Direction:
    """蛇的移动方向，用坐标偏移量表示。

    比如 (0, -1) 表示 x 不变，y 减 1，也就是"向上"。
    """
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    # 相反方向对照表：向上↔向下、向左↔向右
    # 用于防止蛇掉头撞到自己（比如正在往右走时不能立刻按左）
    _OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

    @classmethod
    def is_opposite(cls, a, b):
        """判断方向 b 是不是方向 a 的反方向。"""
        return cls._OPPOSITE.get(a) == b


class SnakeGame(tk.Frame):
    """贪吃蛇游戏组件，可直接嵌入任意容器"""

    CELL_SIZE = 25
    COLS = 30
    ROWS = 22

    BG_COLOR = '#1a1a2e'
    GRID_COLOR = '#16213e'
    SNAKE_COLOR = '#00d2ff'
    SNAKE_HEAD_COLOR = '#00ffff'
    FOOD_COLOR = '#ff6b6b'
    FOOD_GLOW = '#ff4444'

    # 游戏状态常量（替代双布尔 _running/_paused）
    STATE_IDLE = 'idle'
    STATE_PLAYING = 'playing'
    STATE_PAUSED = 'paused'

    def __init__(self, parent, on_back=None, **kw):
        """初始化游戏组件。

        参数：
            parent: 父容器（一般是右侧面板）
            on_back: 点击"返回记账"时的回调函数
        """
        super().__init__(parent, **kw)
        self._on_back = on_back
        self._after_id = None          # 定时器的 ID，用于控制蛇的移动速度
        self._state = self.STATE_IDLE  # 当前游戏状态：空闲/进行中/暂停
        self._snake = []               # 蛇的身体，列表里每个元素是 (x, y) 坐标
        self._food = None              # 食物坐标
        self._direction = Direction.RIGHT  # 当前移动方向
        self._next_dir = Direction.RIGHT   # 下一帧要切换的方向（缓存按键）
        self._score = 0                # 当前分数
        self._speed = 120              # 移动间隔（毫秒），越小越快
        self._keys_bound = False       # 键盘事件是否已绑定

        self._build_ui()

    # ================================================================
    # 界面构建
    # ================================================================

    def _build_ui(self):
        """构建游戏界面：顶部信息栏 + 画布 + 底部按钮 + 按键提示。"""
        # 顶栏：返回按钮、游戏标题、分数、最高分
        bar = tk.Frame(self, bg=self.BG_COLOR)
        bar.pack(fill=tk.X, pady=(0, 5))

        if self._on_back:
            tk.Button(
                bar, text="📋 返回记账", font=('Microsoft YaHei', 9),
                bg='#0f3460', fg='white', relief=tk.FLAT, padx=12,
                command=self._on_back
            ).pack(side=tk.LEFT)

        tk.Label(
            bar, text="🐍 贪吃蛇", font=('Microsoft YaHei', 16, 'bold'),
            bg=self.BG_COLOR, fg='white'
        ).pack(side=tk.LEFT, padx=(20, 30))

        self._score_label = tk.Label(
            bar, text="🏆 分数: 0", font=('Microsoft YaHei', 13, 'bold'),
            bg=self.BG_COLOR, fg='#F1C40F'
        )
        self._score_label.pack(side=tk.LEFT)

        self._best_label = tk.Label(
            bar, text="👑 最高: 0", font=('Microsoft YaHei', 11),
            bg=self.BG_COLOR, fg='#95A5A6'
        )
        self._best_label.pack(side=tk.LEFT, padx=(20, 0))

        # 画布
        w = self.COLS * self.CELL_SIZE
        h = self.ROWS * self.CELL_SIZE
        self._canvas = tk.Canvas(
            self, width=w, height=h, bg=self.BG_COLOR,
            highlightthickness=1, highlightbackground='#0f3460',
            takefocus=True
        )
        self._canvas.pack(pady=(0, 8))

        self._draw_grid()

        # 按钮区
        btn_frame = tk.Frame(self, bg=self.BG_COLOR)
        btn_frame.pack(pady=(0, 8))

        self._start_btn = tk.Button(
            btn_frame, text="▶ 开始游戏", font=('Microsoft YaHei', 10),
            bg='#27AE60', fg='white', width=12, relief=tk.FLAT,
            command=self.start
        )
        self._start_btn.pack(side=tk.LEFT, padx=5)

        self._pause_btn = tk.Button(
            btn_frame, text="⏸ 暂停", font=('Microsoft YaHei', 10),
            bg='#F39C12', fg='white', width=10, relief=tk.FLAT,
            command=self.toggle_pause, state=tk.DISABLED
        )
        self._pause_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="🔄 重新开始", font=('Microsoft YaHei', 10),
            bg='#E74C3C', fg='white', width=12, relief=tk.FLAT,
            command=self.restart
        ).pack(side=tk.LEFT, padx=5)

        # 按键提示
        tk.Label(
            self, text="⌨  方向键 ↑↓←→  或  WASD  控制蛇的方向  ·  空格键 开始/暂停",
            font=('Microsoft YaHei', 8), fg='#555555', bg=self.BG_COLOR
        ).pack(pady=(0, 10))

        self._draw_welcome()

    def _draw_grid(self):
        """绘制固定网格线（只创建一次，不随游戏重置而销毁）"""
        w = self.COLS * self.CELL_SIZE
        h = self.ROWS * self.CELL_SIZE
        for x in range(0, w, self.CELL_SIZE):
            self._canvas.create_line(x, 0, x, h, fill=self.GRID_COLOR, width=1, tags='grid')
        for y in range(0, h, self.CELL_SIZE):
            self._canvas.create_line(0, y, w, y, fill=self.GRID_COLOR, width=1, tags='grid')

    def _draw_welcome(self):
        """在画布中央显示欢迎文字（游戏开始前/重新开始时显示）。"""
        cx = self.COLS * self.CELL_SIZE // 2
        cy = self.ROWS * self.CELL_SIZE // 2
        self._canvas.create_text(
            cx, cy, text="按「开始游戏」或 空格键 开始",
            fill='#555555', font=('Microsoft YaHei', 15),
            tags='overlay'
        )

    # ================================================================
    # 按键管理
    # ================================================================

    def _bind_keys(self):
        """绑定键盘事件到 Canvas（局部绑定，不干扰其他窗口）"""
        if self._keys_bound:
            return

        arrows = [
            ('<Up>', Direction.UP), ('<Down>', Direction.DOWN),
            ('<Left>', Direction.LEFT), ('<Right>', Direction.RIGHT),
        ]
        for key, d in arrows:
            self._canvas.bind(key, lambda e, d=d: self._change_dir(d))
        # WASD + 大写
        for prefix, d in [('w', Direction.UP), ('s', Direction.DOWN),
                          ('a', Direction.LEFT), ('d', Direction.RIGHT)]:
            self._canvas.bind(f'<{prefix}>', lambda e, d=d: self._change_dir(d))
            self._canvas.bind(f'<{prefix.upper()}>', lambda e, d=d: self._change_dir(d))
        # 空格
        self._canvas.bind('<space>', lambda e: self._on_space())

        self._keys_bound = True

    def _unbind_keys(self):
        """解绑所有键盘事件"""
        if not self._keys_bound:
            return
        for key in ['<Up>', '<Down>', '<Left>', '<Right>',
                    '<w>', '<W>', '<s>', '<S>', '<a>', '<A>', '<d>', '<D>',
                    '<space>']:
            self._canvas.unbind(key)
        self._keys_bound = False

    def _change_dir(self, new_dir):
        """处理方向键输入：切换蛇的移动方向（不能掉头）。"""
        if self._state != self.STATE_PLAYING:
            return
        # 不能往反方向走（比如正在往右时不能突然往左，会撞到自己）
        if not Direction.is_opposite(new_dir, self._direction):
            self._next_dir = new_dir

    def _on_space(self):
        """空格键：游戏中则暂停，暂停/空闲则开始。"""
        if self._state == self.STATE_PLAYING:
            self.toggle_pause()
        else:
            self.start()

    # ================================================================
    # 游戏逻辑
    # ================================================================

    def start(self):
        """开始 / 继续游戏"""
        if self._state == self.STATE_PLAYING:
            return

        if self._state == self.STATE_IDLE:
            self._init_game()

        if self._state == self.STATE_PAUSED:
            self._canvas.delete('pause_overlay')

        self._state = self.STATE_PLAYING
        self._start_btn.config(state=tk.DISABLED)
        self._pause_btn.config(state=tk.NORMAL, text="⏸ 暂停")
        self._canvas.focus_set()
        self._tick()

    def _init_game(self):
        """初始化游戏数据：重置分数、蛇的位置、速度，生成第一个食物。"""
        self._score = 0
        self._score_label.config(text="🏆 分数: 0")
        self._direction = Direction.RIGHT
        self._next_dir = Direction.RIGHT
        self._speed = 120

        # 蛇初始位置在画布中央，头朝右，身体 3 格长
        sx = self.COLS // 2  # 画布中央 x 坐标
        sy = self.ROWS // 2  # 画布中央 y 坐标
        self._snake = [(sx, sy), (sx - 1, sy), (sx - 2, sy)]

        self._spawn_food()
        self._draw_snake()

    def _spawn_food(self):
        """在空白位置随机生成一个食物。"""
        while True:
            fx = random.randint(0, self.COLS - 1)
            fy = random.randint(0, self.ROWS - 1)
            # 确保食物不落在蛇身上
            if (fx, fy) not in self._snake:
                self._food = (fx, fy)
                break

    def _draw_snake(self):
        """在画布上绘制蛇和食物（每帧调用，先清除旧的再画新的）。"""
        self._canvas.delete('snake', 'food', 'overlay', 'pause_overlay')

        for i, (sx, sy) in enumerate(self._snake):
            x1 = sx * self.CELL_SIZE + 2
            y1 = sy * self.CELL_SIZE + 2
            x2 = x1 + self.CELL_SIZE - 4
            y2 = y1 + self.CELL_SIZE - 4
            fill = self.SNAKE_HEAD_COLOR if i == 0 else self.SNAKE_COLOR
            self._canvas.create_rectangle(
                x1, y1, x2, y2, fill=fill, outline='', tags='snake'
            )

        if self._food:
            fx, fy = self._food
            cx = fx * self.CELL_SIZE + self.CELL_SIZE // 2
            cy = fy * self.CELL_SIZE + self.CELL_SIZE // 2
            r = self.CELL_SIZE // 2 - 3
            self._canvas.create_oval(
                cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3,
                fill=self.FOOD_GLOW, outline='', tags='food'
            )
            self._canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=self.FOOD_COLOR, outline='', tags='food'
            )

    def _tick(self):
        """游戏的"心跳"——每隔 _speed 毫秒执行一次，推动蛇前进一格。

        每帧做的事：
        1. 把蛇头按当前方向移动一格
        2. 检查是否撞墙或撞到自己（→游戏结束）
        3. 如果吃到食物：加分 + 蛇变长 + 生成新食物 + 加速
        4. 没吃到食物：移除蛇尾（保持长度不变，模拟前进）
        5. 重绘画布，然后调度下一帧
        """
        if self._state != self.STATE_PLAYING:
            return

        self._direction = self._next_dir

        hx, hy = self._snake[0]        # 当前蛇头坐标
        dx, dy = self._direction       # 移动方向
        new_head = (hx + dx, hy + dy)  # 新蛇头坐标

        # 撞墙检测：超出画布边界
        nx, ny = new_head
        if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
            self._game_over()
            return
        # 撞自己检测：新蛇头跟身体某段重合
        if new_head in self._snake:
            self._game_over()
            return

        self._snake.insert(0, new_head)  # 在头部插入新位置

        if new_head == self._food:
            # 吃到食物！加分、生成新食物、稍微加速
            self._score += 10
            self._score_label.config(text=f"🏆 分数: {self._score}")
            self._spawn_food()
            if self._speed > 50:     # 最快不超过 50ms 一帧
                self._speed -= 2     # 每吃一个食物，间隔缩短 2ms
        else:
            # 没吃到食物：去掉尾部，保持蛇的长度不变
            self._snake.pop()

        self._draw_snake()
        # after() 是 Tkinter 的定时器，"self._speed 毫秒后再调一次 _tick"
        self._after_id = self.after(self._speed, self._tick)

    def _game_over(self):
        """游戏结束：停止移动，更新最高分，显示结束画面。"""
        self._state = self.STATE_IDLE
        if self._after_id:
            self.after_cancel(self._after_id)  # 取消定时器，蛇不再移动
            self._after_id = None

        # 更新最高分（存储在类变量 _best_score 中，所有游戏共享）
        best = getattr(SnakeGame, '_best_score', 0)
        if self._score > best:
            SnakeGame._best_score = self._score
        self._best_label.config(text=f"👑 最高: {SnakeGame._best_score}")

        # 半透明遮罩 + 结束提示（按键保持绑定，空格可以重新开始）
        self._canvas.create_rectangle(
            2, 2, self.COLS * self.CELL_SIZE - 2, self.ROWS * self.CELL_SIZE - 2,
            fill=self.BG_COLOR, stipple='gray25', outline='', tags='overlay'
        )
        cx = self.COLS * self.CELL_SIZE // 2
        cy = self.ROWS * self.CELL_SIZE // 2
        self._canvas.create_text(
            cx, cy - 25, text="💀 游戏结束",
            fill='#ff6b6b', font=('Microsoft YaHei', 22, 'bold'), tags='overlay'
        )
        self._canvas.create_text(
            cx, cy + 15, text=f"得分: {self._score}",
            fill='white', font=('Microsoft YaHei', 15), tags='overlay'
        )
        self._canvas.create_text(
            cx, cy + 50, text="空格键 或 点击按钮 重新开始",
            fill='#888888', font=('Microsoft YaHei', 11), tags='overlay'
        )

        self._start_btn.config(state=tk.NORMAL)
        self._pause_btn.config(state=tk.DISABLED)

    def toggle_pause(self):
        """切换暂停/继续状态。"""
        if self._state != self.STATE_PLAYING and self._state != self.STATE_PAUSED:
            return

        if self._state == self.STATE_PLAYING:
            # 暂停：取消定时器，显示"暂停中"遮罩
            self._state = self.STATE_PAUSED
            self._pause_btn.config(text="▶ 继续")
            if self._after_id:
                self.after_cancel(self._after_id)
                self._after_id = None
            cx = self.COLS * self.CELL_SIZE // 2
            cy = self.ROWS * self.CELL_SIZE // 2
            self._canvas.create_text(
                cx, cy, text="⏸ 暂停中",
                fill='white', font=('Microsoft YaHei', 22, 'bold'),
                tags='pause_overlay'
            )
        else:
            # 继续：清除遮罩，恢复定时器
            self._start_btn.config(state=tk.DISABLED)
            self._pause_btn.config(text="⏸ 暂停")
            self._canvas.delete('pause_overlay')
            self._state = self.STATE_PLAYING
            self._tick()

    def restart(self):
        """重新开始游戏：清除所有状态，回到欢迎画面。"""
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._state = self.STATE_IDLE
        # 只清除蛇、食物、遮罩，不动网格线
        self._canvas.delete('snake', 'food', 'overlay', 'pause_overlay')
        self._draw_welcome()
        self._start_btn.config(state=tk.NORMAL)
        self._pause_btn.config(state=tk.DISABLED)
        self._score_label.config(text="🏆 分数: 0")
        self._canvas.focus_set()

    # ================================================================
    # 生命周期
    # ================================================================

    def activate(self):
        """切换到游戏界面时调用：绑定按键，聚焦画布"""
        self._bind_keys()
        self._canvas.focus_set()

    def deactivate(self):
        """离开游戏界面时调用：停止游戏，解绑按键"""
        self._unbind_keys()
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._state = self.STATE_IDLE
