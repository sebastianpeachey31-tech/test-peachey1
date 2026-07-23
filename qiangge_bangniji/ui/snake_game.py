"""
贪吃蛇小游戏 — 内置在记账 APP 中。
纯 Tkinter Canvas 实现，零额外依赖。
"""
import tkinter as tk
import random


class Direction:
    """蛇的移动方向"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    _OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

    @classmethod
    def is_opposite(cls, a, b):
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
        super().__init__(parent, **kw)
        self._on_back = on_back
        self._after_id = None
        self._state = self.STATE_IDLE
        self._snake = []
        self._food = None
        self._direction = Direction.RIGHT
        self._next_dir = Direction.RIGHT
        self._score = 0
        self._speed = 120
        self._keys_bound = False

        self._build_ui()

    # ================================================================
    # 界面构建
    # ================================================================

    def _build_ui(self):
        # 顶栏
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
        if self._state != self.STATE_PLAYING:
            return
        if not Direction.is_opposite(new_dir, self._direction):
            self._next_dir = new_dir

    def _on_space(self):
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
        self._score = 0
        self._score_label.config(text="🏆 分数: 0")
        self._direction = Direction.RIGHT
        self._next_dir = Direction.RIGHT
        self._speed = 120

        sx = self.COLS // 2
        sy = self.ROWS // 2
        self._snake = [(sx, sy), (sx - 1, sy), (sx - 2, sy)]

        self._spawn_food()
        self._draw_snake()

    def _spawn_food(self):
        while True:
            fx = random.randint(0, self.COLS - 1)
            fy = random.randint(0, self.ROWS - 1)
            if (fx, fy) not in self._snake:
                self._food = (fx, fy)
                break

    def _draw_snake(self):
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
        if self._state != self.STATE_PLAYING:
            return

        self._direction = self._next_dir

        hx, hy = self._snake[0]
        dx, dy = self._direction
        new_head = (hx + dx, hy + dy)

        nx, ny = new_head
        if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
            self._game_over()
            return
        if new_head in self._snake:
            self._game_over()
            return

        self._snake.insert(0, new_head)

        if new_head == self._food:
            self._score += 10
            self._score_label.config(text=f"🏆 分数: {self._score}")
            self._spawn_food()
            if self._speed > 50:
                self._speed -= 2
        else:
            self._snake.pop()

        self._draw_snake()
        self._after_id = self.after(self._speed, self._tick)

    def _game_over(self):
        self._state = self.STATE_IDLE
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        # 更新最高分
        best = getattr(SnakeGame, '_best_score', 0)
        if self._score > best:
            SnakeGame._best_score = self._score
        self._best_label.config(text=f"👑 最高: {SnakeGame._best_score}")

        # 遮罩 + 提示（按键保持绑定，空格可以重新开始）
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
        if self._state != self.STATE_PLAYING and self._state != self.STATE_PAUSED:
            return

        if self._state == self.STATE_PLAYING:
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
            self._start_btn.config(state=tk.DISABLED)
            self._pause_btn.config(text="⏸ 暂停")
            self._canvas.delete('pause_overlay')
            self._state = self.STATE_PLAYING
            self._tick()

    def restart(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._state = self.STATE_IDLE
        # 只清除蛇、食物、遮罩，不动网格
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
